import os
from config import LOCAL_STORAGE_PATH
import aiofiles
from utils.search_in_db import combine_search_results
from get_response.call_chat_model import generate_answer
import asyncio

async def get_files (image_id):
    file_path = os.path.join(LOCAL_STORAGE_PATH, f"{image_id}_full.jpg")
    try:
        async with aiofiles.open(file_path, 'rb') as f : #f is the image that we open and f disappears once we get out of with 
            image_bytes = await f.read()
    except FileNotFoundError:
        print(f"Error file not found: {file_path}")
    except Exception as e:
        print(f"Error processing image {image_id}: {str(e)}")
    return image_bytes

async def rag (messages: list):
    query = messages[-1]["content"][0]["text"]
    image_ids = await combine_search_results(query, [])
    images_bytes = []
    for id in image_ids:
        bytes = await get_files(id)
        images_bytes.append(bytes)
    answer = await generate_answer(messages, images_bytes)
    print(answer)
    
messages = [{
    "role": "user",
    "content": [{
        "type": "text",
        "text": "Make a short synthesis of the algorithm 3"
    }]
}]

if __name__ == "__main__":
    asyncio.run(rag(messages))