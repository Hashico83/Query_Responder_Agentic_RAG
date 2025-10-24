# Query Responder RAG App

A full-stack application featuring a React frontend with a dark theme and turquoise accents, connected to a Flask backend that provides Bhagavad Gita wisdom through a REST API.

## 🏗️ Project Structure

```
query-responder-ragApp/
├── backend/
│   ├── app.py              # Flask API server
│   ├── requirements.txt     # Python dependencies
│   └── README.md          # Backend documentation
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── App.tsx        # Main application
│   │   └── main.tsx       # Entry point
│   ├── package.json       # Node.js dependencies
│   └── README.md          # Frontend documentation
├── ingestion-pipeline/
│   ├── config.py           # Configuration settings
│   ├── ingest_docs.py      # Document ingestion script
│   ├── requirements.txt    # Python dependencies
│   ├── chroma_db_data/    # ChromaDB storage
│   └── README.md          # Ingestion documentation
├── reference-docs/         # Document storage for RAG
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v16 or higher)
- **Python** (v3.8 or higher)
- **npm** or **yarn**

### Option 1: Single Command Startup (Recommended)

**For macOS/Linux:**

```bash
cd query-responder-ragApp
./start-app.sh
```

**For Windows:**

```bash
cd query-responder-ragApp
start-app.bat
```

This will automatically:

- Create a Python virtual environment
- Install all dependencies
- Start both backend and frontend servers
- Open the application in your browser

### Option 2: Manual Setup

#### Backend Setup

1. **Navigate to the backend directory:**

   ```bash
   cd query-responder-ragApp/backend
   ```

2. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Flask server:**

   ```bash
   python3 app.py
   ```

4. **Verify the backend is running:**
   - Open http://localhost:5001/health in your browser
   - You should see: `{"status": "healthy", "service": "Query Responder RAG API"}`

#### Frontend Setup

1. **Open a new terminal and navigate to the frontend directory:**

   ```bash
   cd query-responder-ragApp/frontend
   ```

2. **Install Node.js dependencies:**

   ```bash
   npm install
   ```

3. **Start the React development server:**

   ```bash
   npm run dev
   ```

4. **Open the application:**
   - The app will be available at http://localhost:5173
   - You'll see the dark-themed interface with turquoise accents

## 🎨 Features

### Frontend

- **Dark Theme**: Deep background (#1a1a1a) with turquoise accents (#00bcd4)
- **Chat Interface**: Real-time query input and response display
- **History Sidebar**: Expandable sidebar showing previous queries
- **Responsive Design**: Works on desktop and mobile
- **Loading States**: Visual feedback during API calls

### Backend

- **Flask API**: Lightweight Python web framework
- **CORS Support**: Enabled for frontend-backend communication
- **Bhagavad Gita Wisdom**: Returns spiritual teachings from the Gita
- **Error Handling**: Proper HTTP status codes and error messages

## 🔧 API Endpoints

### POST `/api/query`

Submit a query and receive a Bhagavad Gita response.

**Request:**

```json
{
  "query": "What is karma yoga?"
}
```

**Response:**

```json
{
  "response": "Krishna says in the Bhagavad Gita: 'You have the right to work only, but never to its fruits...'",
  "query": "What is karma yoga?",
  "source": "Bhagavad Gita"
}
```

### GET `/health`

Health check endpoint for monitoring.

## 🎯 Usage

1. **Start both servers** (backend on port 5001, frontend on port 5173)
2. **Open the frontend** in your browser
3. **Type a question** in the chat input
4. **Click "Send"** or press Enter
5. **View the response** from the Bhagavad Gita
6. **Use the history sidebar** to view previous queries

## 📚 Document Ingestion Pipeline

The application includes a comprehensive document ingestion pipeline that processes documents from the `reference-docs` folder and stores them in a ChromaDB vector database for RAG functionality.

### Setting Up Document Ingestion

1. **Navigate to the ingestion pipeline:**

   ```bash
   cd query-responder-ragApp/ingestion-pipeline
   ```

2. **Create a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Add documents to the reference-docs folder:**

   ```bash
   # Place your documents in the reference-docs folder
   cp your_documents/* ../reference-docs/
   ```

5. **Run the ingestion pipeline:**
   ```bash
   python3 ingest_docs.py
   ```

### Supported Document Types

- **PDF Documents** (`.pdf`)
- **Word Documents** (`.docx`, `.doc`)
- **Excel Spreadsheets** (`.xlsx`, `.xls`)
- **PowerPoint Presentations** (`.pptx`, `.ppt`)
- **Text Files** (`.txt`, `.md`)
- **CSV Files** (`.csv`)
- **Images** (`.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`)
- **HTML Files** (`.html`, `.htm`)
- **JSON Files** (`.json`)
- **XML Files** (`.xml`)
- **Rich Text Files** (`.rtf`)
- **Email Files** (`.eml`)

### Features

- **Incremental Processing**: Only processes new or updated documents
- **Smart Chunking**: Splits documents into optimal chunks with configurable overlap
- **Metadata Preservation**: Maintains source file information and timestamps
- **Progress Tracking**: Real-time progress bars and detailed logging
- **Error Handling**: Graceful error handling with detailed error messages

## 🛠️ Development

### Backend Development

- The Flask app runs in debug mode for hot reloading
- API changes will automatically restart the server
- Check the terminal for any error messages

### Frontend Development

- Vite provides fast hot module replacement
- Changes to React components will update immediately
- TypeScript provides type safety

## 🔍 Troubleshooting

### Backend Issues

- **Port 5001 in use**: Change the port in `backend/app.py`
- **Python not found**: Use `python3` instead of `python`
- **Dependencies missing**: Run `pip install -r requirements.txt`

### Frontend Issues

- **Port 5173 in use**: Vite will automatically use the next available port
- **Dependencies missing**: Run `npm install`
- **API connection failed**: Ensure the backend is running on port 5001

### CORS Issues

- The backend has CORS enabled for all origins
- If you see CORS errors, check that the backend is running

## 📝 Notes

- The backend currently returns a hardcoded Bhagavad Gita mantra
- In a production environment, this would be replaced with actual RAG processing
- The frontend is configured to connect to `http://localhost:5001`
- Both servers run in development mode with hot reloading enabled
