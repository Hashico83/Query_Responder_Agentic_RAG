import React, { useState } from "react";
import "./HistorySidebar.css";

interface HistoryItem {
  id: string;
  query: string;
  response: string;
  timestamp: string;
}

interface HistorySidebarProps {
  history: HistoryItem[];
  onSelectHistory: (item: HistoryItem) => void;
}

const HistorySidebar: React.FC<HistorySidebarProps> = ({
  history,
  onSelectHistory,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className={`history-sidebar ${isExpanded ? "expanded" : ""}`}>
      <button
        className="history-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="toggle-icon">{isExpanded ? "◀" : "▶"}</span>
        <span className="toggle-text">History</span>
      </button>

      {isExpanded && (
        <div className="history-content">
          <h3>Previous Queries</h3>
          {history.length === 0 ? (
            <p className="no-history">No previous queries</p>
          ) : (
            <div className="history-list">
              {history.map((item) => (
                <div
                  key={item.id}
                  className="history-item"
                  onClick={() => onSelectHistory(item)}
                >
                  <div className="history-query">{item.query}</div>
                  <div className="history-timestamp">{item.timestamp}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default HistorySidebar;
