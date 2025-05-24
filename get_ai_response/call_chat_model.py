# get_ai_response/call_chat_model.py

from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, TextIteratorStreamer
from qwen_vl_utils import process_vision_info
import threading
import torch



# Set up device
if torch.backends.mps.is_available():
    DEVICE = "mps"
    torch.mps.empty_cache()
    print("MPS backend is available. Using Apple Silicon GPU")
elif torch.cuda.is_available():
    DEVICE = "cuda"
    print(f"CUDA available: {torch.cuda.is_available()}")
    try:
        print(f"Device: {torch.cuda.current_device()}")
        print(f"Device name: {torch.cuda.get_device_name(0)}")
    except Exception as e:
        print(f"Could not get CUDA device details: {e}")
else:
    DEVICE = "cpu"
    print("MPS and CUDA not available, using CPU")


model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-VL-3B-Instruct", torch_dtype="auto", device_map="auto"
)
processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-3B-Instruct")



async def generate_answer(messages: list, images: list = None):
    content = []
    if images:
        for image_bytes in images:
            content.append({
                "type": "image", 
                "image": f"data:image;base64,{image_bytes}"
            })
    message_retriever = [{"role": "user", "content": content}]
    conv_to_send = messages + message_retriever
    
    try:
        text = processor.apply_chat_template(
            conv_to_send, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(conv_to_send)
        inputs = processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to(DEVICE)
        
        streamer = TextIteratorStreamer(
            processor.tokenizer, 
            skip_special_tokens=True, 
            skip_prompt=True
        )
        
        generation_kwargs = {
            **inputs,
            "streamer": streamer,
            "max_new_tokens": 1024
        }
        
        # Create a thread to run the generation
        thread = threading.Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()
        
        # Return the streamer that will yield tokens
        return streamer
        
    except Exception as e:
        return iter(["Error generating response: " + str(e)])