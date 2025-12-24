document.getElementById("registerForm").addEventListener("submit", async function (e) {
  e.preventDefault();

  const btn = this.querySelector("button[type='submit']");
  const originalText = btn.innerHTML;

  // استرجاع البيانات
  const username = document.getElementById("username").value.trim();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();
  const date = document.getElementById("date").value;
  const gender = document.getElementById("gender").value;

  // تحقق بسيط من المدخلات
  if (!username || !email || !password || !date || !gender) {
    alert("⚠️ Please fill in all fields.");
    return;
  }

  // التحقق من صحة البريد الإلكتروني
  const emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
  if (!emailPattern.test(email)) {
    alert("⚠️ Please enter a valid email address.");
    return;
  }

  // التحقق من قوة كلمة المرور
  if (password.length < 6) {
    alert("⚠️ Password must be at least 6 characters long.");
    return;
  }

  // عرض التحميل
  btn.disabled = true;
  btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Creating Account...`;

  try {
    const response = await fetch("/auth/register", {
      method: "POST",
      headers: { 
        "Content-Type": "application/json" 
      },
      body: JSON.stringify({ username, email, password, date, gender })
    });

    const result = await response.json();

    if (response.ok) {
      btn.innerHTML = `<i class="fas fa-check"></i> Success! Redirecting...`;
      setTimeout(() => {
        window.location.href = "/login";
      }, 1000);
    } else {
      alert("❌ " + (result.detail || "Registration failed. Please try again."));
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
  } catch (error) {
    console.error("Registration error:", error);
    alert("❌ Network error. Please check your connection and try again.");
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
});
