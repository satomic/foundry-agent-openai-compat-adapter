@echo off
echo === Testing Foundry Agent OpenAI Adapter ===
echo Server: http://localhost:8000
echo.

echo 1. Health Check:
curl -s http://localhost:8000/health
echo.
echo.

echo 2. Models endpoint:
curl -s http://localhost:8000/v1/models
echo.
echo.

echo 3. Chat completions:
echo Request payload:
echo {
echo   "model": "foundry-agent-model",
echo   "messages": [
echo     {"role": "user", "content": "Hello, what is 2+2?"}
echo   ],
echo   "temperature": 0.7
echo }
echo.
echo Response:

curl -X POST http://localhost:8000/v1/chat/completions ^
  -H "Content-Type: application/json" ^
  -d "{\"model\": \"foundry-agent-model\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello, what is 2+2?\"}], \"temperature\": 0.7}" ^
  -w "%%{http_code}" ^
  -s

echo.
echo.
echo === Test Complete ===