# FinSight AI

AI-powered personal finance analytics platform built with React, Flask, PostgreSQL, and machine learning.

FinSight AI transforms transaction data into financial insights through interactive analytics, anomaly detection, expense forecasting, spending clustering, and an AI-powered financial question-answering system.

## Live Demo

Frontend: https://fin-sight-ai-ten-mu.vercel.app/

Backend API: https://finsight-ai-2inl.onrender.com/

Health Check: https://finsight-ai-2inl.onrender.com/api/health

## Features

- Financial dashboard with income, expenses, savings, and savings rate
- Transaction management and transaction data visualization
- Spending analysis by category
- Monthly expense analysis
- Anomaly detection using Isolation Forest
- Expense forecasting using Linear Regression
- Spending pattern clustering using K-Means
- CSV transaction upload
- AI financial question answering
- PostgreSQL database support
- SQLite support for local development
- REST API built with Flask
- Responsive React frontend
- Cloud deployment using Vercel and Render

## Machine Learning

### Anomaly Detection

Uses Isolation Forest to identify unusual spending transactions.

### Expense Forecasting

Uses Linear Regression on historical monthly expenses to estimate the next month's spending.

### Spending Clustering

Uses StandardScaler and K-Means clustering to group transactions according to spending amount patterns.

## AI Assistant

The FinSight AI assistant can answer questions about:

- Total income
- Total expenses
- Total savings
- Savings rate
- Spending by category
- Monthly spending
- Largest transactions

When running locally, FinSight AI can use the Qwen3 8B model through Ollama.

The deployed cloud version uses database-based financial question answering.

## Tech Stack

### Frontend

- React
- Vite
- Recharts
- JavaScript
- CSS

### Backend

- Python
- Flask
- Flask-CORS
- Gunicorn

### Data & Machine Learning

- Pandas
- NumPy
- Scikit-learn

### Database

- SQLite
- PostgreSQL
- psycopg2

### AI

- Ollama
- Qwen3 8B

### Deployment

- Vercel
- Render

## Project Structure

```text
FinSight-AI/
│
├── backend/
│   ├── app.py
│   └── requirements.txt
│
├── data/
│   └── transactions.csv
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── models/
│
├── notebooks/
│
├── src/
│   ├── database.py
│   ├── analytics.py
│   ├── anomaly_detection.py
│   ├── expense_forecasting.py
│   ├── spending_clustering.py
│   └── ai_assistant.py
│
├── .python-version
├── .gitignore
└── Procfile