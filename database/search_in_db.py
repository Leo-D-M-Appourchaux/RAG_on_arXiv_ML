# utils/search_in_db.py

from database.getters_search import db_get_vector_list
from vectorization.vectorization_local import embed_text
from vectorization.class_embedding_queue import embedding_queue



async def get_similar_vectors(query: str, amount: int) -> list:
    # Pause current image embedding if any
    await embedding_queue.pause_current_task()

    try:
        payload = {"texts": [query]}    
        text_vector = await embed_text(payload)

        image_vectors = await db_get_vector_list(text_vector, amount)
        return [img_vec['page_id'] for img_vec in image_vectors]

    except Exception as e:
        print(f"Error in vector processing: {str(e)}")
        raise

    finally:
        await embedding_queue.resume_processing()



async def combine_search_results(optimized_query: str, max_results: int = 3) -> list[str]:
    vector_image_ids = await get_similar_vectors(optimized_query, amount=max_results)

    print(f"Vector image IDs retrieved by the system: {vector_image_ids}\n")

    # Process image IDs
    seen_ids = set()
    best_image_ids = []

    for image_id in vector_image_ids:
        image_id = str(image_id)
        if image_id not in seen_ids and len(best_image_ids) < max_results:
            best_image_ids.append(image_id)
            seen_ids.add(image_id)

    return best_image_ids