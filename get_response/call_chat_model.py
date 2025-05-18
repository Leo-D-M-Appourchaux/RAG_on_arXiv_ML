from transformers import Qwen2_5_VLForConditionalGeneration, AutoTokenizer, AutoProcessor
from qwen_vl_utils import process_vision_info
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

async def generate_answer(messages: list, images: list):
    content = []
    for image_bytes in images:
        content.append({
            "type": "image", 
            "image": f"data:image;base64,{image_bytes}"
        })
    messages.append({"role": "user", "content": content})
    
    try:
        text = processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to(DEVICE)
        
        generated_ids = model.generate(**inputs, max_new_tokens=128)
        generated_ids_trimmed = [
            out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )
        return(output_text)
    except Exception as e:
        print(f"Error: {e}")