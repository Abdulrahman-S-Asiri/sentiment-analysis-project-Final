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
  const emotionsContainer = document.getElementById("emotionsContainer");
  const explanationArea = document.getElementById("explanationArea");
  const emotionTabs = document.getElementById("emotionTabs");
  const highlightedText = document.getElementById("highlightedText");

  const sentimentEmojis = {
    happiness: "😊", sadness: "😢", anger: "😠", fear: "😨",
    surprise: "😲", disgust: "🤢", neutral: "😐"
  };

  const sentimentColors = {
    happiness: "#10b981", sadness: "#3b82f6", anger: "#ef4444",
    fear: "#8b5cf6", surprise: "#f59e0b", disgust: "#84cc16", neutral: "#6b7280"
  };

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function renderHighlight(container, text, tokenImportances) {
    if (!tokenImportances || tokenImportances.length === 0) {
      container.innerHTML = `<span style="color:rgba(255,255,255,0.7)">${escapeHtml(text)}</span>`;
      return;
    }
    const maxAbs = Math.max(...tokenImportances.map(t => Math.abs(t.importance)), 0.001);
    container.innerHTML = tokenImportances.slice(0, 20).map(ti => {
      const norm = Math.abs(ti.importance) / maxAbs;
      const opacity = 0.2 + norm * 0.8;
      const color = ti.importance > 0
        ? `rgba(16, 185, 129, ${opacity})`
        : `rgba(239, 68, 68, ${opacity})`;
      return `<span class="shap-token" style="background:${color}" title="${escapeHtml(ti.token)}: ${ti.importance > 0 ? "+" : ""}${ti.importance.toFixed(3)}">${escapeHtml(ti.token)}</span>`;
    }).join(" ");
    container.innerHTML += `
      <div style="margin-top:12px; font-size:0.8rem; color:rgba(255,255,255,0.5); display:flex; gap:16px;">
        <span><span style="display:inline-block;width:12px;height:12px;background:rgba(16,185,129,0.6);border-radius:2px;margin-right:4px;"></span> Supports</span>
        <span><span style="display:inline-block;width:12px;height:12px;background:rgba(239,68,68,0.6);border-radius:2px;margin-right:4px;"></span> Weakens</span>
      </div>`;
  }

  function displayResults(data) {
    const emotions = data.emotions || [{ label: data.sentiment, confidence: data.confidence || 0 }];
    const topEmotion = emotions[0] || { label: "neutral", confidence: 0 };

    // Multi-emotion badges
    emotionsContainer.innerHTML = emotions.map(e => {
      const color = sentimentColors[e.label] || "#6b7280";
      const emoji = sentimentEmojis[e.label] || "😐";
      const pct = Math.round(e.confidence * 100);
      return `<span class="emotion-badge" style="background:${color}20;border-color:${color};color:${color}">${emoji} ${e.label} (${pct}%)</span>`;
    }).join("");

    // SHAP explanations
    const explanations = data.explanations || {};
    if (Object.keys(explanations).length > 0) {
      explanationArea.classList.remove("hidden");
      emotionTabs.innerHTML = "";
      emotions.forEach((em, i) => {
        if (!explanations[em.label]) return;
        const btn = document.createElement("button");
        btn.className = "emotion-tab" + (i === 0 ? " active" : "");
        btn.textContent = em.label.charAt(0).toUpperCase() + em.label.slice(1);
        btn.addEventListener("click", () => {
          document.querySelectorAll(".emotion-tab").forEach(b => b.classList.remove("active"));
          btn.classList.add("active");
          renderHighlight(highlightedText, data.text, explanations[em.label]);
        });
        emotionTabs.appendChild(btn);
      });
      if (emotions.length > 0 && explanations[emotions[0].label]) {
        renderHighlight(highlightedText, data.text, explanations[emotions[0].label]);
      }
    } else {
      explanationArea.classList.add("hidden");
    }

    // Single badge (backward compat)
    const emoji = sentimentEmojis[topEmotion.label] || "😐";
    const color = sentimentColors[topEmotion.label] || "#6b7280";
    sentimentText.textContent = topEmotion.label.charAt(0).toUpperCase() + topEmotion.label.slice(1);
    sentimentBadge.innerHTML = `<i class="fas fa-heart"></i> ${emoji} ${sentimentText.textContent}`;
    sentimentBadge.style.background = `${color}20`;
    sentimentBadge.style.borderColor = color;
    sentimentBadge.style.color = color;

    analyzedText.textContent = data.text;

    // Confidence bar
    const pct = Math.round(topEmotion.confidence * 100);
    confidenceFill.style.width = `${pct}%`;
    confidencePercent.textContent = `${pct}%`;

    resultDisplay.classList.remove("hidden");
    resultDisplay.scrollIntoView({ behavior: "smooth", block: "nearest" });

    textInput.value = "";
    addToHistory(data.text, emotions, pct);
  }

  analysisForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const text = textInput.value.trim();
    if (!text) {
      alert("Please enter text to analyze.");
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) {
      alert("You must be logged in to analyze.");
      window.location.href = "/login";
      return;
    }

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
        displayResults(data);
      } else {
        alert(`Error: ${data.detail || "Unknown error occurred."}`);
      }
    } catch (error) {
      console.error("Error in fetch:", error);
      alert("Network error occurred. Please try again.");
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtn.innerHTML = originalBtnText;
    }
  });

  function addToHistory(text, emotions, topConfidence) {
    const emptyState = historyList.querySelector('li[style*="text-align: center"]');
    if (emptyState) emptyState.remove();

    const li = document.createElement("li");
    li.className = "history-item fade-in";

    const shortText = text.length > 50 ? text.substring(0, 50) + "..." : text;

    li.innerHTML = `
      <div style="display: flex; align-items: center; gap: var(--spacing-sm);">
        <div style="flex: 1;">
          <div style="color: rgba(255, 255, 255, 0.9); margin-bottom: 4px;">${shortText}</div>
          <div style="display: flex; gap: var(--spacing-sm); align-items: center; font-size: 0.85rem; flex-wrap: wrap;">
            ${emotions.slice(0, 3).map(e => {
              const emoji = sentimentEmojis[e.label] || "😐";
              const pct = Math.round(e.confidence * 100);
              return `<span style="color: rgba(255, 255, 255, 0.7);">${emoji} ${pct}%</span>`;
            }).join("")}
            ${emotions.length > 3 ? `<span style="color: rgba(255, 255, 255, 0.4);">+${emotions.length - 3} more</span>` : ""}
          </div>
        </div>
      </div>
    `;

    historyList.prepend(li);
    while (historyList.children.length > 10) {
      historyList.removeChild(historyList.lastChild);
    }
  }

  // Load quick history
  async function loadQuickHistory() {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const response = await fetch("/history/", {
        headers: { "Authorization": `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        if (data && data.length > 0) {
          const emptyState = historyList.querySelector('li[style*="text-align: center"]');
          if (emptyState) emptyState.remove();

          data.slice(0, 5).forEach(item => {
            const emotions = item.emotions || [{ label: item.sentiment, confidence: item.confidence || 0 }];
            addToHistory(item.text, emotions, Math.round((item.confidence || item.score || 0) * 100));
          });
        }
      }
    } catch (error) {
      console.error("Error loading history:", error);
    }
  }

  loadQuickHistory();
});
