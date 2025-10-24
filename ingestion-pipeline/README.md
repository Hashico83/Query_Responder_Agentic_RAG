# Document Ingestion Pipeline

A comprehensive document ingestion pipeline for the Query Responder RAG application that processes documents from the `reference-docs` folder and stores them in a ChromaDB vector database.

## Features

- **Multi-format Support**: Handles PDF, Word, Excel, PowerPoint, text, markdown, CSV, images, HTML, JSON, XML, RTF, email, and more
- **Incremental Processing**: Only processes new or updated documents using SQLite tracking
- **Smart Chunking**: Splits documents into optimal chunks with configurable overlap
- **Metadata Preservation**: Maintains source file information, timestamps, and file types
- **Progress Tracking**: Real-time progress bars and detailed logging
- **Error Handling**: Graceful error handling with detailed error messages

## Supported File Types

| Extension | File Type | Loader |
|-----------|-----------|--------|
| `.pdf` | PDF Documents | PyPDFLoader |
| `.docx`, `.doc` | Word Documents | UnstructuredWordDocumentLoader |
| `.xlsx`, `.xls` | Excel Spreadsheets | UnstructuredExcelLoader |
| `.pptx`, `.ppt` | PowerPoint Presentations | UnstructuredPowerPointLoader |
| `.txt`, `.md` | Text Files | TextLoader |
| `.csv` | CSV Files | CSVLoader |
| `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif` | Images | UnstructuredImageLoader |
| `.html`, `.htm` | HTML Files | UnstructuredHTMLLoader |
| `.json` | JSON Files | JSONLoader |
| `.xml` | XML Files | UnstructuredXMLLoader |
| `.rtf` | Rich Text Files | UnstructuredRTFLoader |
| `.eml` | Email Files | UnstructuredEmailLoader |

## Directory Structure

```
ingestion-pipeline/
├── config.py                 # Configuration settings
├── ingest_docs.py           # Main ingestion script
├── requirements.txt         # Python dependencies
├── chroma_db_data/         # ChromaDB persistent storage
├── processed_docs_db.sqlite # SQLite tracking database
└── README.md               # This file
```

## Setup Instructions

### 1. Create Virtual Environment

```bash
cd ingestion-pipeline
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Prepare Reference Documents

Place your documents in the `reference-docs` folder at the same level as the `ingestion-pipeline` directory:

```
query-responder-ragApp/
├── reference-docs/          # Your documents go here
│   ├── document1.pdf
│   ├── document2.docx
│   └── ...
├── ingestion-pipeline/
├── frontend/
└── backend/
```

### 4. Run the Ingestion Pipeline

```bash
python3 ingest_docs.py
```

## Configuration

Edit `config.py` to customize the pipeline:

- **Chunking**: Adjust `CHUNK_SIZE` and `CHUNK_OVERLAP`
- **Embedding Model**: Change `EMBEDDING_MODEL_NAME`
- **Collection Name**: Modify `CHROMA_COLLECTION_NAME`
- **File Types**: Add/remove from `SUPPORTED_FILE_TYPES`

## Output

The pipeline creates:

1. **ChromaDB Collection**: Vector embeddings stored in `chroma_db_data/`
2. **Tracking Database**: SQLite database tracking processed files
3. **Detailed Logs**: Progress information and error messages

## Usage Examples

### First Run
```bash
cd ingestion-pipeline
python3 ingest_docs.py
```
Output:
```
🚀 Starting document ingestion pipeline...
📊 Initializing tracking database...
🤖 Loading embedding model...
🗄️  Initializing ChromaDB...
  ✓ Using collection: reference_documents_collection
🔍 Scanning for documents...
  ✓ Found 5 supported files
📄 Processing document1.pdf...
  ✓ Loaded 1 document(s) and created 12 chunks
  ✅ Successfully processed document1.pdf (12 chunks)
...
📊 Ingestion Summary:
  • Total files found: 5
  • Files processed: 5
  • Files skipped: 0
🎉 Document ingestion completed!
```

### Subsequent Runs
Only new or modified files will be processed:
```
🚀 Starting document ingestion pipeline...
...
  ⏭️  Skipping document1.pdf (no changes)
  📄 Processing new_document.docx...
  ✅ Successfully processed new_document.docx (8 chunks)
...
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Ensure all requirements are installed
2. **File Permissions**: Check read permissions for reference documents
3. **Memory Issues**: Reduce `CHUNK_SIZE` for large documents
4. **Unsupported Files**: Add file type to `SUPPORTED_FILE_TYPES` in config.py

### Error Messages

- `"Unsupported file type"`: Add the file extension to `SUPPORTED_FILE_TYPES`
- `"Loader not found"`: Check that the loader is imported in `ingest_docs.py`
- `"Error processing file"`: Check file format and permissions

## Integration with RAG Application

The ingested documents are automatically available to your RAG application through ChromaDB. The collection name and database location are configured in `config.py` and can be accessed by your backend application. 