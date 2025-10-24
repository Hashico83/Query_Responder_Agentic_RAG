import os
import chromadb
from pprint import pprint # For pretty printing dictionaries and lists

# Assuming config.py is in the same directory or accessible via PYTHONPATH
import config

def check_chroma_db():
    print(f"Connecting to ChromaDB at: {config.CHROMA_PERSIST_DIR}")

    # Initialize the persistent client
    try:
        client = chromadb.PersistentClient(path=str(config.CHROMA_PERSIST_DIR))
        print("ChromaDB client connected.")
    except Exception as e:
        print(f"Error connecting to ChromaDB: {e}")
        print("Ensure the 'chroma_db_data' directory exists and is accessible.")
        return

    # 1. List all collections
    print("\n--- Listing Collections ---")
    collections = client.list_collections()
    if not collections:
        print("No collections found in this ChromaDB instance.")
        print("Has the ingestion script run successfully at least once?")
        return

    print("Found collections:")
    for col in collections:
        print(f"- {col.name}")

    # 2. Get the specific collection you're using for documents
    collection_name = config.CHROMA_COLLECTION_NAME
    if collection_name not in [col.name for col in collections]:
        print(f"\nCollection '{collection_name}' not found.")
        print("Please check config.CHROMA_COLLECTION_NAME or run the ingestion script.")
        return

    collection = client.get_collection(name=collection_name)
    print(f"\n--- Details for Collection: '{collection.name}' ---")

    # 3. Get total count of items
    count = collection.count()
    print(f"Total items (chunks) in collection: {count}")

    if count == 0:
        print("Collection is empty. No documents ingested yet or an error occurred during ingestion.")
        return

    # 4. Peek at some items (get the first few without filtering)
    print("\n--- Peeking at first 5 items (IDs, Documents, Metadatas, Embeddings) ---")
    # include=['documents', 'metadatas', 'embeddings'] fetches the actual content, metadata, and vectors
    # By default, it only returns IDs.
    try:
        peek_results = collection.peek(limit=5)
        # ChromaDB results are returned as a dictionary with 'ids', 'embeddings', 'documents', 'metadatas'
        # Check if 'documents' and 'metadatas' keys exist and are not None before accessing.
        if peek_results and peek_results['ids']:
            for i, chunk_id in enumerate(peek_results['ids']):
                print(f"\n--- Item {i+1} (ID: {chunk_id}) ---")
                print("Document Content:")
                pprint(peek_results['documents'][i][:200] + "..." if peek_results['documents'][i] and len(peek_results['documents'][i]) > 200 else peek_results['documents'][i]) # Print first 200 chars
                print("\nMetadata:")
                pprint(peek_results['metadatas'][i])
                print(f"\nEmbedding (first 5 values, shape {len(peek_results['embeddings'][i])}):")
                print(peek_results['embeddings'][i][:5])
        else:
            print("No items to peek at or data missing.")
    except Exception as e:
        print(f"Error peeking at items: {e}")
        print("This can happen if the collection was created with a different embedding function or if data is corrupted.")


    # 5. Get items with a filter (example: filter by file_name)
    print("\n--- Example: Getting items filtered by 'file_name' ---")
    # Replace 'your_example_file.pdf' with an actual file name from your reference-docs
    example_file_name = "your_example_file.pdf" # <<<--- IMPORTANT: Change this to a real file name
    try:
        # It's better to fetch by original 'source' path as that's what's definitively unique.
        # Find a source path from the peek_results above and use it for filtering.
        if peek_results and peek_results['metadatas']:
            first_source_path = peek_results['metadatas'][0].get('source')
            if first_source_path:
                print(f"Trying to retrieve chunks from source: {os.path.basename(first_source_path)}")
                filtered_results = collection.get(
                    where={"source": first_source_path},
                    include=['documents', 'metadatas']
                )
                if filtered_results and filtered_results['ids']:
                    print(f"Found {len(filtered_results['ids'])} chunks for {os.path.basename(first_source_path)}:")
                    for i, chunk_id in enumerate(filtered_results['ids']):
                        print(f"  - ID: {chunk_id}, Content: '{filtered_results['documents'][i][:100]}...', Source: {filtered_results['metadatas'][i].get('source')}")
                else:
                    print("No items found for the example source path.")
            else:
                print("Could not get a sample source path for filtering.")
        else:
            print("No data available to demonstrate filtering.")

    except Exception as e:
        print(f"Error during filtered retrieval: {e}")
        print("Ensure 'source' or 'file_name' metadata is correctly stored.")


if __name__ == "__main__":
    check_chroma_db()