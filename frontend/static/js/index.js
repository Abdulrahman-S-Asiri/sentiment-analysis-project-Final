document.addEventListener("DOMContentLoaded", () => {
  const analysisForm = document.getElementById("analysisForm");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const textInput = document.getElementById("textInput");
  const resultDisplay = document.getElementById("resultDisplay");
  const sentimentText = document.getElementById("sentimentText");
  const sentimentBadge = document.getElementById("sentimentBadge");
  const analyzedText = document.getElementById("analyzedText");
  const confidenceFill = document.getElementById("confidenceFill");
  const confidencePercent = document.getElementById("confidencePercent");
  const historyList = document.getElementById("historyList");

  // Sentiment emoji mapping
  const sentimentEmojis = {
    happiness: "😊",
    sadness: "😢",
    anger: "😠",
    fear: "😨",
    surprise: "😲",
    disgust: "🤢",
    neutral: "😐"
  };

  // Sentiment color mapping
  const sentimentColors = {
    happiness: "#10b981",
    sadness: "#3b82f6",
    anger: "#ef4444",
    fear: "#8b5cf6",
    surprise: "#f59e0b",
    disgust: "#84cc16",
    neutral: "#6b7280"
  };

  analysisForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const text = textInput.value.trim();
    if (!text) {
      alert("⚠️ Please enter text to analyze.");
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) {
      alert("❗ You must be logged in to analyze.");
      window.location.href = "/login";
      return;
    }

    // Disable button and show loading
    analyzeBtn.disabled = true;
    const originalBtnText = analyzeBtn.innerHTML;
    analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';

    try {
      const response = await fetch("/predict/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ text })
      });

      const data = await response.json();

      if (response.ok) {
        // Update sentiment display
        const sentiment = data.sentiment;
        sentimentText.textContent = sentiment.charAt(0).toUpperCase() + sentiment.slice(1);
        
        // Update badge with emoji and color
        const emoji = sentimentEmojis[sentiment] || "😐";
        const color = sentimentColors[sentiment] || "#6b7280";
        sentimentBadge.innerHTML = `<i class="fas fa-heart"></i> ${emoji} ${sentimentText.textContent}`;
        sentimentBadge.style.background = `${color}20`;
        sentimentBadge.style.borderColor = color;
        sentimentBadge.style.color = color;

        // Update analyzed text
        analyzedText.textContent = data.text;

        // Update confidence
        const confidence = data.confidence || data.score || 0;
        const confidencePercentValue = Math.round(confidence * 100);
        confidenceFill.style.width = `${confidencePercentValue}%`;
        confidencePercent.textContent = `${confidencePercentValue}%`;

        // Show result display
        resultDisplay.classList.remove("hidden");
        resultDisplay.scrollIntoView({ behavior: "smooth", block: "nearest" });

        // Add to quick history
        addToHistory(data.text, sentiment, confidencePercentValue);

        // Clear input
        textInput.value = "";
      } else {
        alert(`❌ Error: ${data.detail || "Unknown error occurred."}`);
      }
    } catch (error) {
      console.error("🔥 Error in fetch:", error);
      alert("🚨 Network error occurred. Please try again.");
    } finally {
      // Re-enable button
      analyzeBtn.disabled = false;
      analyzeBtn.innerHTML = originalBtnText;
    }
  });

  function addToHistory(text, sentiment, confidence) {
    // Remove empty state if exists
    const emptyState = historyList.querySelector('li[style*="text-align: center"]');
    if (emptyState) {
      emptyState.remove();
    }

    // Create history item
    const li = document.createElement("li");
    li.className = "history-item fade-in";
    
    const emoji = sentimentEmojis[sentiment] || "😐";
    const shortText = text.length > 50 ? text.substring(0, 50) + "..." : text;
    
    li.innerHTML = `
      <div style="display: flex; align-items: center; gap: var(--spacing-sm);">
        <span style="font-size: 1.5rem;">${emoji}</span>
        <div style="flex: 1;">
          <div style="color: rgba(255, 255, 255, 0.9); margin-bottom: 4px;">${shortText}</div>
          <div style="display: flex; gap: var(--spacing-sm); align-items: center; font-size: 0.85rem;">
            <span style="color: rgba(255, 255, 255, 0.7);">${sentiment}</span>
            <span style="color: rgba(255, 255, 255, 0.5);">•</span>
            <span style="color: rgba(255, 255, 255, 0.7);">${confidence}%</span>
          </div>
        </div>
      </div>
    `;
    
    historyList.prepend(li);
    
    // Limit to 10 items
    while (historyList.children.length > 10) {
      historyList.removeChild(historyList.lastChild);
    }
  }

  // Load quick history on page load
  async function loadQuickHistory() {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const response = await fetch("/history/", {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data && data.length > 0) {
          // Remove empty state
          const emptyState = historyList.querySelector('li[style*="text-align: center"]');
          if (emptyState) {
            emptyState.remove();
          }

          // Add recent items (max 5)
          data.slice(0, 5).forEach(item => {
            addToHistory(
              item.text,
              item.sentiment,
              Math.round((item.confidence || item.score || 0) * 100)
            );
          });
        }
      }
    } catch (error) {
      console.error("Error loading history:", error);
    }
  }

  loadQuickHistory();
});
