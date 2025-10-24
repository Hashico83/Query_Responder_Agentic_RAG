# Query Responder RAG App - Frontend

A React-based frontend application for the Query Responder RAG system, featuring a dark theme with turquoise accents and an intuitive chat interface.

## Features

- **Dark Theme**: Deep background (#1a1a1a) with turquoise accents (#00bcd4)
- **Chat Interface**: Real-time query input and response display
- **History Sidebar**: Expandable sidebar showing previous queries and responses
- **Responsive Design**: Works on desktop and mobile devices
- **Loading States**: Visual feedback during API calls
- **Error Handling**: Graceful error handling for failed requests

## Components

- `App.tsx`: Main application component with state management
- `ChatInterface.tsx`: Displays chat messages and responses
- `HistorySidebar.tsx`: Expandable sidebar for query history
- `QueryInput.tsx`: Text input area with submit functionality

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open your browser to the URL shown in the terminal (usually http://localhost:5173)

## API Integration

The frontend expects the backend API to be running on `http://localhost:5000` with the following endpoint:

- `POST /api/query`: Accepts JSON with `{ query: string }` and returns `{ response: string }`

## Styling

The application uses a custom dark theme with:
- Background: #1a1a1a (deep dark)
- Chat area: #282c34 (lighter dark)
- Text: #e0e0e0 (light)
- Accents: #00bcd4 (turquoise blue)

## Development

- Built with Vite for fast development
- TypeScript for type safety
- React 19 with modern hooks
- CSS modules for component styling

## Available Scripts

- `npm run dev`: Start development server
- `npm run build`: Build for production
- `npm run preview`: Preview production build
- `npm run lint`: Run ESLint
