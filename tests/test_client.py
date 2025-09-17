import requests
import json

# Example usage of the OpenAI-compatible adapter
def test_chat_completion():
    url = "http://localhost:8000/v1/chat/completions"

    payload = {
        "model": "foundry-agent-model",
        "messages": [
            {"role": "user", "content": "Hello, who are you?"}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        result = response.json()
        print("Success!")
        print(f"Response: {result['choices'][0]['message']['content']}")
        print(f"Usage: {result['usage']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def test_models():
    url = "http://localhost:8000/v1/models"
    response = requests.get(url)

    if response.status_code == 200:
        result = response.json()
        print("Available models:")
        for model in result['data']:
            print(f"- {model['id']}")
    else:
        print(f"Error: {response.status_code}")

if __name__ == "__main__":
    print("Testing OpenAI-compatible Foundry Agent adapter...")

    print("\n1. Testing /v1/models endpoint:")
    test_models()

    print("\n2. Testing /v1/chat/completions endpoint:")
    test_chat_completion()