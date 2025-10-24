import React, { useState } from "react";
import "./QueryInput.css";

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
}

const QueryInput: React.FC<QueryInputProps> = ({ onSubmit, isLoading }) => {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
      setQuery("");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="query-input-container">
      <form onSubmit={handleSubmit} className="query-form">
        <div className="input-wrapper">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Enter your query here..."
            className="query-textarea"
            disabled={isLoading}
            rows={3}
          />
          <button
            type="submit"
            className="submit-button"
            disabled={!query.trim() || isLoading}
          >
            {isLoading ? <div className="button-spinner"></div> : "Send"}
          </button>
        </div>
      </form>
    </div>
  );
};

export default QueryInput;
