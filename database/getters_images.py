# database/getters_images.py

import aiosqlite

from config import LOCAL_DB_PATH




async def db_get_image_latex(image_id: str):
    async with aiosqlite.connect(LOCAL_DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        query = """
            SELECT
                pi.latex_code
            FROM page_images pi
            WHERE pi.page_id = ?
        """
        async with conn.execute(query, (image_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None