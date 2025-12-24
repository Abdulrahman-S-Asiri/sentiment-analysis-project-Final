// Admin Dashboard JavaScript

const API_BASE = '/admin';
let currentUserRole = null;

// Check admin access on page load
document.addEventListener("DOMContentLoaded", async () => {
  const token = localStorage.getItem("token");
  
  if (!token) {
    window.location.href = "/login";
    return;
  }

  // Verify admin access
  try {
    const response = await fetch(`${API_BASE}/stats`, {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });

    if (response.status === 403) {
      alert("❌ Access denied. Admin privileges required.");
      window.location.href = "/home";
      return;
    }

    if (!response.ok) {
      throw new Error("Failed to verify admin access");
    }

    // Load dashboard data
    await loadDashboard();
    setupTabs();
    setupLogout();
  } catch (error) {
    console.error("Error:", error);
    if (error.message.includes("403")) {
      alert("❌ Access denied. Admin privileges required.");
      window.location.href = "/home";
    }
  }
});

// Load dashboard statistics
async function loadDashboard() {
  const token = localStorage.getItem("token");
  
  try {
    const response = await fetch(`${API_BASE}/stats`, {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });

    if (!response.ok) throw new Error("Failed to load statistics");

    const stats = await response.json();

    // Update stat cards
    document.getElementById("totalUsers").textContent = stats.users.total;
    document.getElementById("activeUsers").textContent = stats.users.active;
    document.getElementById("totalAnalyses").textContent = stats.analyses.total;
    document.getElementById("todayAnalyses").textContent = stats.analyses.today;

    // Load users
    await loadUsers();
    
    // Load analyses
    await loadAnalyses();
    
    // Load sentiment stats
    displaySentimentStats(stats.sentiments);
  } catch (error) {
    console.error("Error loading dashboard:", error);
    showError("Failed to load dashboard data");
  }
}

// Load users
async function loadUsers() {
  const token = localStorage.getItem("token");
  const usersList = document.getElementById("usersList");
  
  try {
    const response = await fetch(`${API_BASE}/users`, {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });

    if (!response.ok) throw new Error("Failed to load users");

    const users = await response.json();
    
    if (users.length === 0) {
      usersList.innerHTML = '<div class="empty-state"><i class="fas fa-inbox"></i><p>No users found</p></div>';
      return;
    }

    usersList.innerHTML = users.map(user => `
      <div class="table-row">
        <div>#${user.id}</div>
        <div><strong>${user.username}</strong></div>
        <div>${user.email}</div>
        <div>
          <span class="badge ${user.role === 'admin' ? 'badge-admin' : 'badge-user'}">
            <i class="fas fa-${user.role === 'admin' ? 'shield-alt' : 'user'}"></i>
            ${user.role}
          </span>
        </div>
        <div>
          <span class="badge ${user.is_active === 'active' ? 'badge-active' : 'badge-inactive'}">
            <i class="fas fa-${user.is_active === 'active' ? 'check-circle' : 'times-circle'}"></i>
            ${user.is_active}
          </span>
        </div>
        <div>${user.analyses_count || 0}</div>
        <div class="action-buttons">
          <button class="btn btn-sm btn-primary" onclick="viewUserDetails(${user.id})" title="View Details">
            <i class="fas fa-eye"></i>
          </button>
          ${user.role !== 'admin' ? `
            <button class="btn btn-sm btn-warning" onclick="toggleUserRole(${user.id}, '${user.role}')" title="Toggle Role">
              <i class="fas fa-user-shield"></i>
            </button>
            <button class="btn btn-sm ${user.is_active === 'active' ? 'btn-warning' : 'btn-success'}" 
                    onclick="toggleUserStatus(${user.id}, '${user.is_active}')" 
                    title="${user.is_active === 'active' ? 'Deactivate' : 'Activate'}">
              <i class="fas fa-${user.is_active === 'active' ? 'ban' : 'check'}"></i>
            </button>
          ` : ''}
          ${user.role !== 'admin' ? `
            <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id}, '${user.username}')" title="Delete User">
              <i class="fas fa-trash"></i>
            </button>
          ` : ''}
        </div>
      </div>
    `).join('');
  } catch (error) {
    console.error("Error loading users:", error);
    usersList.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load users</p></div>';
  }
}

// Load analyses
async function loadAnalyses() {
  const token = localStorage.getItem("token");
  const analysesList = document.getElementById("analysesList");
  
  try {
    const response = await fetch(`${API_BASE}/analyses`, {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });

    if (!response.ok) throw new Error("Failed to load analyses");

    const analyses = await response.json();
    
    if (analyses.length === 0) {
      analysesList.innerHTML = '<div class="empty-state"><i class="fas fa-inbox"></i><p>No analyses found</p></div>';
      return;
    }

    analysesList.innerHTML = analyses.map(analysis => {
      const shortText = analysis.text.length > 50 ? analysis.text.substring(0, 50) + "..." : analysis.text;
      const date = new Date(analysis.timestamp).toLocaleString();
      const confidence = Math.round((analysis.confidence || 0) * 100);
      
      return `
        <div class="table-row">
          <div>#${analysis.id}</div>
          <div title="${analysis.text}">${shortText}</div>
          <div>
            <span class="badge badge-user">${analysis.sentiment}</span>
          </div>
          <div>${confidence}%</div>
          <div>${analysis.username || 'Unknown'}</div>
          <div style="font-size: 0.85rem;">${date}</div>
          <div class="action-buttons">
            <button class="btn btn-sm btn-danger" onclick="deleteAnalysis(${analysis.id})" title="Delete">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </div>
      `;
    }).join('');
  } catch (error) {
    console.error("Error loading analyses:", error);
    analysesList.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load analyses</p></div>';
  }
}

// Display sentiment statistics
function displaySentimentStats(sentiments) {
  const chart = document.getElementById("sentimentChart");
  
  const sentimentEmojis = {
    happiness: "😊",
    sadness: "😢",
    anger: "😠",
    fear: "😨",
    surprise: "😲",
    disgust: "🤢",
    neutral: "😐"
  };
  
  const sentimentLabels = {
    happiness: "Happiness",
    sadness: "Sadness",
    anger: "Anger",
    fear: "Fear",
    surprise: "Surprise",
    disgust: "Disgust",
    neutral: "Neutral"
  };
  
  if (!sentiments || Object.keys(sentiments).length === 0) {
    chart.innerHTML = '<div class="empty-state"><i class="fas fa-inbox"></i><p>No sentiment data</p></div>';
    return;
  }
  
  chart.innerHTML = Object.entries(sentiments).map(([sentiment, count]) => `
    <div class="sentiment-chart-item">
      <div style="font-size: 2rem; margin-bottom: var(--spacing-xs);">${sentimentEmojis[sentiment] || "😐"}</div>
      <div class="sentiment-chart-value">${count}</div>
      <div class="sentiment-chart-label">${sentimentLabels[sentiment] || sentiment}</div>
    </div>
  `).join('');
}

// Setup tabs
function setupTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");
  
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.dataset.tab;
      
      // Remove active class from all
      tabButtons.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.remove("active"));
      
      // Add active class to clicked
      btn.classList.add("active");
      document.getElementById(`${targetTab}Tab`).classList.add("active");
    });
  });
}

// Setup logout
function setupLogout() {
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      if (confirm("Are you sure you want to logout?")) {
        localStorage.removeItem("token");
        window.location.href = "/login";
      }
    });
  }
}

// User management functions
async function toggleUserRole(userId, currentRole) {
  if (!confirm(`Change user role from ${currentRole} to ${currentRole === 'admin' ? 'user' : 'admin'}?`)) {
    return;
  }
  
  const newRole = currentRole === 'admin' ? 'user' : 'admin';
  const token = localStorage.getItem("token");
  
  showLoading();
  
  try {
    const response = await fetch(`${API_BASE}/users/${userId}/role?role=${newRole}`, {
      method: "PUT",
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });
    
    const data = await response.json();
    
    if (response.ok) {
      alert(`✅ User role updated to ${newRole}`);
      await loadUsers();
    } else {
      alert(`❌ ${data.detail || "Failed to update role"}`);
    }
  } catch (error) {
    alert("❌ Error updating user role");
  } finally {
    hideLoading();
  }
}

async function toggleUserStatus(userId, currentStatus) {
  const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
  const action = newStatus === 'active' ? 'activate' : 'deactivate';
  
  if (!confirm(`Are you sure you want to ${action} this user?`)) {
    return;
  }
  
  const token = localStorage.getItem("token");
  
  showLoading();
  
  try {
    const response = await fetch(`${API_BASE}/users/${userId}/status?status=${newStatus}`, {
      method: "PUT",
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });
    
    const data = await response.json();
    
    if (response.ok) {
      alert(`✅ User ${action}d successfully`);
      await loadUsers();
      await loadDashboard(); // Refresh stats
    } else {
      alert(`❌ ${data.detail || "Failed to update status"}`);
    }
  } catch (error) {
    alert("❌ Error updating user status");
  } finally {
    hideLoading();
  }
}

async function deleteUser(userId, username) {
  if (!confirm(`⚠️ Are you sure you want to delete user "${username}"?\n\nThis will also delete all their analyses!`)) {
    return;
  }
  
  const token = localStorage.getItem("token");
  
  showLoading();
  
  try {
    const response = await fetch(`${API_BASE}/users/${userId}`, {
      method: "DELETE",
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });
    
    const data = await response.json();
    
    if (response.ok) {
      alert(`✅ User deleted successfully`);
      await loadUsers();
      await loadDashboard(); // Refresh stats
    } else {
      alert(`❌ ${data.detail || "Failed to delete user"}`);
    }
  } catch (error) {
    alert("❌ Error deleting user");
  } finally {
    hideLoading();
  }
}

async function deleteAnalysis(analysisId) {
  if (!confirm("Are you sure you want to delete this analysis?")) {
    return;
  }
  
  const token = localStorage.getItem("token");
  
  showLoading();
  
  try {
    const response = await fetch(`${API_BASE}/analyses/${analysisId}`, {
      method: "DELETE",
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });
    
    const data = await response.json();
    
    if (response.ok) {
      alert(`✅ Analysis deleted successfully`);
      await loadAnalyses();
      await loadDashboard(); // Refresh stats
    } else {
      alert(`❌ ${data.detail || "Failed to delete analysis"}`);
    }
  } catch (error) {
    alert("❌ Error deleting analysis");
  } finally {
    hideLoading();
  }
}

async function viewUserDetails(userId) {
  const token = localStorage.getItem("token");
  
  showLoading();
  
  try {
    const response = await fetch(`${API_BASE}/users/${userId}`, {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });
    
    if (!response.ok) throw new Error("Failed to load user details");
    
    const user = await response.json();
    
    const details = `
User Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID: ${user.id}
Username: ${user.username}
Email: ${user.email}
Role: ${user.role}
Status: ${user.is_active}
Gender: ${user.gender}
Date of Birth: ${user.date}
Created: ${new Date(user.created_at).toLocaleString()}
Total Analyses: ${user.analyses_count}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    `;
    
    alert(details);
  } catch (error) {
    alert("❌ Error loading user details");
  } finally {
    hideLoading();
  }
}

// Utility functions
function showLoading() {
  document.getElementById("loadingOverlay").classList.add("active");
}

function hideLoading() {
  document.getElementById("loadingOverlay").classList.remove("active");
}

function showError(message) {
  alert(`❌ ${message}`);
}

// Make functions global for onclick handlers
window.toggleUserRole = toggleUserRole;
window.toggleUserStatus = toggleUserStatus;
window.deleteUser = deleteUser;
window.deleteAnalysis = deleteAnalysis;
window.viewUserDetails = viewUserDetails;

