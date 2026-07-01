"""
Database Cleanup / Reset Script for RecruitGen AI.

Runnable from the ``backend/`` directory:

    python -m scripts.cleanup_db              # default cleanup
    python -m scripts.cleanup_db --dry-run    # preview only
    python -m scripts.cleanup_db --full-reset  # wipe ALL data (with confirmation)

Operations performed during a normal cleanup:
1. Remove duplicate applications  (same candidate_id + job_id, keep oldest)
2. Remove duplicate interviews    (same candidate_id + job_id + scheduled_at)
3. Remove duplicate recommendations (same candidate_id + job_id)
4. Remove duplicate reports       (same report_type + job_id)
5. Purge stale notifications older than 30 days
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, engine
from app.models.application import Application
from app.models.hiring_recommendation import HiringRecommendation
from app.models.interview_schedule import InterviewSchedule
from app.models.notification import Notification
from app.models.report import Report

# ── Constants ───────────────────────────────────────────────
STALE_NOTIFICATION_DAYS = 30


# ── Helpers ─────────────────────────────────────────────────


def _header(title: str) -> None:
    """Print a section header."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


async def _count_rows(session: AsyncSession, model: type) -> int:
    """Return the total row count for a model's table."""
    result = await session.execute(
        select(func.count()).select_from(model),
    )
    return result.scalar_one()


# ── Duplicate removal ──────────────────────────────────────


async def _remove_duplicates(
    session: AsyncSession,
    model: type,
    partition_cols: Sequence[Any],
    *,
    dry_run: bool,
) -> int:
    """Delete duplicate rows, keeping the oldest (earliest created_at).

    Uses a CTE with ``ROW_NUMBER()`` partitioned by *partition_cols*
    and ordered by ``created_at ASC`` so the first occurrence survives.

    Returns the number of rows that were (or would be) deleted.
    """
    label = model.__tablename__

    # Build the ROW_NUMBER window expression
    row_num = (
        func.row_number()
        .over(
            partition_by=partition_cols,
            order_by=model.created_at.asc(),
        )
        .label("rn")
    )

    # Sub-query: tag every row with its rank within the duplicate group
    subq = (
        select(model.id, row_num)
        .subquery("ranked")
    )

    # Find ids where rn > 1 (the duplicates to remove)
    dup_ids_q = select(subq.c.id).where(subq.c.rn > 1)
    result = await session.execute(dup_ids_q)
    dup_ids: list[Any] = [row[0] for row in result.all()]

    count = len(dup_ids)

    if count == 0:
        print(f"  ✓ {label}: no duplicates found")
        return 0

    if dry_run:
        print(f"  ⚠ {label}: {count} duplicate(s) would be removed")
    else:
        await session.execute(
            delete(model).where(model.id.in_(dup_ids)),
        )
        print(f"  ✗ {label}: {count} duplicate(s) removed")

    return count


# ── Stale notification purge ───────────────────────────────


async def _purge_stale_notifications(
    session: AsyncSession,
    *,
    dry_run: bool,
) -> int:
    """Delete notifications older than STALE_NOTIFICATION_DAYS days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=STALE_NOTIFICATION_DAYS)

    # Count first
    count_result = await session.execute(
        select(func.count())
        .select_from(Notification)
        .where(Notification.created_at < cutoff),
    )
    count: int = count_result.scalar_one()

    if count == 0:
        print(f"  ✓ notifications: none older than {STALE_NOTIFICATION_DAYS} days")
        return 0

    if dry_run:
        print(
            f"  ⚠ notifications: {count} stale row(s) (>{STALE_NOTIFICATION_DAYS}d) "
            f"would be removed",
        )
    else:
        await session.execute(
            delete(Notification).where(Notification.created_at < cutoff),
        )
        print(
            f"  ✗ notifications: {count} stale row(s) (>{STALE_NOTIFICATION_DAYS}d) "
            f"removed",
        )

    return count


# ── Full reset ─────────────────────────────────────────────

# Ordered so child tables are truncated before parents (FK safety).
_ALL_TABLES: list[str] = [
    "notifications",
    "reports",
    "hiring_recommendations",
    "skill_evaluations",
    "interview_schedules",
    "candidate_rankings",
    "candidate_matches",
    "job_analyses",
    "applications",
    "resumes",
    "candidate_skills",
    "candidate_projects",
    "candidate_certifications",
    "candidate_educations",
    "candidate_experiences",
    "candidate_profiles",
    "job_requirements",
    "jobs",
    "users",
    "organizations",
]


async def _full_reset(session: AsyncSession, *, dry_run: bool) -> dict[str, int]:
    """TRUNCATE every known table (CASCADE).  Returns table→row-count map."""
    counts: dict[str, int] = {}

    for table in _ALL_TABLES:
        # Check if the table exists before truncating
        exists_q = await session.execute(
            text(
                "SELECT EXISTS ("
                "  SELECT 1 FROM information_schema.tables "
                "  WHERE table_schema = 'public' AND table_name = :t"
                ")"
            ),
            {"t": table},
        )
        if not exists_q.scalar():
            continue

        count_result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))  # noqa: S608
        row_count: int = count_result.scalar_one()
        counts[table] = row_count

        if dry_run:
            print(f"  ⚠ {table}: {row_count} row(s) would be deleted")
        else:
            await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))  # noqa: S608
            print(f"  ✗ {table}: {row_count} row(s) deleted")

    return counts


# ── Main ───────────────────────────────────────────────────


async def main(*, dry_run: bool = False, full_reset: bool = False) -> None:
    """Entry-point for the cleanup script."""

    mode = "DRY-RUN" if dry_run else "LIVE"
    print(f"\n🗄  RecruitGen AI — Database Cleanup  [{mode}]")

    if full_reset:
        _header("FULL RESET — all data will be permanently deleted")
        if not dry_run:
            answer = input("  Type 'YES' to confirm full reset: ")
            if answer.strip() != "YES":
                print("  Aborted.")
                return

    async with AsyncSessionLocal() as session:
        total_affected = 0

        if full_reset:
            counts = await _full_reset(session, dry_run=dry_run)
            total_affected = sum(counts.values())
        else:
            # 1. Duplicate applications (candidate_id + job_id)
            _header("Deduplicating applications")
            total_affected += await _remove_duplicates(
                session,
                Application,
                [Application.candidate_id, Application.job_id],
                dry_run=dry_run,
            )

            # 2. Duplicate interviews (candidate_id + job_id + scheduled_at)
            _header("Deduplicating interview schedules")
            total_affected += await _remove_duplicates(
                session,
                InterviewSchedule,
                [
                    InterviewSchedule.candidate_id,
                    InterviewSchedule.job_id,
                    InterviewSchedule.scheduled_at,
                ],
                dry_run=dry_run,
            )

            # 3. Duplicate recommendations (candidate_id + job_id)
            _header("Deduplicating hiring recommendations")
            total_affected += await _remove_duplicates(
                session,
                HiringRecommendation,
                [HiringRecommendation.candidate_id, HiringRecommendation.job_id],
                dry_run=dry_run,
            )

            # 4. Duplicate reports (report_type + job_id)
            _header("Deduplicating reports")
            total_affected += await _remove_duplicates(
                session,
                Report,
                [Report.report_type, Report.job_id],
                dry_run=dry_run,
            )

            # 5. Stale notifications
            _header("Purging stale notifications")
            total_affected += await _purge_stale_notifications(
                session,
                dry_run=dry_run,
            )

        # ── Summary ─────────────────────────────────────────
        _header("Summary")
        if dry_run:
            print(f"  {total_affected} row(s) would be affected (dry-run, no changes made)")
        else:
            if total_affected > 0:
                await session.commit()
            print(f"  {total_affected} row(s) affected and committed")

    # Dispose engine to ensure clean shutdown
    await engine.dispose()
    print("\n✅ Done.\n")


# ── CLI ─────────────────────────────────────────────────────


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RecruitGen AI — Database cleanup & reset utility",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without deleting anything",
    )
    parser.add_argument(
        "--full-reset",
        action="store_true",
        help="Clear ALL data from all tables (for fresh demo setup)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    try:
        asyncio.run(main(dry_run=args.dry_run, full_reset=args.full_reset))
    except KeyboardInterrupt:
        print("\nInterrupted — no changes committed.")
        sys.exit(1)
