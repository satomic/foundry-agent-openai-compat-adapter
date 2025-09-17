#!/bin/bash

echo "=== Testing Foundry Agent OpenAI Adapter ==="
echo "Server: http://localhost:8000"
echo

# Test 1: Health check
echo "1. Health Check:"
curl -s http://localhost:8000/health | jq '.' 2>/dev/null || curl -s http://localhost:8000/health
echo
echo

# Test 2: Models endpoint
echo "2. Models endpoint:"
curl -s http://localhost:8000/v1/models | jq '.' 2>/dev/null || curl -s http://localhost:8000/v1/models
echo
echo

# Test 3: Chat completions
echo "3. Chat completions:"
echo "Request payload:"
cat << 'EOF'
{
  "model": "foundry-agent-model",
  "messages": [
    {"role": "user", "content": "Hello, what is 2+2?"}
  ],
  "temperature": 0.7
}
EOF
echo
echo "Response:"

curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "foundry-agent-model",
    "messages": [
      {"role": "user", "content": "Hello, what is 2+2?"}
    ],
    "temperature": 0.7
  }' \
  -w "\n\nHTTP Status: %{http_code}\nResponse Time: %{time_total}s\nContent-Type: %{content_type}\n" \
  -s | jq '.' 2>/dev/null || \
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "foundry-agent-model",
    "messages": [
      {"role": "user", "content": "Hello, what is 2+2?"}
    ],
    "temperature": 0.7
  }' \
  -w "\n\nHTTP Status: %{http_code}\nResponse Time: %{time_total}s\nContent-Type: %{content_type}\n" \
  -s

echo
echo "=== Test Complete ==="