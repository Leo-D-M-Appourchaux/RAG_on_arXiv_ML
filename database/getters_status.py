# database/getters_status.py

from typing import Optional, Dict, Any
import aiosqlite, sqlite_vec, time

from config import LOCAL_DB_PATH



def _calculate_estimated_time(embedding_queue, document_id, total_pages, processed_pages) -> str:
    """Calculate estimated completion time based on current processing rate"""
    if document_id not in embedding_queue.document_start_times:
        return "Unknown"
        
    if processed_pages == 0:
        return "Calculating..."
    
    start_time = embedding_queue.document_start_times[document_id]
    current_time = time.time()
    elapsed_time = current_time - start_time
    
    # Calculate pages per second
    pages_per_second = processed_pages / elapsed_time
    
    if pages_per_second <= 0:
        return "Unknown"
        
    # Calculate remaining time
    remaining_pages = total_pages - processed_pages
    remaining_seconds = remaining_pages / pages_per_second
    
    # Format remaining time
    if remaining_seconds < 60:
        return f"Less than a minute"
    elif remaining_seconds < 3600:
        minutes = int(remaining_seconds / 60)
        return f"About {minutes} minute{'s' if minutes > 1 else ''}"
    else:
        hours = int(remaining_seconds / 3600)
        return f"About {hours} hour{'s' if hours > 1 else ''}"



async def get_document_processing_status(embedding_queue, document_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed processing status for a specific document.

    Args:
        document_id (str): The unique identifier of the document.

    Returns:
        Optional[Dict[str, Any]]: A dictionary with processing status or None if not found.
    """
    # Check if document is actively being processed
    is_in_progress = (document_id in embedding_queue.document_total_pages)
    
    if not is_in_progress:
        # Check database for completed document
        async with aiosqlite.connect(LOCAL_DB_PATH) as conn:
            await conn._execute(conn._conn.enable_load_extension, True)
            await conn._execute(sqlite_vec.load, conn._conn)

            query = """
                SELECT 
                    d.total_pages,
                    (SELECT COUNT(*) FROM page_images_vectors piv 
                     WHERE piv.page_id IN (
                         SELECT pi.page_id FROM page_images pi 
                         WHERE pi.document_id = d.document_id
                     )) as processed_pages
                FROM documents d
                WHERE d.document_id = ?
            """
            async with conn.execute(query, (document_id,)) as cursor:
                record = await cursor.fetchone()
                if record:
                    total_pages, processed_pages = record
                    
                    # A document is considered complete if it has processed pages 
                    # and has been fully processed through the pipeline
                    is_complete = processed_pages > 0
                    
                    return {
                        "status": "completed" if is_complete else "not_found",
                        "total_pages": total_pages,
                        "processed_pages": processed_pages,
                        "progress_percentage": round((processed_pages / total_pages) * 100, 2)
                    }
            await conn._execute(conn._conn.enable_load_extension, False)
        return None

    # Document is currently being processed
    total_pages = embedding_queue.document_total_pages[document_id]
    processed_pages = embedding_queue.processed_pages_count.get(document_id, 0)
    
    # Calculate estimated time based on current processing rate
    estimated_time = _calculate_estimated_time(embedding_queue, document_id, total_pages, processed_pages)
    
    return {
        "status": "processing",
        "total_pages": total_pages,
        "processed_pages": processed_pages,
        "progress_percentage": round((processed_pages / total_pages) * 100, 2),
        "estimated_completion_time": estimated_time
    }