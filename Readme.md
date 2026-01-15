<h1 align="center">🏎️ F1 Analytics Hub</h1>
<p align="center">
<strong>An AI-Driven Prediction Engine & Performance Insights Dashboard</strong>
</p>

<p align="center">
<img src="https://www.google.com/search?q=https://img.shields.io/badge/Data_Science-F1_Analytics-red%3Fstyle%3Dfor-the-badge%26logo%3Dformula1" alt="F1 Analytics">
<img src="https://www.google.com/search?q=https://img.shields.io/badge/Frontend-React_|_Vite-blue?style=for-the-badge&logo=react" alt="React">
<img src="https://www.google.com/search?q=https://img.shields.io/badge/Backend-FastAPI-009688%3Fstyle%3Dfor-the-badge%26logo%3Dfastapi%26logoColor%3Dwhite" alt="FastAPI">
<img src="https://www.google.com/search?q=https://img.shields.io/badge/ML-Random_Forest-F7931E%3Fstyle%3Dfor-the-badge%26logo%3Dscikitlearn%26logoColor%3Dwhite" alt="ML">
</p>

<br />

📖 Project Overview

This platform bridges the gap between raw F1 telemetry and actionable insights. It provides a Machine Learning Prediction Engine and a Data Analysis Dashboard in a unified interface, analyzing historical performance data from 2018 to 2024.

💡 The Technical Evolution

Originally a static HTML/JS project, this was migrated to React (Vite) to solve specific engineering challenges:

Declarative State: To sync the Race Calendar dynamically based on the selected Season.

Unified UX: To embed the Streamlit Analytics dashboard via an iframe, allowing users to stay within a single-page application.

Stability: To handle long-running data fetches (FastF1 API) without UI flickering or state resets.

🛠️ Technical Stack & Engineering Purpose

<table align="center">
<tr>
<th>Category</th>
<th>Tools</th>
<th>Implementation Detail</th>
</tr>
<tr>
<td><b>Data Engine</b></td>
<td><code>FastF1</code>, <code>Pandas</code>, <code>NumPy</code></td>
<td>Specialized telemetry extraction and rolling-window feature engineering.</td>
</tr>
<tr>
<td><b>Machine Learning</b></td>
<td><code>Scikit-learn</code></td>
<td><b>Random Forest Regressor</b> for non-linear grid-to-finish modeling.</td>
</tr>
<tr>
<td><b>Backend API</b></td>
<td><code>FastAPI</code>, <code>Uvicorn</code></td>
<td>Asynchronous service serving ML inference and historical segments.</td>
</tr>
<tr>
<td><b>Frontend UI</b></td>
<td><b>React (Vite)</b></td>
<td>SPA architecture with interactive tabbed navigation and TailwindCSS styling.</td>
</tr>
<tr>
<td><b>Analytics</b></td>
<td><code>Streamlit</code>, <code>Plotly</code></td>
<td>Embedded dashboard for deep-dive EDA and feature importance validation.</td>
</tr>
</table>

📈 Data Science Deep Dive

📊 Feature Weighting

Our model ranks inputs based on their predictive weight for the final finishing position:

Grid Position ($\approx 55\%$--$60\%$): The single most significant predictor of race success.

Constructor Form ($\approx 15\%$--$20\%$): Rolling 5-race performance of the car engineering.

Driver Form ($\approx 10\%$--$15\%$): Captures individual momentum and psychological consistency.

Weather Conditions ($< 5\%$): While high-impact, its rarity gives it a lower global statistical weight.

🏁 The "Perfect Model" Challenge

Mechanical Reliability: Defined based on Official Race Classification (completing $90\%$ of distance). This ensures a stable training target despite mechanical retirements.

Recent Form Logic: Instead of static IDs, we use rolling-average point metrics to adapt to mid-season car upgrades and slumps.

🚦 Installation & Execution

🐳 The Docker Way (Full Stack)

Launch the Frontend, Backend API, and Analytics Dashboard with a single command:

docker-compose up --build


Main App (React): http://localhost:5173

Prediction API: http://localhost:8000

Analytics Dashboard: http://localhost:8501

🔧 Manual Setup

<details>
<summary><b>Python Services</b></summary>

pip install -r requirements.txt
python build_dataset.py       # Scrape Data
python train_model.py         # Train AI
uvicorn api:app --reload      # Start API
streamlit run analysis_app.py  # Start Analytics


</details>

<details>
<summary><b>React Frontend</b></summary>

cd frontend
npm install
npm run dev


</details>

☁️ Cloud Roadmap

I am currently deploying this to a cloud-native architecture:

Frontend: Vercel (Global Edge).

Backend: AWS EC2 (t3.micro) + Docker Compose.

Networking: Static Elastic IP with CORS-secured communication.

[Live Demo Link Coming Soon!]

<p align="center">
<b>Developed by 👨‍💻 Divyesh Kuchhadia</b><br />
<a href="https://www.linkedin.com/in/divyeshkuchhadia11/">LinkedIn</a> • <a href="https://github.com/Divu03">GitHub</a> • <a href="https://divyesh-k.web.app">Portfolio</a>
</p>