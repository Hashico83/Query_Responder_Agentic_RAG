import os
import re # --- FIX: Import the regular expression module ---
import hashlib
import sqlite3
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import chromadb
from langchain_core.documents import Document # Import Document class
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
    TextLoader,
    CSVLoader,
    UnstructuredImageLoader
)
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from tqdm import tqdm

import config

LOADER_MAPPING = {
    "PyPDFLoader": PyPDFLoader,
    "UnstructuredWordDocumentLoader": UnstructuredWordDocumentLoader,
    "UnstructuredExcelLoader": UnstructuredExcelLoader,
    "UnstructuredPowerPointLoader": UnstructuredPowerPointLoader,
    "TextLoader": TextLoader,
    "CSVLoader": CSVLoader,
    "UnstructuredImageLoader": UnstructuredImageLoader,
}


def init_db() -> sqlite3.Connection:
    """Initialize the SQLite database for tracking processed documents."""
    conn = sqlite3.connect(config.PROCESSED_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_files (
            filepath TEXT PRIMARY KEY,
            last_modified REAL,
            content_hash TEXT,
            processed_at REAL
        )
    """)

    conn.commit()
    return conn


def get_file_hash(filepath: str) -> str:
    """Generate a hash of the file content."""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
    except FileNotFoundError:
        return "file_not_found"
    return hash_md5.hexdigest()


def get_file_record(conn: sqlite3.Connection, filepath: str) -> Optional[Dict[str, Any]]:
    """Get the record of a processed file from the database."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT filepath, last_modified, content_hash FROM processed_files WHERE filepath = ?",
        (filepath,)
    )
    result = cursor.fetchone()

    if result:
        return {
            "filepath": result[0],
            "last_modified": result[1],
            "content_hash": result[2]
        }
    return None


def update_file_record(conn: sqlite3.Connection, filepath: str, last_modified: float, content_hash: str):
    """Update the record of a processed file in the database."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO processed_files (filepath, last_modified, content_hash, processed_at)
        VALUES (?, ?, ?, ?)
    """, (filepath, last_modified, content_hash, datetime.now().timestamp()))
    conn.commit()


def get_loader(filepath: str):
    """Get the appropriate loader for a file based on its extension."""
    file_ext = Path(filepath).suffix.lower()

    if file_ext not in config.SUPPORTED_FILE_TYPES:
        raise ValueError(f"Unsupported file type: {file_ext}")

    loader_name = config.SUPPORTED_FILE_TYPES[file_ext]
    loader_class = LOADER_MAPPING.get(loader_name)

    if not loader_class:
        raise ValueError(f"Loader class not found for: {loader_name}")

    if loader_name == "TextLoader":
        return loader_class(filepath, encoding='utf-8')
    elif loader_name == "CSVLoader":
        return loader_class(filepath)
    elif "Unstructured" in loader_name:
        return loader_class(filepath, **config.UNSTRUCTURED_CONFIG)
    else:
        return loader_class(filepath)

# --- FIX: New function for intelligent, header-based splitting ---
def split_text_by_headers(documents: List[Document]) -> List[Document]:
    """
    Splits document text based on structural headers.
    This is more effective than a fixed-size splitter for structured documents.
    """
    new_chunks = []
    # This regex looks for lines starting with "Section X:" or a number like "1.", "2.", etc.
    # It will serve as our splitting point.
    header_pattern = r"(Section \d+:|^\d+\.)"

    for doc in documents:
        # Combine the page content if it's already split by the loader
        full_text = doc.page_content
        # Split the text based on the identified header pattern
        # The re.split function can keep the delimiter, which is what we want.
        # (.*?) is a non-greedy capture of the delimiter itself.
        split_text = re.split(f'({header_pattern}.*)', full_text)

        # The result of the split will be like: ['', 'Section 1: ...', 'content...', '', '2. ...', 'content...']
        # We need to re-combine the delimiter with its following content.
        temp_chunk = ""
        for part in split_text:
            if re.match(header_pattern, part):
                # If we find a new header, the previous chunk is complete.
                if temp_chunk.strip():
                    new_chunks.append(Document(page_content=temp_chunk.strip(), metadata=doc.metadata.copy()))
                # Start a new chunk with the new header
                temp_chunk = part
            else:
                # Append the content to the current chunk
                temp_chunk += part

        # Add the last remaining chunk
        if temp_chunk.strip():
            new_chunks.append(Document(page_content=temp_chunk.strip(), metadata=doc.metadata.copy()))

    return new_chunks
# --- End of new function ---


def load_and_chunk_document(filepath: str) -> List[Document]:
    """Load a document and split it into chunks with metadata."""
    try:
        file_path = Path(filepath)
        file_name = file_path.name
        file_type = file_path.suffix.lower()
        last_modified = os.path.getmtime(filepath)

        loader = get_loader(filepath)
        documents = loader.load()

        # Add base metadata to each document from the loader
        for doc in documents:
            doc.metadata.update({
                "source": str(filepath),
                "last_modified": last_modified,
                "file_type": file_type,
                "file_name": file_name
            })

        # --- FIX: Use the new header-based splitting strategy ---
        chunks = split_text_by_headers(documents)

        # As a fallback, you can still split very large chunks if needed
        final_chunks = []
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE, # This will now only apply to chunks that are still too large
            chunk_overlap=config.CHUNK_OVERLAP,
            length_function=len
        )
        for chunk in chunks:
            if len(chunk.page_content) > config.CHUNK_SIZE:
                # If a structurally-split chunk is still too big, split it further
                sub_chunks = text_splitter.split_documents([chunk])
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)

        # Add unique hash to each final chunk's metadata
        for chunk in final_chunks:
            chunk.metadata["chunk_content_hash"] = hashlib.md5(chunk.page_content.encode('utf-8')).hexdigest()
        # --- End of fix ---


        print(f"  ✓ Loaded {len(documents)} document(s) and created {len(final_chunks)} chunks using header-based strategy.")
        return final_chunks

    except Exception as e:
        print(f"  ✗ Error processing {filepath}: {str(e)}")
        return []


def ingest_documents():
    """Main function to ingest documents into ChromaDB."""
    print("🚀 Starting document ingestion pipeline...")

    print("📊 Initializing tracking database...")
    conn = init_db()

    print(f"🤖 Loading embedding model: {config.EMBEDDING_MODEL_NAME}...")
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': True}

    embedding_function = HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL_NAME,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
    print("  ✓ Embedding model loaded.")

    print("🗄️  Initializing ChromaDB client...")
    db_client = chromadb.PersistentClient(path=str(config.CHROMA_PERSIST_DIR))

    vector_db = Chroma(
        client=db_client,
        collection_name=config.CHROMA_COLLECTION_NAME,
        embedding_function=embedding_function,
        persist_directory=str(config.CHROMA_PERSIST_DIR)
    )
    print(f"  ✓ ChromaDB collection '{config.CHROMA_COLLECTION_NAME}' ready.")

    if not config.REFERENCE_DOCS_DIR.exists():
        print(f"  ✗ Reference docs directory not found: {config.REFERENCE_DOCS_DIR}")
        return

    print("🔍 Scanning for documents...")
    supported_files = []
    for root, _, files in os.walk(config.REFERENCE_DOCS_DIR):
        for file in files:
            filepath = os.path.join(root, file)
            file_ext = Path(filepath).suffix.lower()
            if file_ext in config.SUPPORTED_FILE_TYPES:
                supported_files.append(filepath)
    print(f"  ✓ Found {len(supported_files)} supported files")

    if not supported_files:
        print("  ℹ️  No supported files found to process")
        return

    print("\n🧹 Checking for deleted documents to remove from DB...")
    current_files_on_disk = set(supported_files)
    cursor = conn.cursor()
    cursor.execute("SELECT filepath FROM processed_files")
    all_tracked_files_in_db = {row[0] for row in cursor.fetchall()}
    files_to_delete_from_db = all_tracked_files_in_db - current_files_on_disk

    if files_to_delete_from_db:
        print(f"  🗑️ Deleting data for {len(files_to_delete_from_db)} removed documents from ChromaDB...")
        # Placeholder for delete logic
        print("  (Deletion logic would go here)")
    else:
        print("  No documents found for deletion.")

    processed_count = 0
    skipped_count = 0
    total_chunks_processed = 0

    print(f"\nProcessing {len(supported_files)} files...")
    for filepath in tqdm(supported_files, desc="Ingesting documents"):
        try:
            last_modified = os.path.getmtime(filepath)
            content_hash = get_file_hash(filepath)
            record = get_file_record(conn, filepath)

            if record and record["last_modified"] == last_modified and record["content_hash"] == content_hash:
                skipped_count += 1
                continue

            print(f"  📄 Processing {os.path.basename(filepath)}...")
            chunks = load_and_chunk_document(filepath)
            if not chunks:
                print(f"  ⚠️  No chunks created for {os.path.basename(filepath)}")
                continue

            chunk_ids = [
                f"{hashlib.sha256(filepath.encode()).hexdigest()}_{i}"
                for i, _ in enumerate(chunks)
            ]
            
            vector_db.add_documents(
                documents=chunks,
                ids=chunk_ids
            )

            update_file_record(conn, filepath, last_modified, content_hash)
            print(f"  ✅ Successfully processed {os.path.basename(filepath)} ({len(chunks)} chunks)")
            processed_count += 1
            total_chunks_processed += len(chunks)

        except Exception as e:
            print(f"  ✗ Error processing {filepath}: {str(e)}")
            continue

    print("\n📊 Ingestion Summary:")
    print(f"  • Total files found in folder: {len(supported_files)}")
    print(f"  • Files newly processed or updated: {processed_count}")
    print(f"  • Files skipped (no changes): {skipped_count}")
    print(f"  • Total chunks upserted: {total_chunks_processed}")
    print(f"  • ChromaDB Collection: {config.CHROMA_COLLECTION_NAME}")
    print(f"  • ChromaDB location: {config.CHROMA_PERSIST_DIR}")

    conn.close()
    print("🎉 Document ingestion completed!")


if __name__ == "__main__":
    ingest_documents()