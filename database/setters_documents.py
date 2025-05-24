# database/setters_documents.py

from typing import Optional, List
from uuid import uuid4
import aiosqlite

from config import LOCAL_DB_PATH



async def _db_store_pdf_data(
    conn: aiosqlite.Connection,
    document_id: str,
    title: str,
    total_pages: int
) -> None:
    print(f"Inputs to store pdf data: {document_id}, {title}, {total_pages}")

    query = """
        INSERT INTO documents (
            document_id, title, total_pages
        ) VALUES (?, ?, ?)
    """
    await conn.execute(query, (
        document_id, title, total_pages
    ))



async def _db_store_image_with_vector(
    conn: aiosqlite.Connection,
    document_id: str,
    page_number: int,
    page_text: str,
    vector_data: Optional[List[float]] = None,
    page_id: Optional[str] = None,
    latex_code: Optional[str] = None
) -> str:
    print(f"Vector data: {vector_data}")

    if page_id is None:
        page_id = str(uuid4())

    query = """
        INSERT INTO page_images (
            page_id, document_id, page_number, page_text, latex_code
        ) VALUES (?, ?, ?, ?, ?)
    """
    await conn.execute(query, (page_id, document_id, page_number, page_text, latex_code))

    if vector_data:
        vector_query = """
            INSERT INTO page_images_vectors (page_id, vector_data)
            VALUES (?, ?)
        """
        await conn.execute(vector_query, (page_id, vector_data))

    return page_id



async def db_store_pdf_file(
    document_id: str,
    title: str,
    page_texts: List[str],
    vectors: Optional[List[List[float]]] = None,
    page_ids: Optional[List[str]] = None,
    latex_code: Optional[List[str]] = None,
) -> None:
    async with aiosqlite.connect(LOCAL_DB_PATH) as conn:
        await conn.execute("BEGIN")
        try:
            await _db_store_pdf_data(
                conn, document_id, title, len(page_texts)
            )
            print(f"Storing {len(page_texts)} images and vectors")
            print(f"Vectors: {vectors}")
            for i, page_text in enumerate(page_texts):
                page_vector = vectors[i] if vectors and i < len(vectors) else None
                page_id = page_ids[i] if page_ids and i < len(page_ids) else None
                await _db_store_image_with_vector(
                    conn, document_id, i, page_text, page_vector, page_id, latex_code
                )
            await conn.commit()
        except Exception as e:
            await conn.rollback()
            raise ValueError(f"Failed to store PDF file: {str(e)}")



# Should prob keep this private or admin only, can always redo the db if needed
async def _db_remove_pdf_data(document_id: str) -> None:
    async with aiosqlite.connect(LOCAL_DB_PATH) as conn:
        await conn.execute("BEGIN")
        try:
            await conn.execute("""
                DELETE FROM page_images_vectors
                WHERE page_id IN (
                    SELECT page_id FROM page_images WHERE document_id = ?
                )
            """, (document_id,))
            await conn.execute("""
                DELETE FROM page_images WHERE document_id = ?
            """, (document_id,))
            await conn.execute("""
                DELETE FROM documents WHERE document_id = ?
            """, (document_id,))
            await conn.commit()
        except Exception as e:
            await conn.rollback()
            raise ValueError(f"Failed to remove document and its associated data: {str(e)}")