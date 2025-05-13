# admin/create_db.py

import sqlite3, sqlite_vec, sys, os

# Add the parent directory to sys.path to enable imports from adjacent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import LOCAL_DB_PATH



conn = sqlite3.connect(LOCAL_DB_PATH)
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)

vec_version, = conn.execute("select vec_version()").fetchone()
print(f"vec_version={vec_version}")

cursor = conn.cursor()



# Create regular documents table
cursor.execute("""
CREATE TABLE documents (
    document_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_pages INTEGER NOT NULL,
    topic TEXT
)
""")

# Create virtual table for documents' vector data
cursor.execute("""
CREATE VIRTUAL TABLE documents_vectors USING vec0(
    document_id TEXT PRIMARY KEY,
    document_vector FLOAT[1536]
)
""")

# Create trigger to delete from documents_vectors when a document is deleted
cursor.execute("""
CREATE TRIGGER delete_documents_vector
AFTER DELETE ON documents
BEGIN
    DELETE FROM documents_vectors WHERE document_id = OLD(document_id);
END;
""")

# Create regular page_images table
cursor.execute("""
CREATE TABLE page_images (
    page_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    page_text TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
)
""")

# Create virtual table for page_images' vector data
cursor.execute("""
CREATE VIRTUAL TABLE page_images_vectors USING vec0(
    page_id TEXT PRIMARY KEY,
    vector_data FLOAT[1536]
)
""")

# Create trigger to delete from page_images_vectors when a page_image is deleted
cursor.execute("""
CREATE TRIGGER delete_page_images_vector
AFTER DELETE ON page_images
BEGIN
    DELETE FROM page_images_vectors WHERE page_id = OLD(page_id);
END;
""")

conn.commit()
conn.close()