from datasets import load_dataset
from PIL import Image
from io import BytesIO
from config import LOCAL_STORAGE_PATH

# Load the dataset
ds = load_dataset("staghado/ArXiv-tables", split="train")

# Extract and save all images
dataset_length = len(ds)
for i in range(dataset_length):
    for img_type in ["table_image", "page_image"]:
        img_bytes = ds[i][img_type]  # already bytes!
        img = Image.open(BytesIO(img_bytes))
        img.save(f"{LOCAL_STORAGE_PATH}/{i}.jpg")
            
        
print("Images saved!")  