# get_ai_response/main.py

import asyncio
import sys
import os

# Add the parent directory to sys.path to enable imports from adjacent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from get_ai_response.prompt import PROMPT
from get_ai_response.rag import rag



async def main():
    messages = [{"role": "system",
            "content": [{
                "type": "text",
                "text": PROMPT}]}]

    old_image_ids = None

    while True:
        text = input("Enter your question:\n")
        messages.append({
            "role": "user",
            "content": [{
                "type": "text",
                "text": text
            }]
        })

        messages, image_ids = await rag(messages, old_image_ids)
        old_image_ids = image_ids


if __name__ == "__main__":
    asyncio.run(main())