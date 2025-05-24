# admin/fill_db.py

import sqlite_vec, traceback, aiosqlite, asyncio, struct, fitz, time, sys, io, os
from typing import List, Tuple, Dict, Any, Set
from uuid import uuid4, UUID
from PIL import Image

# Add the parent directory to sys.path to enable imports from adjacent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PROCESSED_FOLDER, LOCAL_DB_PATH, EXTRACTION_FOLDER
from database.getters_status import get_document_processing_status
from vectorization.class_embedding_queue import embedding_queue
from database.setters_documents import db_store_pdf_file



# Global tracking of documents being processed
documents_in_process: Dict[str, Dict[str, Any]] = {}
# Set to track documents that have been completed
completed_documents: Set[str] = set()



async def process_page(page, zoom: float = 1.5) -> Tuple[bytes, str]:
    """Process a single page to extract image and text"""
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("jpeg")
    text = page.get_text()
    return img_bytes, text



async def pdf_to_images_and_text(pdf_path: str) -> Tuple[List[bytes], List[str]]:
    """Convert PDF to list of images and text with better error handling"""
    doc = fitz.open(pdf_path)
    try:
        # Process pages in chunks to avoid memory issues
        chunk_size = 4
        pages = [page for page in doc]
        results = []
        
        for i in range(0, len(pages), chunk_size):
            chunk = pages[i:i + chunk_size]
            try:
                chunk_results = await asyncio.gather(
                    *(process_page(page) for page in chunk),
                    return_exceptions=True
                )
                
                # Handle any exceptions in processing
                valid_results = []
                for j, result in enumerate(chunk_results):
                    if isinstance(result, Exception):
                        print(f"Error processing page {i+j}: {str(result)}")
                        # Add empty placeholder
                        valid_results.append((b'', ''))
                    else:
                        valid_results.append(result)
                        
                results.extend(valid_results)
            except Exception as e:
                print(f"Error processing chunk {i//chunk_size}: {str(e)}")
                # Add empty placeholders for the whole chunk
                results.extend([(b'', '') for _ in range(len(chunk))])
            
        images_bytes, texts = zip(*results) if results else ([], [])
        return list(images_bytes), list(texts)
    finally:
        doc.close()



async def image_to_image_and_text(image_path: str) -> Tuple[List[bytes], List[str]]:
    """Convert an image file to a list with one image and empty text for DB compatibility"""
    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # Validate that this is actually an image
        try:
            img = Image.open(io.BytesIO(image_bytes))
            # Convert to JPEG format for consistency with PDF processing
            if img.format != 'JPEG':
                byte_array = io.BytesIO()
                # Convert to RGB if needed (for PNG with transparency, etc.)
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img if img.mode == 'RGBA' else None)
                    img = background
                img.save(byte_array, format='JPEG', optimize=True)
                image_bytes = byte_array.getvalue()
            img.close()
        except Exception as e:
            print(f"Error validating image: {str(e)}")
            raise ValueError(f"Invalid image file: {image_path}")
            
        # Return as a list to be compatible with PDF processing
        return [image_bytes], [""]  # Empty text as placeholder
    except Exception as e:
        print(f"Error processing image file {image_path}: {str(e)}")
        traceback.print_exc()
        raise



def create_thumbnail(image_data: bytes, size=(400, 400)) -> bytes:
    """Create thumbnail from image bytes with error handling"""
    try:
        image = Image.open(io.BytesIO(image_data))
        image.thumbnail(size)
        byte_array = io.BytesIO()
        image.save(byte_array, format='JPEG', optimize=True)
        return byte_array.getvalue()
    except Exception as e:
        print(f"Error creating thumbnail: {str(e)}")
        # Return a minimal valid JPEG as fallback
        return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xdb\x00C\x01\t\t\t\x0c\x0b\x0c\x18\r\r\x182!\x1c!22222222222222222222222222222222222222222222222222\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13"2\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xfe\xfe(\xa2\x8a\x00\xff\xd9'



async def save_to_local(file_content: bytes, filename: str):
    """
    Save the file content to a local directory.

    Args:
        file_content (bytes): The content of the file to save.
        filename (str): The filename to use for saving, including extension (e.g., '123.pdf' or '456_full.jpg').
    """
    # Ensure the storage directory exists
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)
    
    # Construct the full file path
    file_path = os.path.join(PROCESSED_FOLDER, filename)
    
    # Use a helper function via run_in_executor to avoid blocking
    def write_file():
        with open(file_path, 'wb') as f:
            f.write(file_content)
    
    # Run the synchronous file operation in a thread pool
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, write_file)
    
    print(f"File saved locally: {file_path}")



def check_and_resize_for_vect(image_bytes: bytes, max_pixels: int = 1000000) -> bytes:
    """Resize image if needed for vector embedding with error handling"""
    try:
        if not image_bytes:
            print("Warning: Empty image bytes provided")
            return image_bytes
            
        image = Image.open(io.BytesIO(image_bytes))
        current_pixels = image.width * image.height
        
        if current_pixels > max_pixels:
            scale_factor = (max_pixels / current_pixels) ** 0.5
            new_width = int(image.width * scale_factor)
            new_height = int(image.height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', optimize=True)
            return buffer.getvalue()
        
        return image_bytes
    except Exception as e:
        print(f"Error resizing image: {str(e)}")
        return image_bytes  # Return original bytes on error



async def verify_vector_in_database(page_id: UUID) -> bool:
    async with aiosqlite.connect(LOCAL_DB_PATH) as conn:
        await conn._execute(conn._conn.enable_load_extension, True)
        await conn._execute(sqlite_vec.load, conn._conn)

        conn.row_factory = aiosqlite.Row
        query = """
            SELECT EXISTS(
                SELECT 1
                FROM page_images_vectors
                WHERE page_id = ?
            ) as has_vector
        """
        async with conn.execute(query, (str(page_id),)) as cursor:
            result = await cursor.fetchone()
            await conn._execute(conn._conn.enable_load_extension, False)
            return result['has_vector'] == 1



async def retry_missing_page_vectors(document_id: UUID, page_ids: List[UUID], images: List[bytes], max_retries: int = 3) -> int:
    """Retry storing vectors for pages that are missing them"""
    retry_count = 0
    fixed_pages = 0
    
    while retry_count < max_retries:
        missing_vectors = []
        
        # Check which pages are missing vectors
        for idx, page_id in enumerate(page_ids):
            if not await verify_vector_in_database(page_id):
                if idx < len(images) and images[idx]:  # Make sure we have image data
                    missing_vectors.append((idx, page_id))
        
        if not missing_vectors:
            print(f"All vectors present for document {document_id} after retries")
            return fixed_pages
            
        print(f"Found {len(missing_vectors)} pages with missing vectors for document {document_id}, retry {retry_count + 1}/{max_retries}")
        
        # Retry each missing vector
        for idx, page_id in missing_vectors:
            try:
                # Resize image for vector embedding
                resized_image = check_and_resize_for_vect(images[idx])
                
                # Queue image for embedding with higher priority
                await embedding_queue.add_image_task(
                    str(document_id),
                    "Retry", # Title doesn't matter for retries
                    resized_image,
                    idx,
                    len(page_ids),
                    str(page_id),
                    priority=True  # Mark as high priority retry
                )
                
                print(f"Requeued page {idx} (ID: {page_id}) for document {document_id}")
                fixed_pages += 1
            except Exception as e:
                print(f"Error requeuing page {idx} for document {document_id}: {str(e)}")
        
        # Wait before checking again
        retry_delay = 60 * (retry_count + 1)  # Increase wait time with each retry
        print(f"Waiting {retry_delay} seconds before checking vectors again...")
        await asyncio.sleep(retry_delay)
        retry_count += 1
    
    return fixed_pages



async def verify_document_vector(document_id: UUID) -> bool:
    async with aiosqlite.connect(LOCAL_DB_PATH) as conn:
        await conn._execute(conn._conn.enable_load_extension, True)
        await conn._execute(sqlite_vec.load, conn._conn)

        conn.row_factory = aiosqlite.Row
        query = """
            SELECT 
                (SELECT COUNT(*) FROM page_images WHERE document_id = ?) as total_pages,
                (SELECT COUNT(*) FROM page_images_vectors piv 
                 JOIN page_images pi ON pi.page_id = piv.page_id 
                 WHERE pi.document_id = ?) as pages_with_vectors
        """
        async with conn.execute(query, (str(document_id), str(document_id))) as cursor:
            result = await cursor.fetchone()
            await conn._execute(conn._conn.enable_load_extension, False)
            
            if not result or result['total_pages'] == 0:
                return False
                
            # Document is considered complete if at least 90% of pages have vectors
            return (result['pages_with_vectors'] / result['total_pages']) >= 0.9


async def compute_and_store_document_vector(document_id: UUID) -> bool:
    async with aiosqlite.connect(LOCAL_DB_PATH) as conn:
        await conn._execute(conn._conn.enable_load_extension, True)
        await conn._execute(sqlite_vec.load, conn._conn)

        conn.row_factory = aiosqlite.Row
        
        # Check if page vectors exist
        vector_query = """
            SELECT COUNT(*) as vector_count
            FROM page_images_vectors piv
            JOIN page_images pi ON piv.page_id = pi.page_id
            WHERE pi.document_id = ?
        """
        async with conn.execute(vector_query, (str(document_id),)) as cursor:
            result = await cursor.fetchone()
        
        if not result or result['vector_count'] == 0:
            print(f"No page vectors found for document {document_id}")
            await conn._execute(conn._conn.enable_load_extension, False)
            return False
        
        # Count total pages
        pages_query = """
            SELECT COUNT(*) as page_count
            FROM page_images
            WHERE document_id = ?
        """
        async with conn.execute(pages_query, (str(document_id),)) as cursor:
            pages_result = await cursor.fetchone()
            
        total_pages = pages_result['page_count'] if pages_result else 0
        vectorized_pages = result['vector_count']
        
        # Document is considered successfully processed if at least 90% of pages have vectors
        success = total_pages > 0 and (vectorized_pages / total_pages) >= 0.9
        
        if success:
            print(f"Document {document_id} successfully processed: {vectorized_pages}/{total_pages} pages vectorized")
            # Mark document as completed in memory
            completed_documents.add(str(document_id))
        else:
            print(f"Document {document_id} not fully processed: {vectorized_pages}/{total_pages} pages vectorized")
            
        await conn._execute(conn._conn.enable_load_extension, False)
        return success



async def monitor_document_progress(document_id: UUID, filename: str, images: List[bytes], page_ids: List[UUID], total_timeout: int = 3600):
    """Monitor progress of document processing with timeout and verify vectors exist"""
    doc_str = str(document_id)
    start_time = time.time()
    last_check_time = start_time
    last_processed = 0
    
    print(f"Starting monitoring for document {doc_str} ({filename})")
    
    while True:
        try:
            # Get document status
            status = await get_document_processing_status(embedding_queue, doc_str)
            
            current_time = time.time()
            elapsed = current_time - start_time
            
            # If document is not found in queue or database
            if not status:
                if elapsed > 300:  # After 5 minutes, if not found, we have a problem
                    print(f"Document {doc_str} not found in queue or database after 5 minutes. Possible error.")
                    return False
                await asyncio.sleep(30)
                continue
                
            # If document is completed according to queue
            if status.get("status") == "completed":
                # Verify document vector exists
                if not await verify_document_vector(document_id):
                    print(f"Document {doc_str} marked as completed but missing document vector. Computing now.")
                    if await compute_and_store_document_vector(document_id):
                        print(f"Successfully created document vector for {doc_str}")
                    else:
                        print(f"Failed to create document vector for {doc_str}")
                        # Try to fix missing page vectors first
                        fixed_pages = await retry_missing_page_vectors(document_id, page_ids, images)
                        if fixed_pages > 0:
                            # Wait for vectors to be processed
                            await asyncio.sleep(60)
                            # Try computing document vector again
                            if await compute_and_store_document_vector(document_id):
                                print(f"Successfully created document vector for {doc_str} after fixing page vectors")
                            else:
                                print(f"Still failed to create document vector for {doc_str}")
                                return False
                
                print(f"Document {doc_str} ({filename}) processing completed successfully.")
                completed_documents.add(doc_str)
                return True
                
            # Check progress
            total_pages = status.get("total_pages", 0)
            processed = status.get("processed_pages", 0)
            failed = status.get("failed_pages", 0)
            progress = status.get("progress_percentage", 0)
            
            # Calculate processing rate
            time_since_last = current_time - last_check_time
            if time_since_last >= 60:  # Update every minute
                pages_per_minute = (processed - last_processed) / (time_since_last / 60) if time_since_last > 0 else 0
                last_check_time = current_time
                last_processed = processed
                
                # Calculate estimated time remaining
                pages_remaining = total_pages - processed
                estimated_minutes = pages_remaining / max(0.1, pages_per_minute) if pages_per_minute > 0 else float('inf')
                
                print(f"""Document {doc_str} ({filename}) progress:
                    - Elapsed time: {elapsed:.0f} seconds
                    - Pages: {processed}/{total_pages} ({progress:.1f}%)
                    - Failed pages: {failed}
                    - Processing rate: {pages_per_minute:.1f} pages/minute
                    - Estimated remaining: {estimated_minutes:.1f} minutes""")
                
                # If no progress for 5 minutes and we have processed pages, retry missing vectors
                if pages_per_minute < 0.1 and processed > 0 and elapsed > 300:
                    print(f"Document {doc_str} processing appears stalled. Retrying missing vectors.")
                    fixed_pages = await retry_missing_page_vectors(document_id, page_ids, images)
                    if fixed_pages > 0:
                        print(f"Requeued {fixed_pages} pages for vector processing")
            
            # Check for timeout
            if elapsed > total_timeout:
                print(f"Document {doc_str} processing timed out after {total_timeout} seconds.")
                # Force document vector calculation if we have enough pages
                if processed / total_pages >= 0.7:  # If at least 70% complete, calculate vector
                    print(f"Document {doc_str} has {processed}/{total_pages} pages processed. Forcing vector calculation.")
                    
                    # Try to fix missing page vectors first
                    fixed_pages = await retry_missing_page_vectors(document_id, page_ids, images)
                    
                    # Wait a bit for vectors to be processed
                    if fixed_pages > 0:
                        print(f"Waiting for {fixed_pages} requeued vectors to be processed...")
                        await asyncio.sleep(60)
                    
                    # Calculate document vector
                    if await compute_and_store_document_vector(document_id):
                        print(f"Successfully created document vector for timed out document {doc_str}")
                        completed_documents.add(doc_str)
                        return True
                    else:
                        print(f"Failed to create document vector for timed out document {doc_str}")
                        return False
                return False
                
            # Sleep before next check
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"Error monitoring document {doc_str}: {str(e)}")
            traceback.print_exc()
            await asyncio.sleep(30)



async def process_single_pdf(pdf_path: str, timeout: int = 3600):
    """Process a single PDF file with consistent IDs across folder and DB"""
    try:
        # Generate document ID - will be used consistently in both folder and DB
        document_id = uuid4()
        filename = os.path.basename(pdf_path)
        print(f"Processing {pdf_path}")
        
        # Track start time
        start_time = time.time()
        documents_in_process[str(document_id)] = {
            "filename": filename,
            "start_time": start_time,
            "status": "extracting"
        }

        # Extract images and text from PDF
        images, text_pages = await pdf_to_images_and_text(pdf_path)
        total_pages = len(images)

        print(f"Extracted {total_pages} images and text from {filename}")
        
        documents_in_process[str(document_id)]["status"] = "metadata"
        documents_in_process[str(document_id)]["total_pages"] = total_pages

        # Store PDF to folder with document_id
        documents_in_process[str(document_id)]["status"] = "storing"
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        await save_to_local(pdf_content, f"{document_id}.pdf")

        # Generate page_ids before processing to ensure consistency between folder and DB
        page_ids = [str(uuid4()) for _ in range(total_pages)]
        
        # Store in database with page_ids first to ensure DB entries exist
        documents_in_process[str(document_id)]["status"] = "database_init"
        await db_store_pdf_file(
            document_id=str(document_id),
            title=filename,
            page_texts=text_pages,
            page_ids=page_ids
        )
        
        # Track successfully processed pages
        processed_pages = []
        
        # Process and store images to folder
        documents_in_process[str(document_id)]["status"] = "image_processing"
        for page_idx, (image_data, page_id) in enumerate(zip(images, page_ids)):
            # Skip empty images (from extraction errors)
            if not image_data:
                print(f"Warning: Empty image data for page {page_idx}. Skipping folder storing.")
                continue
                
            try:
                # Use consistent page_id for both folder and database
                # store full resolution image
                await save_to_local(image_data, f"{page_id}_full.jpg")

                # Create and store thumbnail
                thumb_data = create_thumbnail(image_data)
                await save_to_local(thumb_data, f"{page_id}_thumb.jpg")

                # Queue image for embedding with the specific page_id
                resized_image = check_and_resize_for_vect(image_data)
                await embedding_queue.add_image_task(
                    str(document_id),
                    filename,
                    resized_image,
                    page_idx,
                    total_pages,
                    str(page_id)  # Pass page_id to ensure consistency
                )
                
                processed_pages.append(page_idx)
            except Exception as e:
                print(f"Error processing page {page_idx} for {filename}: {str(e)}")
                traceback.print_exc()
                # Continue with other pages despite error

        documents_in_process[str(document_id)]["status"] = "monitoring"
        # Launch background task to monitor progress (don't await it)
        monitor_task = asyncio.create_task(
            monitor_document_progress(document_id, filename, images, page_ids, timeout)
        )
        documents_in_process[str(document_id)]["monitor_task"] = monitor_task

        print(f"Successfully queued {filename} for processing")
        return document_id, monitor_task

    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        traceback.print_exc()
        return None, None



async def process_single_image(image_path: str, timeout: int = 3600):
    """Process a single image file as a one-page document"""
    try:
        # Generate document ID - will be used consistently in both folder and DB
        document_id = uuid4()
        filename = os.path.basename(image_path)
        print(f"Processing image {image_path}")

        latex_path = image_path.replace(".jpg", ".txt")
        print(f"Looking for LaTeX file: {latex_path}")

        # Track start time
        start_time = time.time()
        documents_in_process[str(document_id)] = {
            "filename": filename,
            "start_time": start_time,
            "status": "extracting"
        }

        try:
            with open(latex_path, 'r', encoding='utf-8') as f:
                latex_code = f.read()
        except Exception as e:
            print(f"Error reading LaTeX file {latex_path}: {str(e)}")

        # Extract image bytes
        images, text_pages = await image_to_image_and_text(image_path)
        total_pages = 1  # Single page for images

        print(f"Extracted image as a single-page document: {filename}")
        documents_in_process[str(document_id)]["status"] = "metadata"
        documents_in_process[str(document_id)]["total_pages"] = total_pages

        documents_in_process[str(document_id)]["metadata"] = {
            "title": filename,
        }

        # Store original image to folder with document_id
        documents_in_process[str(document_id)]["status"] = "storing"
        
        # Determine the file extension from the original file
        file_ext = os.path.splitext(filename)[1].lower()
        await save_to_local(images[0], f"{document_id}{file_ext}")

        # Generate page_id for consistency between folder and DB
        page_ids = [str(uuid4())]
        
        # Store in database with page_id first to ensure DB entry exists
        documents_in_process[str(document_id)]["status"] = "database_init"
        await db_store_pdf_file(
            document_id=str(document_id),
            title=filename,
            page_texts=text_pages,
            page_ids=page_ids,
            latex_code=latex_code
        )
        
        # Process and store images to folder
        documents_in_process[str(document_id)]["status"] = "image_processing"
        
        try:
            # Use consistent page_id for both folder and database
            # store full resolution image
            await save_to_local(images[0], f"{page_ids[0]}_full.jpg")

            # Create and store thumbnail
            thumb_data = create_thumbnail(images[0])
            await save_to_local(thumb_data, f"{page_ids[0]}_thumb.jpg")

            # Queue image for embedding with the specific page_id
            resized_image = check_and_resize_for_vect(images[0])
            await embedding_queue.add_image_task(
                str(document_id),
                filename,
                resized_image,
                0,  # page_idx
                total_pages,
                str(page_ids[0])  # Pass page_id to ensure consistency
            )
            
        except Exception as e:
            print(f"Error processing image {filename}: {str(e)}")
            traceback.print_exc()

        documents_in_process[str(document_id)]["status"] = "monitoring"
        # Launch background task to monitor progress (don't await it)
        monitor_task = asyncio.create_task(
            monitor_document_progress(document_id, filename, images, page_ids, timeout)
        )
        documents_in_process[str(document_id)]["monitor_task"] = monitor_task

        print(f"Successfully queued image {filename} for processing")
        return document_id, monitor_task

    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        traceback.print_exc()
        return None, None



async def process_pdf_folder(folder_path: str, concurrent_limit: int = 2, timeout: int = 3600):
    """Process PDFs from subfolders, using subfolder names with concurrency control"""
    successful = 0
    failed = 0
    pending_tasks = []
    
    # Create a semaphore to limit concurrent processing
    semaphore = asyncio.Semaphore(concurrent_limit)
    
    async def process_with_semaphore(file_path):
        async with semaphore:
            # Check file extension to determine processing method
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.pdf':
                return await process_single_pdf(file_path, timeout)
            elif file_ext in ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'):
                return await process_single_image(file_path, timeout)
            else:
                print(f"Unsupported file type: {file_ext}")
                return None, None
    
    # Walk through all subfolders
    for root, dirs, files in os.walk(folder_path):
        # Find PDF, image, and text files
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'))]
        total_files = len(pdf_files) + len(image_files)
        
        if not total_files:
            print(f"No PDF or image files found in folder: {os.path.basename(root)}")
            continue
        
        print(f"\nProcessing {len(pdf_files)} PDF files, {len(image_files)} image files from folder: {os.path.basename(root)}")
        
        # Launch tasks for all PDFs in this folder
        for pdf_file in pdf_files:
            file_path = os.path.join(root, pdf_file)
            print(f"\nQueuing PDF: {pdf_file}")
            
            # Create and start the task
            task = asyncio.create_task(process_with_semaphore(file_path))
            pending_tasks.append((pdf_file, task))
        
        # Launch tasks for all image files in this folder
        for image_file in image_files:
            file_path = os.path.join(root, image_file)
            print(f"\nQueuing image: {image_file}")
            
            # Create and start the task
            task = asyncio.create_task(process_with_semaphore(file_path))
            pending_tasks.append((image_file, task))
    
    # Wait for all tasks to complete
    for file_name, task in pending_tasks:
        try:
            doc_id, monitor_task = await task
            
            if doc_id:
                print(f"Successfully queued {file_name}")
                # Wait for monitoring to complete
                if monitor_task:
                    result = await monitor_task
                    if result:
                        successful += 1
                        print(f"Successfully processed {file_name}")
                    else:
                        # Even if monitoring failed, the document might have been processed
                        if str(doc_id) in completed_documents:
                            successful += 1
                            print(f"Document {file_name} was eventually processed successfully")
                        else:
                            failed += 1
                            print(f"Failed to fully process {file_name}")
                else:
                    # No monitoring task means something failed early
                    failed += 1
            else:
                failed += 1
                print(f"Failed to process {file_name}")
                
        except Exception as e:
            failed += 1
            print(f"Error processing {file_name}: {e}")
            traceback.print_exc()
    
    # Summary
    print(f"\nProcessing complete:")
    print(f"Successfully processed: {successful}")
    print(f"Failed: {failed}")
    return successful, failed



async def main():
    """Main async function to run the whole process"""
    # Folder containing PDFs and images
    DOCS_FOLDER = EXTRACTION_FOLDER
    
    # Make sure the embedding queue background tasks are started
    # This will work because we're already inside an event loop (asyncio.run creates one)
    embedding_queue.start_background_tasks()
    
    # Run the processor
    success, failed = await process_pdf_folder(DOCS_FOLDER, concurrent_limit=2, timeout=3600)
    
    return success, failed



if __name__ == "__main__":
    # Run everything in a single asyncio.run() call
    asyncio.run(main())