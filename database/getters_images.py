# database/getters_images.py

import aiosqlite

from config import LOCAL_DB_PATH




async def db_get_image_metadata(image_id: str):
    async with aiosqlite.connect(LOCAL_DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        query = """
            SELECT 
                pi.page_number,
                d.title,
                d.total_pages,
                d.document_id
            FROM page_images pi
            JOIN documents d ON pi.document_id = d.document_id
            WHERE pi.page_id = ?
        """
        async with conn.execute(query, (image_id,)) as cursor:
            return await cursor.fetchone()