# get_ai_response/main.py

import asyncio

from rag import rag



async def main():
    messages = []

    while True:
        text = input("Enter your question:\n")
        messages.append({
            "role": "user",
            "content": [{
                "type": "text",
                "text": text
            }]
        })

        answer, image_number, original_value, new_value = await rag(messages)
        messages.append({
            "role": "assistant",
            "content": [{
                "type": "text",
                "text": answer
            }]
        })

        # execute tool
        # if image_number and original_value and new_value:
        #     


if __name__ == "__main__":
    asyncio.run(main())