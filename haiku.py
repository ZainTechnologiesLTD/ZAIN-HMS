import os
from openai import OpenAI

# Read the key from the environment variable you exported above
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

response = client.responses.create(
    # pick a valid model; these are good defaults:
    model="gpt-5",      # fast & inexpensive
    # or: model="o3-mini",     # stronger reasoning (slower/pricier)
    input="write a haiku about AI",
)

# New Responses API: read the first text item
print(response.output[0].content[0].text)
