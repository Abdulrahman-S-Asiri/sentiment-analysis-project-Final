document.addEventListener("DOMContentLoaded", async () => {
  const token = localStorage.getItem("token");
  const container = document.getElementById("historyContainer");

  if (!token) {
    window.location.href = "/login";
    return;
  }

  // Sentiment emoji and color mapping
  const sentimentEmojis = {
    happiness: "😊",
    sadness: "😢",
    anger: "😠",
    fear: "😨",
    surprise: "😲",
    disgust: "🤢",
    neutral: "😐"
  };

  const sentimentColors = {
    happiness: "#10b981",
    sadness: "#3b82f6",
    anger: "#ef4444",
    fear: "#8b5cf6",
    surprise: "#f59e0b",
    disgust: "#84cc16",
    neutral: "#6b7280"
  };

  try {
    const response = await fetch("/history/", {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    if (!response.ok) {
      throw new Error(`Server responded with status ${response.status}`);
    }

    const results = await response.json();

    if (!Array.isArray(results)) {
      throw new Error("Unexpected response format");
    }

    container.innerHTML = "";

    if (results.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <i class="fas fa-inbox"></i>
          <h3 style="color: rgba(255, 255, 255, 0.7); margin-top: var(--spacing-md);">No analysis history yet</h3>
          <p style="color: rgba(255, 255, 255, 0.5); margin-top: var(--spacing-sm);">
            Start analyzing text to see your history here!
          </p>
          <a href="/analyze" class="btn btn-primary" style="margin-top: var(--spacing-md);">
            <i class="fas fa-magic"></i> Start Analyzing
          </a>
        </div>
      `;
      return;
    }

    results.forEach((item, index) => {
      const emotions = item.emotions || [{ label: item.sentiment, confidence: item.confidence || 0 }];
      const topEmotion = emotions[0] || { label: item.sentiment, confidence: 0 };
      const emoji = sentimentEmojis[topEmotion.label] || "😐";
      const color = sentimentColors[topEmotion.label] || "#6b7280";
      const date = new Date(item.timestamp);
      const formattedDate = date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      });

      const div = document.createElement("div");
      div.className = "history-item fade-in";
      div.style.animationDelay = `${index * 0.1}s`;

      div.innerHTML = `
        <div class="history-icon" style="background: ${color}20; border: 2px solid ${color}; color: ${color};">
          ${emoji}
        </div>
        <div class="history-content">
          <div class="history-text">"${item.text}"</div>
          <div class="history-meta">
            ${emotions.map(e => {
              const ec = sentimentColors[e.label] || "#6b7280";
              const ee = sentimentEmojis[e.label] || "😐";
              const epct = Math.round(e.confidence * 100);
              return `<span class="history-sentiment" style="background:${ec}20; border:1px solid ${ec}; color:${ec};">
                ${ee} ${e.label} (${epct}%)
              </span>`;
            }).join("")}
            <span class="history-date">
              <i class="fas fa-clock"></i> ${formattedDate}
            </span>
          </div>
        </div>
      `;

      container.appendChild(div);
    });

  } catch (err) {
    console.error("❌ Error loading history:", err);
    container.innerHTML = `
      <div class="empty-state">
        <i class="fas fa-exclamation-triangle" style="color: var(--danger);"></i>
        <h3 style="color: rgba(255, 255, 255, 0.7); margin-top: var(--spacing-md);">Failed to load history</h3>
        <p style="color: rgba(255, 255, 255, 0.5); margin-top: var(--spacing-sm);">
          ${err.message || "Please try again later."}
        </p>
        <button onclick="location.reload()" class="btn btn-primary" style="margin-top: var(--spacing-md);">
          <i class="fas fa-redo"></i> Retry
        </button>
      </div>
    `;
  }
});
