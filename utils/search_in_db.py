# utils/search_in_db.py

from database.getters_search import db_get_vector_list, db_search_keywords
from vectorization.vectorization_local import embed_text
from vectorization.class_embedding_queue import embedding_queue



async def get_similar_vectors(query: str, amount: int) -> list:
    # Pause current image embedding if any
    await embedding_queue.pause_current_task()

    print(f"In get_similar_vectors: {query}, {amount}")

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



async def get_page_by_keywords(keywords: list, amount: int) -> list[str]:
    pages = []
    for keyword in keywords:
        keyword = keyword.lower()
        pages.extend(await db_search_keywords(keyword, amount))

    # Deduplicate pages by page_id
    unique_pages = {page['page_id']: page for page in pages}

    # Calculate keyword match scores
    page_scores = {}
    for page_id, page in unique_pages.items():
        page_scores[page_id] = 0
        page_text = page['page_text'].lower()
        for keyword in keywords:
            if keyword.lower() in page_text:
                page_scores[page_id] += 1

    print(page_scores)

    # Sort by score descending
    sorted_pages = dict(sorted(page_scores.items(), key=lambda x: x[1], reverse=True))

    # Return only the n amount of pages
    sorted_pages = list(sorted_pages.items())[:amount]
    return [page_id for page_id, _ in sorted_pages]



async def combine_search_results(optimized_query: str, keywords: list, max_results: int = 6) -> list[str]:
    print(f"In combine_search_results: {optimized_query}, {keywords}, {max_results}")
    vector_image_ids = await get_similar_vectors(optimized_query, amount=5)
    keywords_image_ids = await get_page_by_keywords(keywords, amount=5)

    print(f"Vector image IDs: {vector_image_ids}")
    print(f"Keywords image IDs: {keywords_image_ids}")

    # Process image IDs
    seen_ids = set()
    best_image_ids = []

    for image_id in vector_image_ids + keywords_image_ids:
        image_id = str(image_id)
        if image_id not in seen_ids and len(best_image_ids) < max_results:
            best_image_ids.append(image_id)
            seen_ids.add(image_id)

    return best_image_ids