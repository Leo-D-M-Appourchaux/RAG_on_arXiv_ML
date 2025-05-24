# get_ai_response/rag.py

import aiofiles
import base64
import json
import sys
import os

# Add the parent directory to sys.path to enable imports from adjacent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PROCESSED_FOLDER
from database.search_in_db import combine_search_results
from get_ai_response.call_chat_model import generate_answer
from database.image_processing import resize_base64_image



async def get_files(image_id):
    file_path = os.path.join(PROCESSED_FOLDER, f"{image_id}_full.jpg")
    try:
        async with aiofiles.open(file_path, 'rb') as f : #f is the image that we open and f disappears once we get out of with 
            image_bytes = await f.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            return image_base64
    except FileNotFoundError:
        print(f"Error file not found: {file_path}")
    except Exception as e:
        print(f"Error processing image {image_id}: {str(e)}")
    return None



async def catch_tool_call(text: str):
    if text.startswith("{"):
        try:
            json_code = json.loads(text)

            image_number = json_code['image_number']
            original_value = json_code['original_value']
            new_value = json_code['new_value']
            
            return image_number, original_value, new_value
        except json.JSONDecodeError:
            print("Error decoding JSON")
            return None, None, None
    return None, None, None



async def rag(messages: list):
    query = messages[-1]["content"][0]["text"]
    image_ids = await combine_search_results(query)
    images_bytes = []
    for id in image_ids:
        bytes = await get_files(id)
        resized_bytes = await resize_base64_image(bytes)
        images_bytes.append(resized_bytes)
    
    image_numbers = [i for i in range(len(images_bytes))]
    retriever_message = [{"role": "tool", "content": [{"type": "text", "text": str(image_numbers)}]}]
    messages = messages + retriever_message

    streamer = await generate_answer(messages, images_bytes)
    full_answer = ""
    for chunk in streamer:
        full_answer += chunk
        print(chunk, end="", flush=True)

    messages.append({
            "role": "assistant",
            "content": [{
                "type": "text",
                "text": full_answer
            }]
        })
    
    image_number, original_value, new_value = await catch_tool_call(full_answer)

    return messages, image_number, original_value, new_value