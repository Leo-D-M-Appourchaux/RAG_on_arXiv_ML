# database/getters_search.py

import sqlite_vec, aiosqlite
import numpy as np

from config import LOCAL_DB_PATH



async def db_get_vector_list(query_vector: list[float], amount: int) -> list[dict]:
    async with aiosqlite.connect(LOCAL_DB_PATH) as conn:
        await conn._execute(conn._conn.enable_load_extension, True)
        await conn._execute(sqlite_vec.load, conn._conn)

        conn.row_factory = aiosqlite.Row
        # Enable sqlite-vec extension
        await conn.execute("SELECT vec_version();")
        
        # Convert query_vector to blob for sqlite-vec
        query_vector_blob = np.array(query_vector, dtype=np.float32).tobytes()
        
        query = """
            SELECT 
                piv.page_id,
                1 - vec_distance_cosine(piv.vector_data, ?) as similarity
            FROM page_images_vectors piv
            ORDER BY vec_distance_cosine(piv.vector_data, ?)
            LIMIT ?
        """
        params = (query_vector_blob, query_vector_blob, amount)
        
        try:
            async with conn.execute(query, params) as cursor:
                results = await cursor.fetchall()
                return [{'page_id': row['page_id'], 'similarity': row['similarity']} for row in results]
        except Exception as e:
            print(f"Database query failed: {e}")
            raise
        finally:
            await conn._execute(conn._conn.enable_load_extension, False)