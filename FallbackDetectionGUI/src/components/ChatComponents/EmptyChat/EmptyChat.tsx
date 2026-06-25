import "./EmptyChat.css";

export default function EmptyChat() {
  return (
    <div className="empty-chat-main">

      {/* Glowing orb */}
      <div className="empty-chat-orb">
        <span className="empty-chat-orb-icon">◈</span>
      </div>

      {/* Text */}
      <div className="empty-chat-text-block">
        <h2 className="empty-chat-title">Start a Conversation</h2>
        <p className="empty-chat-subtitle">
          Ask anything — the RAG pipeline will retrieve, analyze,
          and respond with fallback detection running in real time.
        </p>
      </div>

      {/* Suggestion chips */}
      <div className="empty-chat-chips">
        <span className="empty-chat-chip">What is RAG?</span>
        <span className="empty-chat-chip">Explain fallback detection</span>
        <span className="empty-chat-chip">How are chunks scored?</span>
        <span className="empty-chat-chip">What triggers a fallback?</span>
      </div>

      {/* Bottom hint */}
      <p className="empty-chat-hint">
        ↓ Type your message below to begin
      </p>

    </div>
  );
}