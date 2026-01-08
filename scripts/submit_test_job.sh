#!/bin/bash

# AIDP Agent Compute Router - Test Job Submission Script
# Usage: bash scripts/submit_test_job.sh

set -e

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

echo "AIDP Agent Compute Router - Test Job"
echo "=========================================="
echo "API: $API_BASE_URL"
echo ""

# Test 1: Submit Job
echo "Submitting job..."
JOB_RESPONSE=$(curl -s -X POST "$API_BASE_URL/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "TEXT_TO_IMAGE",
    "prompt": "A futuristic city skyline at sunset, cyberpunk style, neon lights",
    "steps": 30
  }')

echo "Response: $JOB_RESPONSE"

# Extract job_id (simple regex for demo)
JOB_ID=$(echo "$JOB_RESPONSE" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$JOB_ID" ]; then
  echo "Failed to create job"
  exit 1
fi

echo "Job created: $JOB_ID"
echo ""

# Test 2: Poll Job Status
echo "Polling job status..."
for i in {1..30}; do
  STATUS_RESPONSE=$(curl -s -X GET "$API_BASE_URL/jobs/$JOB_ID")
  STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
  
  echo "[$i/30] Status: $STATUS"
  
  if [ "$STATUS" = "COMPLETED" ]; then
    echo "Job completed!"
    OUTPUT_URL=$(echo "$STATUS_RESPONSE" | grep -o '"output_url":"[^"]*"' | cut -d'"' -f4)
    COST=$(echo "$STATUS_RESPONSE" | grep -o '"compute_cost":[0-9.]*' | cut -d':' -f2)
    
    echo ""
    echo "Results:"
    echo "  - Output: $OUTPUT_URL"
    echo "  - Cost: \$$COST (AIDP)"
    echo ""
    echo "Demo complete!"
    exit 0
  elif [ "$STATUS" = "FAILED" ]; then
    echo "Job failed"
    exit 1
  fi
  
  sleep 2
done

echo "Timeout: Job still running (you can check status manually)"
echo "Run: curl http://localhost:8000/jobs/$JOB_ID"
