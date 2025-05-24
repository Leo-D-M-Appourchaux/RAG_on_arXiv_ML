# get_ai_response/rag.py

import aiofiles
import base64
import json
import sys
import os
import cv2
import base64
import numpy as np

# Add the parent directory to sys.path to enable imports from adjacent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PROCESSED_FOLDER
from database.search_in_db import combine_search_results
from get_ai_response.call_chat_model import generate_answer
from database.image_processing import resize_base64_image
from database.getters_latex import db_get_image_latex
from get_ai_response.latex_to_image import modify_numeric_values, latex_to_base64

# Global counter for unique window names
_window_counter = 0



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
    text = text.replace("[", "").replace("]", "").strip()

    if "```json" in text and "```" in text:
        try:
            json_str = text[text.index("```json") + len("```json"):text.rindex("```")].strip()
            print("Extracted JSON:", json_str)
            json_code = json.loads(json_str)
            print(type(json_code))
            return (json_code['image_number'], json_code['original_value'], json_code['new_value'])
        except json.JSONDecodeError:
            print("Error decoding JSON")
            return None, None, None
    elif "{" in text and "}" in text:
        try:
            start = text.index("{")
            end = text.index("}") + 1
            json_str = text[start:end]
            print("Extracted JSON:", json_str)
            json_code = json.loads(json_str)
            print(type(json_code))
            return (json_code['image_number'], json_code['original_value'], json_code['new_value'])
        except json.JSONDecodeError:
            print("Error decoding JSON")
            return None, None, None
    return None, None, None


async def show_base64_image(base64_str, window_name=None):
    global _window_counter
    try:
        # Use provided window_name or generate a unique one
        if window_name is None:
            window_name = f"Base64 Image {_window_counter}"
            _window_counter += 1
        # Decode base64 string to bytes
        image_data = base64.b64decode(base64_str)
        # Convert bytes to NumPy array
        np_arr = np.frombuffer(image_data, np.uint8)
        # Decode image from NumPy array
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if image is None:
            print(f"Failed to decode image for window {window_name}")
            return
        # Display the image in a named window
        cv2.imshow(window_name, image)
        # Brief delay to allow window to render without blocking
        cv2.waitKey(1)  # Non-blocking, allows window to stay open
    except Exception as e:
        print(f"Error displaying image {window_name}: {str(e)}")



async def rag(messages: list, old_image_ids: list = None):
    query = messages[-1]["content"][0]["text"]
    image_ids = await combine_search_results(query)
    images_bytes = []
    for id in image_ids:
        bytes = await get_files(id)
        resized_bytes = await resize_base64_image(bytes)
        await show_base64_image(resized_bytes)
        images_bytes.append(resized_bytes)
    
    image_numbers = [i for i in range(len(images_bytes))]
    indexes_message = [{"role": "tool", "content": [{"type": "text", "text": str(image_numbers)}]}]
    messages = messages + indexes_message

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
    
    print("Image number:", image_number)
    print("Original value:", original_value)
    print("New value:", new_value)
    
    if image_number:
        print("Image number found")
        target_id = old_image_ids[int(image_number) % 3]
        print("Target image id:", target_id)
        latex_code = await db_get_image_latex(target_id)
        print("Latex code generated")
        new_latex = modify_numeric_values(latex_code, str(original_value), str(new_value))
        print("Latex code modified")
        image_base64 = latex_to_base64(new_latex)
        print("Image base64 generated")
        await show_base64_image(image_base64)
        
    return messages, image_ids