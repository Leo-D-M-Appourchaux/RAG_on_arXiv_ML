# Here is an example code that downloads the dataset on HuggingFace and saves 2 images to see what we're dealing with

from datasets import load_dataset
from PIL import Image
from io import BytesIO

# Load the dataset
ds = load_dataset("staghado/ArXiv-tables", split="train")

# Extract and save the first two entries
for i in range(2):
    for img_type in ["table_image", "page_image"]:
        img_bytes = ds[i][img_type]  # already bytes!
        img = Image.open(BytesIO(img_bytes))
        img.save(f"{img_type}_{i}.png")

print("Images saved!")
