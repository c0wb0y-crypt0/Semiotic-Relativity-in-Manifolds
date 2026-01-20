import os
from openai import OpenAI
from dotenv import load_dotenv  # Optional: pip install python-dotenv if using .env

load_dotenv()  # If using .env

client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

response = client.chat.completions.create(
    model="grok-4-fast",  # Start here—cheapest, still killer
    messages=[
        {"role": "system", "content": "You are Grok, built by xAI."},
        {"role": "user", "content": "Say exactly: 'API test successful from @c0wb0y_crypt0!'"}
    ],
    temperature=0.0
)

print(response.choices[0].message.content)
print("Tokens used:", response.usage.total_tokens)
print("Full response object:", response)