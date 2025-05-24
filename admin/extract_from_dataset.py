# admin/extract_from_dataset.py

from datasets import load_dataset
import concurrent.futures
from io import BytesIO
from PIL import Image
import argparse
import tqdm
import sys
import os

# Add the parent directory to sys.path to enable imports from adjacent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import EXTRACTION_FOLDER



def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Extract images and LaTeX code from the ArXiv-tables dataset")
    parser.add_argument("-n", "--num_samples", type=int, default=10, 
                        help="Number of samples to extract (default: 10)")
    parser.add_argument("-o", "--output_dir", type=str, default=EXTRACTION_FOLDER,
                        help=f"Output directory for extracted files (default: {EXTRACTION_FOLDER})")
    parser.add_argument("-b", "--batch_size", type=int, default=4,
                        help="Batch size for processing (default: 4)")
    return parser.parse_args()



def ensure_directory_exists(directory):
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")



def process_sample(sample, index, output_dir):
    """Process a single sample from the dataset."""
    try:
        # Extract image and save as JPG
        img_bytes = sample["page_image"]
        img = Image.open(BytesIO(img_bytes))
        img_path = os.path.join(output_dir, f"sample_{index}.jpg")
        img.save(img_path, optimize=True)
        
        # Extract LaTeX content and save as TXT
        latex_content = sample["latex_content"]
        txt_path = os.path.join(output_dir, f"sample_{index}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(latex_content)
        
        return True
    except Exception as e:
        print(f"Error processing sample {index}: {str(e)}")
        return False



def extract_dataset(num_samples, output_dir, batch_size=4):
    """Extract images and LaTeX code from the ArXiv-tables dataset."""
    # Ensure output directory exists
    ensure_directory_exists(output_dir)
    
    print(f"Loading dataset 'staghado/ArXiv-tables'...")
    dataset = load_dataset("staghado/ArXiv-tables", split="train")
    
    # Determine actual number of samples to extract
    available_samples = len(dataset)
    num_samples = min(num_samples, available_samples)
    
    print(f"Dataset loaded successfully! Total available samples: {available_samples}")
    print(f"Extracting {num_samples} samples to {output_dir}...")
    
    successful = 0
    
    # Use ThreadPoolExecutor for parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
        # Create a dictionary of futures to their index
        future_to_idx = {
            executor.submit(process_sample, dataset[i], i, output_dir): i 
            for i in range(num_samples)
        }
        
        # Process as completed with progress bar
        for future in tqdm.tqdm(concurrent.futures.as_completed(future_to_idx), 
                               total=num_samples, 
                               desc="Extracting samples"):
            idx = future_to_idx[future]
            try:
                if future.result():
                    successful += 1
            except Exception as e:
                print(f"Exception occurred while processing sample {idx}: {str(e)}")
    
    print(f"Extraction complete! Successfully processed {successful}/{num_samples} samples.")
    print(f"Files saved to: {output_dir}")



def main():
    """Main entry point."""
    args = parse_arguments()
    extract_dataset(
        num_samples=args.num_samples,
        output_dir=args.output_dir,
        batch_size=args.batch_size
    )



if __name__ == "__main__":
    main()