# Foundry Agent OpenAI Compatibility Adapter

English | [中文](README_CN.md)

## Overview

This adapter provides an OpenAI-compatible API layer for Azure AI Foundry Agents, allowing you to use existing OpenAI client libraries and tools with Azure AI Foundry Agents seamlessly. It acts as a bridge between the OpenAI API format and Azure AI Foundry Agent APIs. Moreover, this is a more elegant way to use AI Foundry Agent than [using mcp integration](https://github.com/satomic/ai-foundry-agent-mcp).

**Azure AI Foundry Agent Core Capabilities Supported:**
- 📚 **Knowledge**: Access to custom knowledge bases and documents
- ⚡ **Actions**: Execute custom functions and integrations
- 🔗 **Connected Agents**: Multi-agent orchestration and collaboration

## Features

- 🔄 **OpenAI-compatible API**: Full compatibility with OpenAI's `/v1/chat/completions` endpoint
- 🌊 **Streaming Support**: Real-time streaming responses with Server-Sent Events (SSE)
- 📋 **Model Listing**: `/v1/models` endpoint for listing available models
- 🔍 **Comprehensive Logging**: Detailed logging with configurable levels and file rotation
- 📊 **Request Auditing**: Automatic audit trail for all requests and responses
- 🛡️ **Error Handling**: Robust error handling with fallback responses
- 📖 **Auto Documentation**: FastAPI-powered interactive API documentation
- 🔧 **Health Monitoring**: Health check endpoint for service monitoring
- 🌐 **CORS Support**: Cross-origin resource sharing enabled
- ⚙️ **Environment Configuration**: Flexible configuration via environment variables

## Project Structure

```
foundry-agent-openai-compat-adapter/
├── main.py               # Main application file
├── README.md             # This file
├── .env.example          # Environment variables template
├── logs/                 # Auto-generated log files
├── audits/               # Auto-generated audit files
└── tests/                # Test scripts
    ├── test_client.py    # Python test client
    ├── test_streaming.py # Streaming test
    ├── test_curl.bat     # Windows curl tests
    └── test_curl.sh      # Linux/macOS curl tests
```

## Prerequisites

- Python 3.7+
- Azure AI Foundry Agent (with valid credentials)
- Azure Subscription Application credentials (tenant_id, client_id, client_secret)

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/satomic/foundry-agent-openai-compat-adapter.git
    cd foundry-agent-openai-compat-adapter
    ```

2. **Install required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure environment variables:**
    ```bash
    cp .env.example .env
    ```

    Edit the `.env` file with your Azure Subscription Application credentials and settings:
    ```bash
    # Azure Authentication Information (from Azure Subscription Application)
    AZURE_TENANT_ID=your_tenant_id_here
    AZURE_CLIENT_ID=your_client_id_here
    AZURE_CLIENT_SECRET=your_client_secret_here

    # Azure AI Project Information
    AZURE_ENDPOINT=your_azure_ai_endpoint_here
    AZURE_AGENT_ID=your_agent_id_here

    # Server Configuration (Optional)
    SERVER_HOST=0.0.0.0
    SERVER_PORT=8000
    LOG_LEVEL=info
    ```

## Usage

### Starting the Server

```bash
python main.py
```

The server will start on `http://localhost:8000` (or the configured host/port).

### API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger/OpenAPI documentation.

### Testing the Adapter

**Python test script:**
```bash
python tests/test_client.py
```

**Streaming test:**
```bash
python tests/test_streaming.py
```

**curl tests:**
```bash
# Windows
tests/test_curl.bat

# Linux/macOS
bash tests/test_curl.sh
```

## API Usage Examples

### Python with OpenAI Library

```python
import openai

# Configure the client to use the local adapter
client = openai.OpenAI(
    api_key="not-needed",  # Any string works
    base_url="http://localhost:8000/v1"
)

# Non-streaming chat completion
response = client.chat.completions.create(
    model="foundry-agent-model",
    messages=[
        {"role": "user", "content": "Hello! Can you help me with Python?"}
    ],
    temperature=0.7,
    max_tokens=150
)

print(response.choices[0].message.content)

# Streaming chat completion
stream = client.chat.completions.create(
    model="foundry-agent-model",
    messages=[
        {"role": "user", "content": "Tell me a short story"}
    ],
    temperature=0.7,
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```


### curl

```bash
# Non-streaming request
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "foundry-agent-model",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7,
    "max_tokens": 150
  }'

# Streaming request
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "model": "foundry-agent-model",
    "messages": [{"role": "user", "content": "Tell me a story"}],
    "temperature": 0.7,
    "stream": true
  }'
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | OpenAI-compatible chat completions (supports streaming) |
| `/v1/models` | GET | List available models |
| `/health` | GET | Health check endpoint |
| `/docs` | GET | Interactive API documentation |

## Supported OpenAI Parameters

### Chat Completions

- ✅ `model`: Model identifier (use "foundry-agent-model")
- ✅ `messages`: Array of conversation messages
- ✅ `temperature`: Sampling temperature (0.0 to 2.0)
- ✅ `max_tokens`: Maximum tokens in completion
- ✅ `stream`: Enable streaming responses
- ❌ `functions`, `tools`: Not currently supported


## Logging and Monitoring

### Log Files

Logs are automatically saved to the `logs/` directory with daily rotation:
- Format: `YYYY-MM-DD.log`


### Log Levels

Set via `LOG_LEVEL` environment variable:
- `DEBUG`: Detailed debugging information
- `INFO`: General information (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

### Audit Trail

All requests and responses are automatically saved to the `audits/` directory:
- File format: `audit_YYYYMMDD_HHMMSS_mmm_XXXXXXXX.json`
- Includes complete request/response data
- Metadata about server environment
- Separate audit trails for streaming vs non-streaming requests




## Troubleshooting

### Common Issues

1. **Server won't start**: Check environment variables in `.env` file
2. **Authentication errors**: Verify Azure credentials and permissions
3. **Agent not responding**: Check `AZURE_AGENT_ID` and agent status in Azure
4. **Timeout errors**: Check network connectivity to Azure endpoints


## License

This project is licensed under the MIT License. See LICENSE file for details.
