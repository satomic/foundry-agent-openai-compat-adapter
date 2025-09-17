# Foundry Agent OpenAI Compatibility Adapter

[English](README.md) | 中文


---

## 概述

这个适配器为 Azure AI Foundry Agents 提供了 OpenAI 兼容的 API 层，让您可以无缝地使用现有的 OpenAI 客户端库和工具与 Azure AI Foundry Agents 进行交互。它充当 OpenAI API 格式和 Azure AI Foundry Agent APIs 之间的桥梁。而且，这是一种相对于[使用mcp集成](https://github.com/satomic/ai-foundry-agent-mcp)更加优雅的使用AI Foundry Agent的方式。

**支持的 Azure AI Foundry Agent 核心能力：**
- 📚 **知识库 (Knowledge)**: 访问自定义知识库和文档
- ⚡ **操作 (Actions)**: 执行自定义函数和集成
- 🔗 **互联代理 (Connected Agents)**: 多代理编排和协作

## 功能特性

- 🔄 **OpenAI 兼容 API**: 完全兼容 OpenAI 的 `/v1/chat/completions` 端点
- 🌊 **流式响应支持**: 使用服务器发送事件 (SSE) 的实时流式响应
- 📋 **模型列表**: `/v1/models` 端点用于列出可用模型
- 🔍 **全面日志记录**: 详细的日志记录，支持可配置级别和文件轮转
- 📊 **请求审计**: 自动审计所有请求和响应
- 🛡️ **错误处理**: 强大的错误处理机制和故障回退响应
- 📖 **自动文档**: FastAPI 驱动的交互式 API 文档
- 🔧 **健康监控**: 服务监控的健康检查端点
- 🌐 **CORS 支持**: 启用跨域资源共享
- ⚙️ **环境配置**: 通过环境变量进行灵活配置


## 项目结构

```
foundry-agent-openai-compat-adapter/
├── main.py               # 主应用程序文件
├── README.md             # 本文件
├── .env.example          # 环境变量模板
├── logs/                 # 自动生成的日志文件
├── audits/               # 自动生成的审计文件
└── tests/                # 测试脚本
    ├── test_client.py    # Python 测试客户端
    ├── test_streaming.py # 流式测试
    ├── test_curl.bat     # Windows curl 测试
    └── test_curl.sh      # Linux/macOS curl 测试
```

## 系统要求

- Python 3.7+
- Azure AI Foundry Agent（具有有效凭据）
- Azure 订阅应用程序凭据（tenant_id、client_id、client_secret）

## 安装步骤

1. **克隆仓库:**
    ```bash
    git clone https://github.com/satomic/foundry-agent-openai-compat-adapter.git
    cd foundry-agent-openai-compat-adapter
    ```

2. **安装依赖:**
    ```bash
    pip install -r requirements.txt
    ```

3. **配置环境变量:**
    ```bash
    cp .env.example .env
    ```

    编辑 `.env` 文件，填入您的 Azure 订阅应用程序凭据和设置：
    ```bash
    # Azure 身份验证信息（来自 Azure 订阅应用程序）
    AZURE_TENANT_ID=your_tenant_id_here
    AZURE_CLIENT_ID=your_client_id_here
    AZURE_CLIENT_SECRET=your_client_secret_here

    # Azure AI 项目信息
    AZURE_ENDPOINT=your_azure_ai_endpoint_here
    AZURE_AGENT_ID=your_agent_id_here

    # 服务器配置（可选）
    SERVER_HOST=0.0.0.0
    SERVER_PORT=8000
    LOG_LEVEL=info
    ```

## 使用方法

### 启动服务器

```bash
python main.py
```

服务器将在 `http://localhost:8000`（或配置的主机/端口）上启动。

### API 文档

访问 `http://localhost:8000/docs` 查看交互式 Swagger/OpenAPI 文档。

### 测试适配器

**Python 测试脚本:**
```bash
python tests/test_client.py
```

**流式测试:**
```bash
python tests/test_streaming.py
```

**curl 测试:**
```bash
# Windows
tests/test_curl.bat

# Linux/macOS
bash tests/test_curl.sh
```

## API 使用示例

### 使用 OpenAI 库的 Python 示例

```python
import openai

# 配置客户端使用本地适配器
client = openai.OpenAI(
    api_key="not-needed",  # 任何字符串都可以
    base_url="http://localhost:8000/v1"
)

# 非流式聊天补全
response = client.chat.completions.create(
    model="foundry-agent-model",
    messages=[
        {"role": "user", "content": "你好！你能帮我学习 Python 吗？"}
    ],
    temperature=0.7,
    max_tokens=150
)

print(response.choices[0].message.content)

# 流式聊天补全
stream = client.chat.completions.create(
    model="foundry-agent-model",
    messages=[
        {"role": "user", "content": "给我讲一个简短的故事"}
    ],
    temperature=0.7,
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

### curl 示例

```bash
# 非流式请求
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "foundry-agent-model",
    "messages": [{"role": "user", "content": "你好！"}],
    "temperature": 0.7,
    "max_tokens": 150
  }'

# 流式请求
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "model": "foundry-agent-model",
    "messages": [{"role": "user", "content": "给我讲个故事"}],
    "temperature": 0.7,
    "stream": true
  }'
```

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/v1/chat/completions` | POST | OpenAI 兼容的聊天补全（支持流式） |
| `/v1/models` | GET | 列出可用模型 |
| `/health` | GET | 健康检查端点 |
| `/docs` | GET | 交互式 API 文档 |

## 支持的 OpenAI 参数

- ✅ `model`: 模型标识符（使用 "foundry-agent-model"）
- ✅ `messages`: 对话消息数组
- ✅ `temperature`: 采样温度（0.0 到 2.0）
- ✅ `max_tokens`: 补全中的最大令牌数
- ✅ `stream`: 启用流式响应
- ❌ `functions`, `tools`: 当前不支持

## 日志记录和监控

### 日志文件

日志自动保存到 `logs/` 目录，按日轮转：
- 格式：`YYYY-MM-DD.log`

### 日志级别

通过 `LOG_LEVEL` 环境变量设置：
- `DEBUG`: 详细调试信息
- `INFO`: 一般信息（默认）
- `WARNING`: 警告消息
- `ERROR`: 错误消息
- `CRITICAL`: 严重错误

### 审计追踪

所有请求和响应自动保存到 `audits/` 目录：
- 文件格式：`audit_YYYYMMDD_HHMMSS_mmm_XXXXXXXX.json`
- 包含完整的请求/响应数据
- 服务器环境的元数据
- 流式和非流式请求的独立审计追踪



## 故障排除

### 常见问题

1. **服务器无法启动**: 检查 `.env` 文件中的环境变量
2. **身份验证错误**: 验证 Azure 凭据和权限
3. **代理无响应**: 检查 `AZURE_AGENT_ID` 和 Azure 中的代理状态
4. **超时错误**: 检查到 Azure 端点的网络连接


## 许可证

此项目采用 MIT 许可证。详情请参阅 LICENSE 文件。