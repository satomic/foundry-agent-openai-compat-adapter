import openai

client = openai.OpenAI(
    api_key="not-needed",  # any string is ok
    base_url="http://localhost:8000/v1"
)

# non-streaming
response = client.chat.completions.create(
    model="foundry-agent-model",
    messages=[
        {"role": "user", "content": "hello, what is 2+2?"}
    ],
    temperature=0.7,
    max_tokens=150
)

print(response.choices[0].message.content)

# streaming
stream = client.chat.completions.create(
    model="foundry-agent-model",
    messages=[
        {"role": "user", "content": "change website color to yellow, and text to 'Hello, world!'"}
    ],
    temperature=0.7,
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")