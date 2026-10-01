from flask import Flask, jsonify, request
from flask_cors import CORS
from pathlib import Path
import sys
import importlib
import pandas as pd

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
DATA_PATH = BASE_DIR / "data" / "transactions.csv"

if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))


# ============================================================
# DATABASE
# ============================================================

from database import (
    initialize_database,
    import_csv_if_database_empty,
    replace_transactions,
    get_transactions,
)


# ============================================================
# DATABASE MUST BE INITIALIZED BEFORE ANALYTICS IMPORTS
# ============================================================

initialize_database()
import_csv_if_database_empty(DATA_PATH)


# ============================================================
# ANALYTICS / ML MODULES
# ============================================================

import analytics
import anomaly_detection
import expense_forecasting
import spending_clustering
import ai_assistant


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

# Allow the deployed Vercel frontend to communicate with Flask
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "https://fin-sight-ai-ten-mu.vercel.app"
            ]
        }
    }
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/")
def home():
    return jsonify({
        "message": "FinSight AI backend is running",
        "status": "success"
    })


@app.route("/api/health")
def health():
    return jsonify({
        "status": "healthy"
    })


# ============================================================
# ANALYTICS
# ============================================================

@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    try:
        result = analytics.get_analytics()

        if hasattr(result, "to_dict"):
            result = result.to_dict()

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# TRANSACTIONS
# ============================================================

@app.route("/api/transactions", methods=["GET"])
def transactions():
    try:
        data = get_transactions()

        return jsonify(data)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# ANOMALY DETECTION
# ============================================================

@app.route("/api/anomalies", methods=["GET"])
def anomalies():
    try:
        result = anomaly_detection.detect_anomalies()

        if hasattr(result, "to_dict"):
            result = result.to_dict(orient="records")

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# EXPENSE FORECAST
# ============================================================

@app.route("/api/forecast", methods=["GET"])
def forecast():
    try:
        result = expense_forecasting.forecast_expenses()

        if hasattr(result, "to_dict"):
            result = result.to_dict()

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# SPENDING CLUSTERS
# ============================================================

@app.route("/api/clusters", methods=["GET"])
def clusters():
    try:
        result = spending_clustering.cluster_spending()

        if hasattr(result, "to_dict"):
            result = result.to_dict(orient="records")

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# AI ASSISTANT
# ============================================================

@app.route("/api/ask", methods=["POST"])
def ask_ai():
    try:
        data = request.get_json(silent=True) or {}

        question = data.get("question", "").strip()

        if not question:
            return jsonify({
                "error": "Question is required"
            }), 400

        result = ai_assistant.ask_question(question)

        if isinstance(result, dict):
            return jsonify(result)

        return jsonify({
            "answer": result
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# CSV UPLOAD
# ============================================================

@app.route("/api/upload", methods=["POST"])
def upload_csv():
    try:
        if "file" not in request.files:
            return jsonify({
                "error": "No file uploaded"
            }), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({
                "error": "No file selected"
            }), 400

        if not file.filename.lower().endswith(".csv"):
            return jsonify({
                "error": "Only CSV files are supported"
            }), 400

        uploaded_df = pd.read_csv(file)

        required_columns = [
            "date",
            "description",
            "category",
            "type",
            "amount",
            "payment_method"
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in uploaded_df.columns
        ]

        if missing_columns:
            return jsonify({
                "error": "Missing required columns",
                "missing_columns": missing_columns
            }), 400

        uploaded_df["date"] = pd.to_datetime(
            uploaded_df["date"],
            errors="coerce"
        )

        if uploaded_df["date"].isna().any():
            return jsonify({
                "error": "Some dates in the CSV are invalid"
            }), 400

        uploaded_df["amount"] = pd.to_numeric(
            uploaded_df["amount"],
            errors="coerce"
        )

        if uploaded_df["amount"].isna().any():
            return jsonify({
                "error": "Some amounts in the CSV are invalid"
            }), 400

        uploaded_df["date"] = uploaded_df["date"].dt.strftime("%Y-%m-%d")

        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        uploaded_df.to_csv(DATA_PATH, index=False)

        replace_transactions(uploaded_df)

        importlib.reload(analytics)
        importlib.reload(anomaly_detection)
        importlib.reload(expense_forecasting)
        importlib.reload(spending_clustering)
        importlib.reload(ai_assistant)

        return jsonify({
            "message": "Transactions uploaded successfully.",
            "transactions": len(uploaded_df),
            "database_updated": True,
            "analysis_refreshed": True
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )