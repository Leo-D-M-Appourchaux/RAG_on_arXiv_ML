# vectorization/class_embedding_queue.py

from typing import Dict, Any, List, Deque, Optional
from collections import deque
from datetime import datetime
import asyncio, json, time

from database.setters_vectors import store_page_vector
from vectorization.vectorization_local import embed_images



class EmbeddingQueue:
    def __init__(self):
        self.image_queue: Deque[Dict[str, Any]] = deque()
        self.current_task = None
        self.lock = asyncio.Lock()
        self.processing = False
        self.processed_pages_count: Dict[str, int] = {}  # Track number of processed pages per document
        self.document_total_pages: Dict[str, int] = {}
        self.failed_pages: Dict[str, List[int]] = {}
        self.document_start_times: Dict[str, float] = {}

        print(f"[{datetime.now()}] Initialized EmbeddingQueue instance")


    def start_background_tasks(self):
        """Start background tasks that require a running event loop"""
        asyncio.create_task(self._check_stalled_documents_periodically())
        print(f"[{datetime.now()}] Started background task for checking stalled documents")


    async def _check_stalled_documents_periodically(self):
        """Periodically check for and process stalled documents"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                await self._check_stalled_documents()
            except Exception as e:
                print(f"[{datetime.now()}] Error in stalled document checker: {str(e)}")


    def _start_stalled_checker(self):
        """Start a background task to periodically check for stalled documents"""
        asyncio.create_task(self._check_stalled_documents_periodically())


    async def _check_stalled_documents(self):
        """Check for documents that have stalled processing and compute their vectors"""
        current_time = time.time()
        documents_to_process = []
        
        print(f"[{datetime.now()}] Checking for stalled documents...")
        
        async with self.lock:
            for doc_id in list(self.processed_pages_count.keys()):
                # Skip documents that are already completed
                if doc_id not in self.document_total_pages:
                    continue
                    
                # Check if this document has been processing for more than 10 minutes
                if doc_id not in self.document_start_times:
                    self.document_start_times[doc_id] = current_time
                    continue
                    
                time_processing = current_time - self.document_start_times[doc_id]
                if time_processing < 600:  # Less than 10 minutes
                    continue
                
                # Calculate percentage processed
                processed_count = self.processed_pages_count[doc_id]
                total_expected = self.document_total_pages[doc_id]
                percent_processed = (processed_count / total_expected) * 100
                
                # Get count of pages still in queue for this document
                pages_in_queue = 0
                for task in self.image_queue:
                    if task['document_id'] == doc_id:
                        pages_in_queue += 1
                
                # If no tasks are pending and we have at least 70% of pages, 
                # or if more than 20 minutes have passed and we have at least 50% of pages
                stalled_timeout = (pages_in_queue == 0 and percent_processed >= 70) or \
                                (time_processing >= 1200 and percent_processed >= 50)
                                
                if stalled_timeout:
                    print(f"[{datetime.now()}] Document {doc_id} appears stalled:")
                    print(f"- Processing time: {time_processing:.1f} seconds")
                    print(f"- Processed {processed_count}/{total_expected} pages ({percent_processed:.1f}%)")
                    print(f"- Pages still in queue: {pages_in_queue}")
                    
                    # Document is considered complete if stalled conditions are met
                    self._mark_document_complete(doc_id, processed_count, total_expected)
        
        # Process any stalled documents (outside of lock)
        for doc_id in documents_to_process:
            print(f"[{datetime.now()}] Processing stalled document: {doc_id}")
            try:
                await self._process_document_vector(doc_id)
            except Exception as e:
                print(f"[{datetime.now()}] Error processing stalled document {doc_id}: {str(e)}")


    async def add_image_task(self, document_id: str, document_title: str, image_bytes: bytes, page_number: int, total_pages: int, page_id: Optional[str] = None):
        """Add a new image embedding task to the queue"""
        print(f"[{datetime.now()}] Adding new task - Document ID: {document_id}, Page: {page_number+1}/{total_pages}")

        if document_id not in self.processed_pages_count:
            self.processed_pages_count[document_id] = 0
            self.document_total_pages[document_id] = total_pages
            self.failed_pages[document_id] = []
            self.document_start_times[document_id] = time.time()
            print(f"[{datetime.now()}] Initialized new document tracking - ID: {document_id}, Total Pages: {total_pages}")

        task = {
            'document_id': document_id,
            'document_title': document_title,
            'image_bytes': image_bytes,
            'page_number': page_number,
            'page_id': page_id,
            'timestamp': time.time(),
            'retry_count': 0
        }
        self.image_queue.append(task)

        queue_stats = {
            'queue_size': len(self.image_queue),
            'documents_in_progress': len(self.processed_pages_count),
            'current_document': document_id,
            'page_number': page_number
        }
        print(f"[{datetime.now()}] Task added to queue. Queue stats: {json.dumps(queue_stats)}")

        if not self.processing:
            print(f"[{datetime.now()}] Queue processor not running. Starting new processing task.")
            asyncio.create_task(self.process_queue())


    async def process_queue(self):
        """Process all tasks in the queue with improved error handling and retries"""
        if self.processing:
            print(f"[{datetime.now()}] Queue processor already running")
            return

        self.processing = True
        print(f"[{datetime.now()}] Starting queue processor")

        failed_tasks = []  # Track failed tasks for retry

        while self.image_queue:
            async with self.lock:
                task = self.image_queue.popleft()
                self.current_task = task

            document_id = task['document_id']
            page_number = task['page_number']
            page_id = task.get('page_id')
            wait_time = time.time() - task['timestamp']

            print(f"""[{datetime.now()}] Starting task processing:
                - Document ID: {document_id}
                - Page: {page_number}
                - Queue size: {len(self.image_queue)}
                - Wait time: {wait_time:.2f} seconds""")

            try:
                processing_start = time.time()
                files = {
                    'files': ('image.png', task['image_bytes'], 'image/png')
                }

                try:
                    print(f"[{datetime.now()}] Calling embed_image API for document {document_id}, page {page_number}")
                    vector = await embed_images(files)  # This has built-in retry logic
                    
                    # Store vector in database
                    await store_page_vector(document_id, page_number, vector, page_id)
                    
                    # Update processed page count
                    self.processed_pages_count[document_id] = self.processed_pages_count.get(document_id, 0) + 1
                    
                    # Check if document is complete
                    await self._check_document_completion(document_id)
                    
                    processing_time = time.time() - processing_start

                    print(f"""[{datetime.now()}] Task completed successfully:
                        - Document ID: {document_id}
                        - Page: {page_number}
                        - Processing time: {processing_time:.2f} seconds
                        - Vector size: {len(vector)}""")

                except Exception as e:
                    print(f"[{datetime.now()}] Error embedding image for document {document_id}, page {page_number}: {str(e)}")
                    
                    # Track this failed page
                    if document_id in self.failed_pages:
                        self.failed_pages[document_id].append(page_number)
                    
                    # Add to failed tasks queue for later retry if under retry limit
                    retry_count = task.get('retry_count', 0) + 1
                    if retry_count <= 3:  # Limit retries to 3 attempts
                        task['retry_count'] = retry_count
                        task['last_error'] = str(e)
                        task['last_attempt'] = time.time()
                        failed_tasks.append(task)
                        print(f"[{datetime.now()}] Added to retry queue (attempt {retry_count}/3)")
                    else:
                        print(f"[{datetime.now()}] Max retries exceeded for document {document_id}, page {page_number}")
                        # Check if we should compute document vector despite this failure
                        await self._check_document_completion(document_id)

            except Exception as e:
                print(f"[{datetime.now()}] Error processing task for document {document_id}, page {page_number}: {str(e)}")
            finally:
                self.current_task = None

        # Process failed tasks if any
        if failed_tasks:
            print(f"[{datetime.now()}] Processing {len(failed_tasks)} failed tasks after a delay")
            # Wait a bit before retrying
            await asyncio.sleep(10)
            # Add failed tasks back to the queue
            async with self.lock:
                for task in failed_tasks:
                    self.image_queue.append(task)
            # Process the queue again
            return await self.process_queue()
            
        self.processing = False
        print(f"[{datetime.now()}] Queue processor finished - no more tasks in queue")


    async def _check_document_completion(self, document_id: str):
        """Check if a document's page processing is complete"""
        if document_id not in self.processed_pages_count or document_id not in self.document_total_pages:
            return
            
        total_pages = self.document_total_pages[document_id]
        processed_pages = self.processed_pages_count[document_id]
        
        # Calculate what percentage of pages are done
        percent_complete = (processed_pages / total_pages) * 100
        
        # Count pages still in queue for this document
        pages_in_queue = 0
        for task in self.image_queue:
            if task['document_id'] == document_id:
                pages_in_queue += 1
        
        # Document is considered complete if either:
        # 1. All pages processed successfully (100%)
        # 2. No more pages in queue AND at least 70% processed
        # 3. At least 95% processed (regardless of queue)
        is_complete = (
            (processed_pages == total_pages) or
            (pages_in_queue == 0 and percent_complete >= 70) or
            (percent_complete >= 95)
        )
        
        if is_complete:
            print(f"[{datetime.now()}] Document processing complete: {document_id} with {processed_pages}/{total_pages} pages ({percent_complete:.1f}%)")
            self._mark_document_complete(document_id, processed_pages, total_pages)


    def _mark_document_complete(self, document_id: str, processed_pages: int, total_pages: int):
        """Mark a document as complete and clean up tracking data"""
        print(f"[{datetime.now()}] Marking document as complete: {document_id}")
        print(f"[{datetime.now()}] - Processed pages: {processed_pages}/{total_pages}")
        
        # Clean up tracking data
        if document_id in self.processed_pages_count:
            del self.processed_pages_count[document_id]
        if document_id in self.document_total_pages:
            del self.document_total_pages[document_id]
        if document_id in self.failed_pages:
            del self.failed_pages[document_id]
        if document_id in self.document_start_times:
            del self.document_start_times[document_id]


    async def pause_current_task(self):
        """Pause the current task and return it to the queue"""
        async with self.lock:
            if self.current_task:
                print(f"[{datetime.now()}] Pausing current task and returning to queue")
                self.image_queue.appendleft(self.current_task)
                self.current_task = None
            self.processing = False
            print(f"[{datetime.now()}] Queue processing paused")


    async def resume_processing(self):
        """Resume queue processing if paused"""
        async with self.lock:
            if not self.processing and self.image_queue:
                print(f"[{datetime.now()}] Resuming queue processing")
                self.processing = True
                try:
                    await self.process_queue()
                except Exception as e:
                    print(f"[{datetime.now()}] Error during queue processing: {str(e)}")
                    self.processing = False



print(f"[{datetime.now()}] Initializing global embedding queue")
embedding_queue = EmbeddingQueue()