# AIDP Agent Compute Router - Test Job Submission Script (Windows)
# Usage: powershell -ExecutionPolicy Bypass -File scripts/submit_test_job.ps1

$API_BASE_URL = $env:API_BASE_URL -replace '^$', 'http://localhost:8000'

Write-Host "AIDP Agent Compute Router - Test Job" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "API: $API_BASE_URL" -ForegroundColor Yellow
Write-Host ""

# Test 1: Submit Job
Write-Host "Submitting job..." -ForegroundColor Yellow

$jobPayload = @{
    type = "TEXT_TO_IMAGE"
    prompt = "A futuristic city skyline at sunset, cyberpunk style, neon lights"
    steps = 30
} | ConvertTo-Json

try {
    $jobResponse = Invoke-WebRequest -Uri "$API_BASE_URL/jobs" `
        -Method POST `
        -ContentType "application/json" `
        -Body $jobPayload `
        -UseBasicParsing

    $jobData = $jobResponse.Content | ConvertFrom-Json
    $JOB_ID = $jobData.job_id

    if (-not $JOB_ID) {
        Write-Host "Failed to create job" -ForegroundColor Red
        exit 1
    }

    Write-Host "Response: $($jobResponse.Content)"
    Write-Host "Job created: $JOB_ID" -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host "Failed to submit job: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Poll Job Status
Write-Host "Polling job status..." -ForegroundColor Yellow
$maxAttempts = 30

for ($i = 1; $i -le $maxAttempts; $i++) {
    try {
        $statusResponse = Invoke-WebRequest -Uri "$API_BASE_URL/jobs/$JOB_ID" `
            -Method GET `
            -UseBasicParsing

        $statusData = $statusResponse.Content | ConvertFrom-Json
        $STATUS = $statusData.status

        Write-Host "[$i/$maxAttempts] Status: $STATUS" -ForegroundColor Cyan

        if ($STATUS -eq "COMPLETED") {
            Write-Host "Job completed!" -ForegroundColor Green
            
            $outputUrl = $statusData.output_url
            $cost = $statusData.compute_cost

            Write-Host ""
            Write-Host "Results:" -ForegroundColor Green
            Write-Host "  - Output: $outputUrl" -ForegroundColor White
            Write-Host "  - Cost: `$$cost (AIDP)" -ForegroundColor White
            Write-Host ""
            Write-Host "Demo complete!" -ForegroundColor Green
            exit 0
        }
        elseif ($STATUS -eq "FAILED") {
            Write-Host "Job failed" -ForegroundColor Red
            exit 1
        }

        Start-Sleep -Seconds 2
    }
    catch {
        Write-Host "Error checking status: $_" -ForegroundColor Red
    }
}

Write-Host "Timeout: Job still running (you can check status manually)" -ForegroundColor Yellow
Write-Host "Run: curl http://localhost:8000/jobs/$JOB_ID" -ForegroundColor Yellow
