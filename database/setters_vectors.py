# database/setters_vectors.py

import aiosqlite, struct, sqlite_vec
from datetime import datetime
from typing import Optional

from config import LOCAL_DB_PATH



async def store_page_vector(document_id: str, page_number: int, vector: list, page_id: Optional[str] = None) -> None:
    """Store page vector in database with page_id if provided"""
    print(f"[{datetime.now()}] Storing page vector in database - Document: {document_id}, Page: {page_number}")
    print(f"SAMPLE VECTOR: {vector[:1]}")  # Log first element for verification

    # Ensure vector length matches the expected dimension (1536)
    if len(vector) != 1536:
        raise ValueError(f"Vector length {len(vector)} does not match expected dimension 1536")

    # Convert vector to binary blob
    vector_blob = struct.pack(f'<{len(vector)}f', *vector)

    async with aiosqlite.connect(LOCAL_DB_PATH) as conn:
        await conn._execute(conn._conn.enable_load_extension, True)
        await conn._execute(sqlite_vec.load, conn._conn)

        if page_id:
            # Use page_id if provided
            query = """
                INSERT OR REPLACE INTO page_images_vectors (page_id, vector_data) VALUES (?, ?)
            """
            try:
                await conn.execute(query, (page_id, vector_blob))
                await conn.commit()
                print(f"[{datetime.now()}] Successfully stored page vector - Document: {document_id}, Page: {page_number}, Page ID: {page_id}")
            except Exception as e:
                print(f"[{datetime.now()}] Database error while storing page vector: {str(e)}")
                raise
            finally:
                await conn._execute(conn._conn.enable_load_extension, False)
        else:
            # Fall back to document_id and page_number
            select_query = """
                SELECT page_id FROM page_images 
                WHERE document_id = ? AND page_number = ?
            """
            async with conn.execute(select_query, (document_id, page_number)) as cursor:
                row = await cursor.fetchone()
                if row:
                    page_id = row[0]
                    query = """
                        INSERT OR REPLACE INTO page_images_vectors (page_id, vector_data) VALUES (?, ?)
                    """
                    try:
                        await conn.execute(query, (page_id, vector_blob))
                        await conn.commit()
                        print(f"[{datetime.now()}] Successfully stored page vector - Document: {document_id}, Page: {page_number}")
                    except Exception as e:
                        print(f"[{datetime.now()}] Database error while storing page vector: {str(e)}")
                        raise
                    finally:
                        await conn._execute(conn._conn.enable_load_extension, False)
                else:
                    print(f"[{datetime.now()}] ERROR: Page not found for Document: {document_id}, Page: {page_number}")
                    await conn._execute(conn._conn.enable_load_extension, False)
                    raise ValueError("Page not found")