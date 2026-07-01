"""
Seed script — ensures a default admin account exists.

Usage:
    cd backend
    python -m scripts.seed_admin
"""

import asyncio
import sys
from pathlib import Path

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine, AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.core.security import hash_password


DEFAULT_ADMIN = {
    "email": "admin@recruitgen.ai",
    "password": "Admin@123456",
    "full_name": "System Administrator",
    "org_name": "RecruitGen",
}


async def seed_admin() -> None:
    async with AsyncSessionLocal() as session:
        # Check for existing admin
        result = await session.execute(
            select(User).where(User.role == UserRole.ADMIN).limit(1)
        )
        existing = result.scalar_one_or_none()
        if existing:
            print(f"✓ Admin account already exists: {existing.email}")
            return

        # Ensure organization exists
        org_result = await session.execute(
            select(Organization).where(Organization.name == DEFAULT_ADMIN["org_name"]).limit(1)
        )
        org = org_result.scalar_one_or_none()
        if not org:
            org = Organization(name=DEFAULT_ADMIN["org_name"])
            session.add(org)
            await session.flush()
            print(f"  Created organization: {DEFAULT_ADMIN['org_name']}")

        # Create admin user
        admin = User(
            email=DEFAULT_ADMIN["email"],
            hashed_password=hash_password(DEFAULT_ADMIN["password"]),
            full_name=DEFAULT_ADMIN["full_name"],
            role=UserRole.ADMIN,
            organization_id=org.id,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print(f"✓ Admin account created: {DEFAULT_ADMIN['email']}")
        print(f"  Password: {DEFAULT_ADMIN['password']}")
        print(f"  ⚠ Change this password after first login!")


if __name__ == "__main__":
    asyncio.run(seed_admin())
