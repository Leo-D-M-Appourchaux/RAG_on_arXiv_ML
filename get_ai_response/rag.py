# get_ai_response/rag.py

import aiofiles
import base64
import json
import sys
import os
from database.getters_latex import db_get_image_latex
from get_ai_response.latex_to_image import modify_numeric_values, latex_to_base64
import cv2
import base64
import numpy as np

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


def show_base64_image(base64_str):
    # Decode base64 string to bytes
    image_data = base64.b64decode(base64_str)

    # Convert bytes to NumPy array
    np_arr = np.frombuffer(image_data, np.uint8)

    # Decode image from NumPy array
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Display the image
    cv2.imshow("Base64 Image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()



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
    
    target_id = None
    
    if image_number: 
        target_id = image_ids[image_number]
        latex_code = db_get_image_latex(target_id)
        new_latex = modify_numeric_values(latex_code, original_value, new_value)
        image_base64 = latex_to_base64(new_latex)
        show_base64_image(image_base64)
        

    return messages, target_id, original_value, new_value