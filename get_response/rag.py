import os
from config import LOCAL_STORAGE_PATH
import aiofiles

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

