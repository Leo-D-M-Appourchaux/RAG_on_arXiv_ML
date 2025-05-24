# get_ai_response/latex_to_image.py

from pdf2image import convert_from_path
from pylatex import Document, NoEscape
import tempfile
import shutil
import base64
import re
import io
import os


def auto_complete_latex_environments(latex_str):
    """
    Properly close LaTeX environments in the correct nesting order
    """
    # Define environment patterns
    begin_pattern = r'\\begin\{([^}]+)\}'
    end_pattern = r'\\end\{([^}]+)\}'
    
    # Find all begin and end environments
    begins = [(m.start(), m.group(1)) for m in re.finditer(begin_pattern, latex_str)]
    ends = [(m.start(), m.group(1)) for m in re.finditer(end_pattern, latex_str)]
    
    # Create a stack to track unclosed environments
    stack = []
    begin_idx = 0
    end_idx = 0
    
    # Process environments in order of appearance
    all_positions = []
    for pos, env in begins:
        all_positions.append((pos, 'begin', env))
    for pos, env in ends:
        all_positions.append((pos, 'end', env))
    
    # Sort by position
    all_positions.sort()
    
    # Track unclosed environments
    for pos, action, env in all_positions:
        if action == 'begin':
            stack.append(env)
        elif action == 'end':
            if stack and stack[-1] == env:
                stack.pop()
            # If end doesn't match, we have malformed LaTeX, but continue
    
    # Add missing end environments in reverse order
    missing_ends = []
    while stack:
        env = stack.pop()
        missing_ends.append(f"\\end{{{env}}}")
    
    if missing_ends:
        latex_str += "\n" + "\n".join(missing_ends)
    
    return latex_str



def latex_to_image_object(latex_str):
    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_name = os.path.join(temp_dir, "temp_latex")
        
        print("Starting LaTeX compilation...")

        # Create LaTeX document object
        doc = Document()
        
        # Add required packages
        doc.packages.append(NoEscape(r'\usepackage{float}'))        
        doc.packages.append(NoEscape(r'\usepackage{booktabs}'))     
        doc.packages.append(NoEscape(r'\usepackage{graphicx}'))     
        doc.packages.append(NoEscape(r'\usepackage{multirow}'))     
        doc.packages.append(NoEscape(r'\usepackage{makecell}'))     
        doc.packages.append(NoEscape(r'\usepackage{cite}'))         
        doc.packages.append(NoEscape(r'\usepackage{threeparttable}'))
        doc.packages.append(NoEscape(r'\usepackage{xcolor}'))
        doc.packages.append(NoEscape(r'\usepackage{amssymb}'))      
        doc.packages.append(NoEscape(r'\usepackage{hyperref}'))     
        doc.packages.append(NoEscape(r'\usepackage{textcomp}'))     
        
        # Add specialcell macro definition
        doc.preamble.append(NoEscape(r'\newcommand{\specialcell}[2][c]{\begin{tabular}[#1]{@{}c@{}}#2\end{tabular}}'))

        # Auto-complete missing LaTeX structure with proper nesting
        latex_str = auto_complete_latex_environments(latex_str)
            
        doc.append(NoEscape(latex_str))  # Add table content

        # Generate PDF file
        try:
            doc.generate_pdf(temp_name, clean_tex=True)
        except Exception as e:
            print(f"LaTeX compilation failed: {e}")
            raise
            
        pdf_path = f"{temp_name}.pdf"
        
        if not os.path.exists(pdf_path):
            raise Exception("Failed to generate PDF file")
        
        print("PDF compiled successfully")

        # Convert PDF to PIL Image
        poppler_path = shutil.which("pdftoppm")
        images = convert_from_path(
            pdf_path,
            poppler_path=os.path.dirname(poppler_path) if poppler_path else None
        )
        
        if not images:
            raise Exception("Failed to convert PDF to image")
        
        print("Image conversion successful")
        return images[0]



def save_latex_as_image(latex_str, outname: str):
    os.makedirs("outputs", exist_ok=True)
    print("Starting render:", outname)
    image = latex_to_image_object(latex_str)
    png_path = f"{outname}.png"
    image.save(png_path, "PNG")
    print("PNG generated:", os.path.exists(png_path))
    return png_path



def latex_to_bytes(latex_str, format="JPG"):
    image = latex_to_image_object(latex_str)
    img_bytes = io.BytesIO()
    image.save(img_bytes, format=format)
    img_bytes.seek(0)
    return img_bytes.getvalue()



def latex_to_base64(latex_str, format="JPG"):
    img_bytes = latex_to_bytes(latex_str, format)
    return base64.b64encode(img_bytes).decode('utf-8')



def latex_to_io(latex_str, format="JPG"):
    image = latex_to_image_object(latex_str)
    img_io = io.BytesIO()
    image.save(img_io, format=format)
    img_io.seek(0)
    return img_io


def modify_numeric_values(latex_str, old_val, new_val):
    return latex_str.replace(old_val, new_val)