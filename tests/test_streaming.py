import requests
import json
import sys

def test_streaming_response():
    """Test streaming chat completion"""
    url = "http://localhost:8000/v1/chat/completions"

    # Test streaming request
    payload = {
        "model": "foundry-agent-model",
        "messages": [
            {"role": "user", "content": "Hello, can you tell me a short story?"}
        ],
        "temperature": 0.7,
        "stream": True  # Enable streaming
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    print("🌊 Testing STREAMING response...")
    print("Request payload:")
    print(json.dumps(payload, indent=2))
    print("\nStreaming response:")
    print("-" * 50)

    try:
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=60)

        if response.status_code == 200:
            collected_content = ""

            for line in response.iter_lines(decode_unicode=True):
                if line:
                    print(f"Raw line: {line}")

                    if line.startswith("data: "):
                        data_content = line[6:]  # Remove "data: " prefix

                        if data_content == "[DONE]":
                            print("✅ Stream completed with [DONE]")
                            break

                        try:
                            chunk_data = json.loads(data_content)
                            print(f"Parsed chunk: {json.dumps(chunk_data, indent=2)}")

                            # Extract content from delta
                            if chunk_data.get("choices") and len(chunk_data["choices"]) > 0:
                                delta = chunk_data["choices"][0].get("delta", {})
                                if "content" in delta and delta["content"]:
                                    collected_content += delta["content"]
                                    print(f"Content so far: {collected_content}")

                        except json.JSONDecodeError as e:
                            print(f"Failed to parse JSON: {e}")
                            print(f"Data content: {data_content}")

            print("-" * 50)
            print(f"✅ Final collected content: {collected_content}")

        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the server running?")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_non_streaming_response():
    """Test non-streaming chat completion"""
    url = "http://localhost:8000/v1/chat/completions"

    # Test non-streaming request
    payload = {
        "model": "foundry-agent-model",
        "messages": [
            {"role": "user", "content": "Hello, what is 2+2?"}
        ],
        "temperature": 0.7,
        "stream": False  # Disable streaming
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("\n📄 Testing NON-STREAMING response...")
    print("Request payload:")
    print(json.dumps(payload, indent=2))
    print("\nResponse:")
    print("-" * 50)

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)

        if response.status_code == 200:
            result = response.json()
            print("✅ Non-streaming response:")
            print(json.dumps(result, indent=2))

            # Validate choices
            if "choices" in result and result["choices"]:
                print(f"✅ Response has {len(result['choices'])} choices")
                print(f"Content: {result['choices'][0]['message']['content']}")
            else:
                print("❌ Response missing choices or choices empty")

        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Foundry Agent Streaming Adapter")
    print("=" * 60)

    # Test both streaming and non-streaming
    test_non_streaming_response()
    test_streaming_response()

    print("\n" + "=" * 60)
    print("Tests completed!")