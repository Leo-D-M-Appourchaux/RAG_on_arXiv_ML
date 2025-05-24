# get_ai_response/main.py

import asyncio
import sys
import os
from get_ai_response.prompt import PROMPT

# Add the parent directory to sys.path to enable imports from adjacent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from get_ai_response.rag import rag



async def main():
    messages = [{"role": "system",
            "content": [{
                "type": "text",
                "text": PROMPT}]}]

    while True:
        text = input("Enter your question:\n")
        messages.append({
            "role": "user",
            "content": [{
                "type": "text",
                "text": text
            }]
        })

        messages, target_id, original_value, new_value = await rag(messages)

        # execute tool
        # if image_number and original_value and new_value:
        #     


if __name__ == "__main__":
    asyncio.run(main())