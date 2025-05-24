from datasets import load_dataset
import glob
import os
from latex_to_image import latex_to_image_object

# Load dataset
dataset = load_dataset("staghado/ArXiv-tables") 

# Clean up previous files
for ext in ["aux", "log", "fls", "pdf"]:
    for f in glob.glob(f"outputs/*.{ext}"):
        try:
            os.remove(f)
        except:
            pass

# Process tables with error handling
for i in range(10):
    try:
        print(f"\nProcessing table {i}...")
        latex = dataset["train"][i]["latex_content"]
        
        # Print first 200 characters for debugging
        print(f"LaTeX content preview: {latex[:200]}...")
        
        image = latex_to_image_object(latex)
        resized = image.resize((800, 600))
        resized.save(f"resized_table_{i}.png")
        print(f"Successfully saved resized_table_{i}.png")
        
    except Exception as e:
        print(f"Error processing table {i}: {e}")
        # Save the problematic LaTeX for manual inspection
        with open(f"failed_latex_{i}.tex", "w", encoding='utf-8') as f:
            f.write(latex)
        continue

print("Processing complete!")
