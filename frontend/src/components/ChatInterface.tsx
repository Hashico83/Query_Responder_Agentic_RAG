import React from "react";
import "./ChatInterface.css";

// --- FIX: Ensure the 'source' property is included in the interface ---
interface ConversationItem {
  query: string;
  response: string;
  sources?: string[];
  liked?: boolean;
  source?: string;
}

interface ChatInterfaceProps {
  conversationHistory: ConversationItem[];
  isTyping: boolean;
  currentTypingResponse: string;
  onFeedback: (query: string, response: string, liked: boolean) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  conversationHistory,
  isTyping,
  currentTypingResponse,
  onFeedback,
}) => {
  return (
    <div className="chat-interface">
      <div className="chat-messages">
        {conversationHistory.map((item, index) => {
          // --- FIX: Determine if the message is a final answer based on its source ---
          const isFinalAnswer =
            item.source &&
            (item.source.includes("Internal Docs") ||
              item.source.includes("High-Confidence RAG") ||
              item.source.includes("Web Search") ||
              item.source.includes("Exact Match Rephrased"));

          return (
            <div key={index} className="conversation-item">
              <div className="user-message">
                <div className="message-content user-content">
                  <div className="message-label">You:</div>
                  <div className="message-text">{item.query}</div>
                </div>
              </div>

              {item.response && (
                <div className="model-message">
                  <div className="message-content model-content">
                    <div className="message-label">Assistant:</div>
                    <div className="message-text">
                      {item.response.split("\n").map((line, lineIndex) => (
                        <p key={lineIndex}>{line}</p>
                      ))}
                    </div>
                    {item.sources && item.sources.length > 0 && (
                      <div className="message-sources">
                        <p>
                          <strong>Sources:</strong>
                        </p>
                        <ul>
                          {item.sources.map((source, sourceIndex) => (
                            <li key={sourceIndex}>
                              <a
                                href={source}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                {source}
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {/* --- FIX: Conditionally render the feedback buttons --- */}
                    {isFinalAnswer && (
                      <div className="feedback-container">
                        <button
                          className={`feedback-button ${
                            item.liked === true ? "liked" : ""
                          }`}
                          onClick={() =>
                            onFeedback(item.query, item.response, true)
                          }
                        >
                          👍
                        </button>
                        <button
                          className={`feedback-button ${
                            item.liked === false ? "disliked" : ""
                          }`}
                          onClick={() =>
                            onFeedback(item.query, item.response, false)
                          }
                        >
                          👎
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
        {isTyping && (
          <div className="model-message">
            <div className="message-content model-content typing-indicator">
              <div className="message-label">Assistant:</div>
              <div className="message-text">
                <p>{currentTypingResponse}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;
