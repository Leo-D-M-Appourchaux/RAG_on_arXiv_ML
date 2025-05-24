from PIL import Image
import io
import math
import base64


async def resize_base64_image(base64_string: str, max_pixels: int = 1000000) -> str:
    try:
        image_bytes = base64.b64decode(base64_string)
        img = Image.open(io.BytesIO(image_bytes))
        orig_width, orig_height = img.size
        total_pixels = orig_width * orig_height

        if total_pixels > max_pixels:
            scale_factor = math.sqrt(max_pixels / total_pixels)
            new_width = int(orig_width * scale_factor)
            new_height = int(orig_height * scale_factor)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        resized_bytes = buffer.getvalue()
        resized_base64 = base64.b64encode(resized_bytes).decode('utf-8')
        return resized_base64

    except Exception as e:
        print(f"Error processing base64 image: {str(e)}")
        return None