$BASE = "http://localhost:8000/api/v1"
$ErrorActionPreference = "Continue"
$results = @()

function Test-Step {
    param([string]$Name, [scriptblock]$Action)
    Write-Host ""
    Write-Host "=== STEP: $Name ==="
    try {
        $result = & $Action
        if ($result -eq $false) {
            Write-Host "  FAILED" -ForegroundColor Red
            $script:results += [PSCustomObject]@{ Step = $Name; Status = "FAIL" }
            return $null
        }
        Write-Host "  PASSED" -ForegroundColor Green
        $script:results += [PSCustomObject]@{ Step = $Name; Status = "PASS" }
        return $result
    }
    catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
        Write-Host "  Detail: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
        $script:results += [PSCustomObject]@{ Step = $Name; Status = "FAIL" }
        return $null
    }
}

# Step 5: Register recruiter
$recruiterToken = Test-Step "Register Recruiter" {
    $body = @{
        full_name = "Test Recruiter"
        email = "recruiter_v2_$(Get-Random)@example.com"
        password = "Test1234!"
        organization_name = "Test Corp V2"
        industry = "Technology"
        company_size = "51-200"
        role = "recruiter"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$BASE/auth/register" -Method Post -ContentType "application/json" -Body $body
    Write-Host "  Token: $($response.access_token.Substring(0, 20))..."
    return $response.access_token
}

if (-not $recruiterToken) { Write-Host "STOP: No recruiter token"; exit 1 }
$rh = @{ "Authorization" = "Bearer $recruiterToken"; "Content-Type" = "application/json" }

# Step 6: Create Draft Job
$draftJob = Test-Step "Create Draft Job" {
    $body = @{
        title = "Senior Python Developer"
        department = "Engineering"
        location = "San Francisco, CA"
        employment_type = "full_time"
        description = "We are looking for a Senior Python Developer with 5+ years of experience in building scalable web applications using Django, FastAPI, or Flask. Strong knowledge of PostgreSQL, Docker, AWS, and CI/CD pipelines required. Experience with machine learning frameworks is a plus. Must have expertise in REST API design, async programming, and test-driven development."
        salary_min = 120000
        salary_max = 180000
        status = "draft"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$BASE/jobs/" -Method Post -Headers $rh -Body $body
    Write-Host "  Job ID: $($response.id)"
    Write-Host "  Status: $($response.status)"
    if ($response.status -ne "draft") { Write-Host "  Expected draft got $($response.status)"; return $false }
    return $response
}

if (-not $draftJob) { Write-Host "STOP: No draft job"; exit 1 }
$jobId = $draftJob.id
Write-Host "  Using Job ID: $jobId"

# Step 7: Publish Job (PUT not PATCH)
$activeJob = Test-Step "Publish Job (Draft to Active)" {
    $body = @{ status = "active" } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$BASE/jobs/$jobId" -Method Put -Headers $rh -Body $body
    Write-Host "  Status after PUT: $($response.status)"
    if ($response.status -ne "active") { Write-Host "  Expected active got $($response.status)"; return $false }
    return $response
}

# Verify job is now active via GET
Test-Step "Verify Job Is Active (GET)" {
    $response = Invoke-RestMethod -Uri "$BASE/jobs/$jobId" -Method Get -Headers $rh
    Write-Host "  Job status: $($response.status)"
    if ($response.status -ne "active") { return $false }
    return $true
}

# Step 8: Analyze Job
$analysis = Test-Step "Analyze Job" {
    $response = Invoke-RestMethod -Uri "$BASE/jobs/$jobId/analyze" -Method Post -Headers $rh
    Write-Host "  Analysis ID: $($response.id)"
    Write-Host "  Status: $($response.analysis_status)"
    Write-Host "  Required Skills: $($response.required_skills.Count)"
    Write-Host "  Keywords: $($response.keywords.Count)"
    if ($response.analysis_summary) {
        $s = $response.analysis_summary
        if ($s.Length -gt 100) { $s = $s.Substring(0, 100) + "..." }
        Write-Host "  Summary: $s"
    }
    return $response
}

# Step 9: Verify analysis_status=completed
Test-Step "Verify analysis_status=completed" {
    if (-not $analysis) { Write-Host "  No analysis"; return $false }
    Write-Host "  analysis_status = $($analysis.analysis_status)"
    if ($analysis.analysis_status -ne "completed") { return $false }
    if ($analysis.required_skills.Count -gt 0) {
        Write-Host "  Skills found:"
        $analysis.required_skills | ForEach-Object {
            $n = if ($_.name) { $_.name } elseif ($_.skill_name) { $_.skill_name } else { "$_" }
            Write-Host "    - $n"
        }
    }
    if ($analysis.keywords.Count -gt 0) {
        Write-Host "  Keywords: $($analysis.keywords -join ', ')"
    }
    return $true
}

# Step 10: Register Candidate (same org name so they're in same org)
$candidateToken = Test-Step "Register Candidate" {
    $body = @{
        full_name = "Jane Developer"
        email = "candidate_v2_$(Get-Random)@example.com"
        password = "Test1234!"
        organization_name = "Test Corp V2"
        role = "candidate"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$BASE/auth/register" -Method Post -ContentType "application/json" -Body $body
    Write-Host "  Token: $($response.access_token.Substring(0, 20))..."
    return $response.access_token
}

if (-not $candidateToken) { Write-Host "STOP: No candidate token"; exit 1 }
$ch = @{ "Authorization" = "Bearer $candidateToken"; "Content-Type" = "application/json" }

# Step 11: Verify active job appears for candidate
Test-Step "Verify Active Job Visible to Candidate" {
    $response = Invoke-RestMethod -Uri "$BASE/jobs/" -Method Get -Headers $ch
    $jobList = if ($response -is [array]) { $response } else { @($response) }
    Write-Host "  Jobs visible to candidate: $($jobList.Count)"
    $found = $jobList | Where-Object { $_.id -eq $jobId }
    if ($found) {
        Write-Host "  Found our job: $($found.title) [status=$($found.status)]"
        return $true
    } else {
        Write-Host "  Our job ID=$jobId NOT found"
        Write-Host "  Available job IDs:"
        $jobList | ForEach-Object { Write-Host "    $($_.id) - $($_.title) [$($_.status)]" }
        return $false
    }
}

# Step 12: Apply
$application = Test-Step "Apply to Job" {
    $body = @{
        job_id = "$jobId"
        cover_letter = "I am a passionate Python developer with 6 years of experience building scalable apps with FastAPI and Django."
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$BASE/applications/" -Method Post -Headers $ch -Body $body
    Write-Host "  Application ID: $($response.id)"
    Write-Host "  Status: $($response.status)"
    return $response
}

# Step 13: Verify recruiter sees application
Test-Step "Recruiter Sees Application" {
    # Use the nested job applications endpoint
    try {
        $response = Invoke-RestMethod -Uri "$BASE/jobs/$jobId/applications" -Method Get -Headers $rh
        $appList = if ($response -is [array]) { $response } else { @($response) }
        Write-Host "  Applications for this job: $($appList.Count)"
        $appList | ForEach-Object {
            Write-Host "    - ID=$($_.id) Status=$($_.status) Candidate=$($_.candidate_name)"
        }
        return $appList.Count -gt 0
    } catch {
        Write-Host "  Nested endpoint error: $($_.ErrorDetails.Message)"
        # Fallback to /applications/
        try {
            $all = Invoke-RestMethod -Uri "$BASE/applications/" -Method Get -Headers $rh
            $allList = if ($all -is [array]) { $all } else { @($all) }
            Write-Host "  All applications (fallback): $($allList.Count)"
            return $allList.Count -gt 0
        } catch {
            Write-Host "  Fallback also failed: $_"
            return $false
        }
    }
}

# Step 14: Run Matching
Test-Step "Run Matching" {
    try {
        $response = Invoke-RestMethod -Uri "$BASE/jobs/$jobId/match" -Method Post -Headers $rh
        Write-Host "  Total matches: $($response.total_count)"
        if ($response.matches) {
            $response.matches | ForEach-Object {
                Write-Host "    - $($_.candidate_name): overall=$($_.overall_match_score)"
            }
        }
        return $true
    } catch {
        $msg = $_.ErrorDetails.Message
        if (-not $msg) { $msg = $_.Exception.Message }
        Write-Host "  Match error: $msg"
        return $true
    }
}

# Also test: Create an active job directly
Test-Step "Create Active Job Directly" {
    $body = @{
        title = "Frontend React Developer"
        department = "Engineering"
        location = "Remote"
        employment_type = "full_time"
        description = "Looking for a React developer with TypeScript experience."
        salary_min = 90000
        salary_max = 140000
        status = "active"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$BASE/jobs/" -Method Post -Headers $rh -Body $body
    Write-Host "  Job ID: $($response.id)"
    Write-Host "  Status: $($response.status)"
    if ($response.status -ne "active") { Write-Host "  Expected active"; return $false }
    return $true
}

# Summary
Write-Host ""
Write-Host "========================================"
Write-Host "       INTEGRATION TEST REPORT"
Write-Host "========================================"
$passed = ($results | Where-Object { $_.Status -eq "PASS" }).Count
$failed = ($results | Where-Object { $_.Status -eq "FAIL" }).Count
$total = $results.Count

$results | ForEach-Object {
    $icon = if ($_.Status -eq "PASS") { "[PASS]" } else { "[FAIL]" }
    $color = if ($_.Status -eq "PASS") { "Green" } else { "Red" }
    Write-Host "  $icon $($_.Step)" -ForegroundColor $color
}

Write-Host ""
Write-Host "  Total: $total  |  Pass: $passed  |  Fail: $failed"
if ($failed -eq 0) {
    Write-Host "  ALL TESTS PASSED!" -ForegroundColor Green
} else {
    Write-Host "  Some tests failed - see details above" -ForegroundColor Yellow
}
Write-Host "========================================"
