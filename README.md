# <div align="center">
   <img src="https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/fastapi.svg" alt="Sentiment Insight Logo" width="80" height="80" />
  
   <h1>Sentiment Insight</h1>
   <p><strong>Understand Feelings. Empower Decisions.</strong></p>
   <p>AI-powered Sentiment Analysis for Everyone</p>
  
   <img src="https://img.shields.io/badge/Framework-FastAPI-4F8EF7?style=for-the-badge&logo=fastapi" />
   <img src="https://img.shields.io/badge/Frontend-HTML/CSS/JS-6C63FF?style=for-the-badge&logo=html5" />
   <img src="https://img.shields.io/badge/Model-PyTorch-F7B801?style=for-the-badge&logo=pytorch" />
   <img src="https://img.shields.io/badge/License-MIT-22223B?style=for-the-badge" />
</div>

---

<details>
<summary><strong>Brand Identity</strong> (click to expand)</summary>

<ul>
   <li><strong>Project Name:</strong> Sentiment Insight</li>
   <li><strong>Tagline:</strong> Understand Feelings. Empower Decisions.</li>
   <li><strong>Colors:</strong>
      <ul>
         <li>Primary: <span style="color:#4F8EF7">#4F8EF7</span></li>
         <li>Secondary: <span style="color:#6C63FF">#6C63FF</span></li>
         <li>Accent: <span style="color:#F7B801">#F7B801</span></li>
         <li>Background: <span style="color:#F4F6FB">#F4F6FB</span></li>
         <li>Text: <span style="color:#22223B">#22223B</span></li>
      </ul>
   </li>
   <li><strong>Fonts:</strong> Poppins, Open Sans, Roboto</li>
   <li><strong>Logo:</strong> <em>Simple, modern, emotion-inspired (see above)</em></li>
</ul>

</details>

---

# Sentiment Analysis Project

## Overview

This is a **Sentiment Analysis Web Application** built with **FastAPI (Backend)** and a simple **HTML/CSS/JS Frontend**.
It allows users to input English text and get the **predicted sentiment** using a trained deep learning model (LSTM/BERT).

## Features

- 🔑 User Authentication (Login & Register)
- 📝 Sentiment Prediction (7 Categories: sadness, disappointment, anger, neutral, happiness, excitement, gratitude)
- 📊 History Tracking (stores past analyses)
- 🌐 Simple Web Interface
- 🗄️ Database Integration

## Project Structure

```
sentiment-analysis-project-Final
 ├── backend/        # FastAPI backend, routers, database, entry points
 ├── frontend/       # Static HTML, CSS, JS files
 ├── model/          # Sentiment analysis model files
 ├── tests/          # Unit and API tests
 ├── requirements.txt
 ├── README.md
 ├── .env            # Not included in repo
```

## Installation & Run

1. **Clone the repository**

   ```bash
   git clone https://github.com/D7oomyalasere/sentiment-analysis-project-Final.git
   cd sentiment-analysis-project-Final
   ```
2. **Create and activate virtual environment**

   ```bash
   python -m venv venv
   venv\Scripts\activate   # On Windows
   source venv/bin/activate # On Linux/Mac
   ```
3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```
4. **Run the server**

   ```bash
   uvicorn backend.main:app --reload
   ```
5. **Access the app**

   - API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - Frontend: [http://127.0.0.1:8000/static/front.html](http://127.0.0.1:8000/static/front.html)

---

## Notes

This project is still under development and can be improved with:

- Advanced frontend (React/Vue)
- Better model (Transformer-based like BERT)
- Deployment online (Heroku, Render, etc.)
* Deployment online (Heroku, Render, etc.).
