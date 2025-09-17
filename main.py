import os
import sys
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import json
import uuid
from datetime import datetime
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from azure.ai.projects import AIProjectClient
from azure.identity import ClientSecretCredential
from azure.ai.agents.models import ListSortOrder
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging to output to both console and daily log files
def setup_logging():
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Get log level from environment variable
    log_level_str = os.getenv('LOG_LEVEL', 'info').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with daily rotation
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(log_dir, f"{today}.log")
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

# Audit functionality
def save_audit_data(request_data, response_data, request_type="chat_completion"):
    """Save complete request and response data to audit files"""
    try:
        # Create audits directory if it doesn't exist
        audit_dir = "audits"
        os.makedirs(audit_dir, exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # microseconds to milliseconds
        audit_id = f"{timestamp}_{uuid.uuid4().hex[:8]}"
        
        # Prepare audit data with metadata
        audit_data = {
            "audit_id": audit_id,
            "timestamp": datetime.now().isoformat(),
            "request_type": request_type,
            "request": request_data,
            "response": response_data,
            "metadata": {
                "server_version": "1.0.0",
                "audit_format_version": "1.0",
                "environment": {
                    "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                    "platform": os.name,
                    "working_directory": os.getcwd()
                }
            }
        }
        
        # Save to JSON file
        audit_file = os.path.join(audit_dir, f"audit_{audit_id}.json")
        with open(audit_file, 'w', encoding='utf-8') as f:
            json.dump(audit_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Audit data saved to: {audit_file}")
        return audit_id
        
    except Exception as e:
        logger.error(f"Failed to save audit data: {e}")
        return None

app = FastAPI(title="Foundry Agent OpenAI Compatibility Layer", version="1.0.0")

# Add logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log request basics
    logger.info(f"{request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Log response status
    logger.info(f"Response: {response.status_code}")
    
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str

class Delta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None

class StreamChoice(BaseModel):
    index: int
    delta: Delta
    finish_reason: Optional[str] = None

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Usage

class ChatCompletionStreamResponse(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[StreamChoice]

class FoundryAgentAdapter:
    def __init__(self):
        """Initialize the Azure Agent Manager with credentials from environment variables."""
        # Get Azure credentials from environment
        tenant_id = os.getenv('AZURE_TENANT_ID')
        client_id = os.getenv('AZURE_CLIENT_ID') 
        client_secret = os.getenv('AZURE_CLIENT_SECRET')
        endpoint = os.getenv('AZURE_ENDPOINT')
        agent_id = os.getenv('AZURE_AGENT_ID')
        
        # Validate required environment variables
        if not all([tenant_id, client_id, client_secret, endpoint, agent_id]):
            missing = [var for var, val in {
                'AZURE_TENANT_ID': tenant_id,
                'AZURE_CLIENT_ID': client_id,
                'AZURE_CLIENT_SECRET': client_secret,
                'AZURE_ENDPOINT': endpoint,
                'AZURE_AGENT_ID': agent_id
            }.items() if not val]
            
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        # Initialize Azure credentials
        self.credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        self.project = AIProjectClient(
            credential=self.credential,
            endpoint=endpoint
        )
        self.agent = self.project.agents.get_agent(agent_id)

    async def create_streaming_response(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        """Create a streaming response in OpenAI format"""
        request_id = f"chatcmpl-{uuid.uuid4().hex[:29]}"
        created = int(datetime.now().timestamp())

        try:
            # Get the response from Foundry Agent (non-streaming)
            response = await self.create_chat_completion(request)
            content = response.choices[0].message.content

            # First chunk with role
            first_chunk = ChatCompletionStreamResponse(
                id=request_id,
                created=created,
                model=request.model,
                choices=[
                    StreamChoice(
                        index=0,
                        delta=Delta(role="assistant", content=""),
                        finish_reason=None
                    )
                ]
            )
            yield f"data: {json.dumps(first_chunk.model_dump())}\n\n"

            # Stream content in small chunks
            words = content.split()
            for i, word in enumerate(words):
                chunk_content = word + (" " if i < len(words) - 1 else "")

                chunk = ChatCompletionStreamResponse(
                    id=request_id,
                    created=created,
                    model=request.model,
                    choices=[
                        StreamChoice(
                            index=0,
                            delta=Delta(content=chunk_content),
                            finish_reason=None
                        )
                    ]
                )

                yield f"data: {json.dumps(chunk.model_dump())}\n\n"
                await asyncio.sleep(0.05)  # Small delay to simulate streaming

            # Final chunk with finish_reason
            final_chunk = ChatCompletionStreamResponse(
                id=request_id,
                created=created,
                model=request.model,
                choices=[
                    StreamChoice(
                        index=0,
                        delta=Delta(),
                        finish_reason="stop"
                    )
                ]
            )
            yield f"data: {json.dumps(final_chunk.model_dump())}\n\n"

            # End of stream marker
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            # Send error as stream
            error_chunk = ChatCompletionStreamResponse(
                id=request_id,
                created=created,
                model=request.model,
                choices=[
                    StreamChoice(
                        index=0,
                        delta=Delta(role="assistant", content=f"Error: {str(e)}"),
                        finish_reason="stop"
                    )
                ]
            )
            yield f"data: {json.dumps(error_chunk.model_dump())}\n\n"
            yield "data: [DONE]\n\n"

    async def create_chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        try:
            logger.info(f"Processing chat completion request with {len(request.messages)} messages")

            # Create thread
            thread = self.project.agents.threads.create()
            logger.info(f"Created thread: {thread.id}")

            # Find the last user message
            last_user_message = None
            for msg in reversed(request.messages):
                if msg.role == "user":
                    last_user_message = msg.content
                    break

            if not last_user_message:
                logger.error("No user message found in request")
                raise HTTPException(status_code=400, detail="No user message found")

            # Create message in thread
            message = self.project.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=last_user_message
            )

            # Run the agent
            run = self.project.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=self.agent.id
            )

            logger.info(f"Run completed with status: {run.status}")

            if run.status == "failed":
                logger.error(f"Run failed: {run.last_error}")
                raise HTTPException(status_code=500, detail=f"Agent run failed: {run.last_error}")

            # Get all messages from the thread
            messages_pager = self.project.agents.messages.list(
                thread_id=thread.id,
                order=ListSortOrder.ASCENDING
            )

            # Convert ItemPaged to list
            messages = list(messages_pager)
            logger.info(f"Retrieved {len(messages)} messages from thread")

            # Find the assistant's response
            assistant_response = None
            assistant_messages = []

            for message in messages:
                if message.role == "assistant":
                    # Try to extract content from text_messages
                    if hasattr(message, 'text_messages') and message.text_messages:
                        for text_msg in message.text_messages:
                            if hasattr(text_msg, 'text') and text_msg.text:
                                if hasattr(text_msg.text, 'value'):
                                    assistant_messages.append(text_msg.text.value)
                                elif hasattr(text_msg.text, 'content'):
                                    assistant_messages.append(text_msg.text.content)
                            elif hasattr(text_msg, 'content'):
                                assistant_messages.append(text_msg.content)

            # Combine all assistant messages
            if assistant_messages:
                assistant_response = "\n".join(assistant_messages)
            else:
                logger.warning("No assistant response found, using fallback")
                assistant_response = "I apologize, but I couldn't generate a proper response. Please try again."

            # Calculate token usage (approximate)
            prompt_tokens = len(last_user_message.split()) if last_user_message else 0
            completion_tokens = len(assistant_response.split()) if assistant_response else 0
            total_tokens = prompt_tokens + completion_tokens

            # Create the response
            response = ChatCompletionResponse(
                id=f"chatcmpl-{uuid.uuid4().hex[:29]}",
                created=int(datetime.now().timestamp()),
                model=request.model,
                choices=[
                    Choice(
                        index=0,
                        message=Message(role="assistant", content=assistant_response),
                        finish_reason="stop"
                    )
                ],
                usage=Usage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens
                )
            )

            logger.info("Response created successfully")
            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in chat completion: {str(e)}")
            # Return a valid response even on error to prevent client-side crashes
            return ChatCompletionResponse(
                id=f"chatcmpl-error-{uuid.uuid4().hex[:20]}",
                created=int(datetime.now().timestamp()),
                model=request.model,
                choices=[
                    Choice(
                        index=0,
                        message=Message(role="assistant", content=f"I apologize, but an error occurred: {str(e)}"),
                        finish_reason="stop"
                    )
                ],
                usage=Usage(
                    prompt_tokens=0,
                    completion_tokens=10,
                    total_tokens=10
                )
            )

adapter = None

@app.on_event("startup")
async def startup_event():
    global adapter
    adapter = FoundryAgentAdapter()
    logger.info("Foundry Agent adapter initialized")

@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest):
    if not adapter:
        raise HTTPException(status_code=500, detail="Adapter not initialized")

    # Check if streaming is requested
    if request.stream:
        logger.info("Streaming response requested")
        
        # Convert request to dict for audit
        request_dict = request.model_dump()

        headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*",
        }

        # Create a wrapper generator to collect streaming data for audit
        async def streaming_with_audit():
            collected_chunks = []
            collected_content = ""
            
            try:
                async for chunk in adapter.create_streaming_response(request):
                    collected_chunks.append(chunk)
                    
                    # Extract content from chunk for audit
                    if chunk.startswith("data: ") and not chunk.startswith("data: [DONE]"):
                        try:
                            chunk_data = chunk[6:].strip()  # Remove "data: " prefix
                            if chunk_data:
                                chunk_json = json.loads(chunk_data)
                                if "choices" in chunk_json and chunk_json["choices"]:
                                    delta = chunk_json["choices"][0].get("delta", {})
                                    if "content" in delta and delta["content"]:
                                        collected_content += delta["content"]
                        except json.JSONDecodeError:
                            pass  # Skip malformed chunks
                    
                    yield chunk
                
                # Save audit data after streaming completes
                streaming_audit_data = {
                    "chunks": collected_chunks,
                    "full_content": collected_content,
                    "chunk_count": len(collected_chunks)
                }
                save_audit_data(request_dict, streaming_audit_data, "chat_completion_streaming")
                
            except Exception as e:
                logger.error(f"Error in streaming audit: {e}")
                # Save error audit data
                error_audit_data = {
                    "error": str(e),
                    "chunks_before_error": collected_chunks
                }
                save_audit_data(request_dict, error_audit_data, "chat_completion_streaming_error")
                raise

        return StreamingResponse(
            streaming_with_audit(),
            media_type="text/event-stream",
            headers=headers
        )

    # Non-streaming response
    try:
        # Convert request to dict for audit
        request_dict = request.model_dump()
        
        response = await adapter.create_chat_completion(request)

        # Basic validation
        if not response.choices or len(response.choices) == 0:
            logger.error("Response has no choices")
            raise HTTPException(status_code=500, detail="Response contained no choices")

        logger.info("Returning successful response")
        
        # Convert response to dict for audit
        response_dict = response.model_dump()
        
        # Save audit data
        save_audit_data(request_dict, response_dict, "chat_completion_non_streaming")

        # Return with OpenAI-compatible headers
        headers = {
            "Content-Type": "application/json",
            "openai-version": "2020-10-01",
            "openai-model": response.model,
            "x-request-id": response.id,
        }

        return JSONResponse(
            content=response_dict,
            status_code=200,
            headers=headers
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in endpoint: {str(e)}")
        
        # Convert request to dict for audit
        request_dict = request.model_dump()
        
        # Return a fail-safe response
        fallback_response = ChatCompletionResponse(
            id=f"chatcmpl-failsafe-{uuid.uuid4().hex[:20]}",
            created=int(datetime.now().timestamp()),
            model=request.model,
            choices=[
                Choice(
                    index=0,
                    message=Message(role="assistant", content="I apologize, but I encountered an error processing your request. Please try again."),
                    finish_reason="stop"
                )
            ],
            usage=Usage(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30
            )
        )
        
        # Convert response to dict for audit
        response_dict = fallback_response.model_dump()
        response_dict["error"] = str(e)  # Add error info to audit
        
        # Save audit data for error case
        save_audit_data(request_dict, response_dict, "chat_completion_error")

        headers = {
            "Content-Type": "application/json",
            "openai-version": "2020-10-01",
            "openai-model": request.model,
            "x-request-id": fallback_response.id
        }

        return JSONResponse(
            content=fallback_response.model_dump(),
            status_code=200,
            headers=headers
        )

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "foundry-agent-model",
                "object": "model",
                "created": int(datetime.now().timestamp()),
                "owned_by": "foundry"
            }
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    # Get server configuration from environment variables
    host = os.getenv('SERVER_HOST', '0.0.0.0')
    port = int(os.getenv('SERVER_PORT', '8000'))
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)