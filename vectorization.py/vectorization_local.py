# vectorization\vectorization_local.py

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from PIL import Image
import numpy as np
import torch, io

from config import VECT_MODEL_NAME



if torch.backends.mps.is_available():
    DEVICE = "mps"
    print("MPS backend is available. Using Apple Silicon GPU.")
elif torch.cuda.is_available():
    DEVICE = "cuda"
    print(f"CUDA Available: {torch.cuda.is_available()}")
    try:
        print(f"Device: {torch.cuda.current_device()}")
        print(f"Device Name: {torch.cuda.get_device_name(0)}")
    except Exception as e:
        print(f"Could not get CUDA device details: {e}")
else:
    DEVICE = "cpu"
    print("MPS and CUDA not available. Using CPU.")

print(f"Loading model: {VECT_MODEL_NAME}")
model = HuggingFaceEmbedding(
    model_name=VECT_MODEL_NAME,
    device=DEVICE,
    trust_remote_code=True
)



async def embed_text(request: dict):
    try:
        embeddings = []
        
        for text in request["texts"]:
            print(f"Processing query: {text}")
            
            query_embedding = model.get_query_embedding(text)
            
            if isinstance(query_embedding, np.ndarray):
                query_embedding = query_embedding.tolist()
            
            embeddings.append(query_embedding)

        return embeddings

    except Exception as e:
        import traceback
        print(f"Error details: {traceback.format_exc()}")
        raise Exception(f"Text embedding failed: {str(e)}")



async def embed_images(files: dict):
    try:
        if len(files) != 1:
            raise ValueError("Expected exactly one file for embedding")
        file_tuple = list(files.values())[0]
        _, image_bytes, _ = file_tuple
        
        image = Image.open(io.BytesIO(image_bytes))
        print(f"Processing image of size: {image.size}")
        
        image_embedding = model.get_image_embedding(image)
        
        if isinstance(image_embedding, np.ndarray):
            image_embedding = image_embedding.tolist()
        
        return image_embedding

    except Exception as e:
        import traceback
        print(f"Error details: {traceback.format_exc()}")
        raise Exception(f"Image embedding failed: {str(e)}")