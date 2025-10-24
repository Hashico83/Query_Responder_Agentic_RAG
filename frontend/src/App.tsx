import React, { useState } from "react";
import ChatInterface from "./components/ChatInterface";
import HistorySidebar from "./components/HistorySidebar";
import QueryInput from "./components/QueryInput";
import "./App.css";

interface HistoryItem {
  id: string;
  query: string;
  response: string;
  timestamp: string;
}

// --- FIX: Added the 'source' property to the interface ---
interface ConversationItem {
  query: string;
  response: string;
  sources?: string[];
  liked?: boolean;
  source?: string; // To track where the response came from
}

function App() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [conversationHistory, setConversationHistory] = useState<
    ConversationItem[]
  >([]);
  const [isTyping, setIsTyping] = useState(false);
  const [currentTypingResponse, setCurrentTypingResponse] = useState("");
  const [sessionId, setSessionId] = useState(Date.now().toString());

  const handleNewQuery = async (query: string) => {
    const userMessage: ConversationItem = { query, response: "" };
    setConversationHistory((prev) => [...prev, userMessage]);

    setIsTyping(true);
    setCurrentTypingResponse("");

    try {
      const response = await fetch("http://localhost:5001/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-ID": sessionId,
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const responseText = data.response || "No response received";
      const responseSources = data.sources || [];
      // --- FIX: Capture the 'source' from the backend response ---
      const responseSource = data.source || "Unknown";

      // Simulate typing for the response
      let typedText = "";
      for (const char of responseText) {
        typedText += char;
        setCurrentTypingResponse(typedText);
        await new Promise((resolve) => setTimeout(resolve, 20));
      }

      setConversationHistory((prev) => {
        const updatedHistory = [...prev];
        const lastItem = updatedHistory[updatedHistory.length - 1];
        lastItem.response = responseText;
        lastItem.sources = responseSources;
        // --- FIX: Save the 'source' to the conversation state ---
        lastItem.source = responseSource;
        return updatedHistory;
      });
      setCurrentTypingResponse("");

      const newHistoryItem: HistoryItem = {
        id: Date.now().toString(),
        query,
        response: responseText,
        timestamp: new Date().toLocaleString(),
      };
      setHistory((prev) => [newHistoryItem, ...prev]);
    } catch (error) {
      console.error("Error fetching response:", error);
      const errorResponse =
        "Error: Unable to fetch response from the server. Please try again.";

      setConversationHistory((prev) => {
        const updatedHistory = [...prev];
        const lastItem = updatedHistory[updatedHistory.length - 1];
        lastItem.response = errorResponse;
        return updatedHistory;
      });
      setCurrentTypingResponse("");
    } finally {
      setIsTyping(false);
    }
  };

  const handleFeedback = async (
    query: string,
    response: string,
    liked: boolean
  ) => {
    try {
      await fetch("http://localhost:5001/api/feedback", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query, response, liked }),
      });
      // Optionally, update the UI to show feedback was registered
      setConversationHistory((prev) => {
        const updatedHistory = prev.map((item) => {
          if (item.query === query && item.response === response) {
            return { ...item, liked };
          }
          return item;
        });
        return updatedHistory;
      });
    } catch (error) {
      console.error("Error sending feedback:", error);
    }
  };

  const handleSelectHistory = (item: HistoryItem) => {
    // This function is kept for the history sidebar functionality
  };

  return (
    <div className="app">
      <HistorySidebar history={history} onSelectHistory={handleSelectHistory} />
      <div className="main-content">
        <header className="app-header">
          <h1>Accelerate RFP response with Agentic RAG</h1>
          <p>
            As a user, feel free to ask questions related to your RFP Response
            and the the system will respond based on the documents that are
            available in the reference folder (Old RFP response etc.). In case
            the system is not able to find the answer, it will search the web
            for the answer. Implemented using Langchain, Ollama, and ChromaDB
            and using agents to generate the response.
          </p>
        </header>

        <div className="chat-container">
          <ChatInterface
            conversationHistory={conversationHistory}
            isTyping={isTyping}
            currentTypingResponse={currentTypingResponse}
            onFeedback={handleFeedback}
          />
          <QueryInput onSubmit={handleNewQuery} isLoading={isTyping} />
        </div>
      </div>
    </div>
  );
}

export default App;
