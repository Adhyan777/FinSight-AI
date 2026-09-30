from flask import Flask, jsonify, request
import sys
import os
import importlib
import pandas as pd

# ============================================================
# PYTHON PATH
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

SRC_PATH = os.path.join(
    PROJECT_ROOT,
    "src"
)

sys.path.append(SRC_PATH)


# ============================================================
# IMPORT MODULES
# ============================================================

import analytics
import anomaly_detection
import expense_forecasting
import spending_clustering
import ai_assistant

from database import (
    initialize_database,
    import_csv_if_database_empty,
    replace_transactions,
    get_transactions
)


# ============================================================
# APP
# ============================================================

app = Flask(__name__)

app.config["CLOUD_MODE"] = (
    os.getenv("CLOUD_MODE", "false").lower() == "true"
)


# ============================================================
# DATA PATH
# ============================================================

DATA_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "transactions.csv"
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

initialize_database()

import_csv_if_database_empty(
    DATA_PATH
)


# ============================================================
# CORS
# ============================================================

@app.after_request
def add_cors_headers(response):

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = (
        "GET, POST, OPTIONS"
    )

    return response


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return {
        "message": "FinSight AI backend is running"
    }


# ============================================================
# ANALYTICS
# ============================================================

@app.route("/api/analytics")
def get_analytics():

    return jsonify({

        "total_income":
            float(analytics.total_income),

        "total_expenses":
            float(analytics.total_expenses),

        "total_savings":
            float(analytics.total_savings),

        "savings_rate":
            float(
                round(
                    analytics.savings_rate,
                    2
                )
            ),

        "monthly_expenses": {

            str(month): float(amount)

            for month, amount
            in analytics.monthly_expenses.items()

        },

        "category_expenses": {

            str(category): float(amount)

            for category, amount
            in analytics.category_expenses.items()

        },

        "highest_spending_category": {

            "category":
                str(
                    analytics.highest_category
                ),

            "amount":
                float(
                    analytics.highest_category_amount
                )

        },

        "largest_transaction": {

            "description":
                str(
                    analytics.largest_transaction[
                        "description"
                    ]
                ),

            "amount":
                float(
                    analytics.largest_transaction[
                        "amount"
                    ]
                ),

            "category":
                str(
                    analytics.largest_transaction[
                        "category"
                    ]
                )

        }

    })


# ============================================================
# TRANSACTIONS
# ============================================================

@app.route("/api/transactions")
def api_transactions():

    return jsonify(
        get_transactions()
    )


# ============================================================
# ANOMALIES
# ============================================================

@app.route("/api/anomalies")
def get_anomalies():

    return jsonify([

        {
            "date":
                str(row["date"]),

            "description":
                str(row["description"]),

            "category":
                str(row["category"]),

            "amount":
                float(row["amount"]),

            "payment_method":
                str(row["payment_method"])

        }

        for _, row
        in anomaly_detection.anomalies.iterrows()

    ])


# ============================================================
# FORECAST
# ============================================================

@app.route("/api/forecast")
def get_forecast():

    return jsonify({

        "predicted_expense":
            float(
                round(
                    expense_forecasting.predicted_expense,
                    2
                )
            )

    })


# ============================================================
# CLUSTERS
# ============================================================

@app.route("/api/clusters")
def get_clusters():

    return jsonify({

        "summary": [

            {
                "cluster":
                    int(cluster),

                "count":
                    int(row["count"]),

                "mean":
                    float(row["mean"]),

                "min":
                    float(row["min"]),

                "max":
                    float(row["max"])

            }

            for cluster, row
            in spending_clustering.cluster_summary.iterrows()

        ],

        "transactions": [

            {
                "date":
                    str(row["date"]),

                "description":
                    str(row["description"]),

                "category":
                    str(row["category"]),

                "amount":
                    float(row["amount"]),

                "cluster":
                    int(row["cluster"])

            }

            for _, row
            in spending_clustering.expense_df.iterrows()

        ]

    })


# ============================================================
# AI FINANCIAL Q&A
# ============================================================

@app.route(
    "/api/ask",
    methods=["POST"]
)
def ask_financial_question():

    data = request.get_json()

    if not data or "question" not in data:

        return jsonify({
            "error": "Question is required."
        }), 400

    question = data["question"].strip()

    if not question:

        return jsonify({
            "error": "Question cannot be empty."
        }), 400

    try:

        answer = ai_assistant.ask_ai(
            question
        )

        return jsonify({

            "question":
                question,

            "answer":
                answer

        })

    except Exception as e:

        return jsonify({

            "error":
                "Unable to generate AI response.",

            "details":
                str(e)

        }), 500


# ============================================================
# CSV UPLOAD
# ============================================================

@app.route(
    "/api/upload",
    methods=["POST"]
)
def upload_transactions():

    if "file" not in request.files:

        return jsonify({
            "error":
                "No CSV file was uploaded."
        }), 400

    file = request.files["file"]

    if file.filename == "":

        return jsonify({
            "error":
                "No file was selected."
        }), 400

    if not file.filename.lower().endswith(".csv"):

        return jsonify({
            "error":
                "Only CSV files are supported."
        }), 400

    try:

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

            for column
            in required_columns

            if column not in uploaded_df.columns

        ]

        if missing_columns:

            return jsonify({

                "error":
                    "CSV is missing required columns.",

                "missing_columns":
                    missing_columns

            }), 400

        # ----------------------------------------------------
        # DATE VALIDATION
        # ----------------------------------------------------

        uploaded_df["date"] = pd.to_datetime(
            uploaded_df["date"],
            errors="coerce"
        )

        if uploaded_df["date"].isnull().any():

            return jsonify({

                "error":
                    "CSV contains invalid dates."

            }), 400

        # ----------------------------------------------------
        # AMOUNT VALIDATION
        # ----------------------------------------------------

        uploaded_df["amount"] = pd.to_numeric(
            uploaded_df["amount"],
            errors="coerce"
        )

        if uploaded_df["amount"].isnull().any():

            return jsonify({

                "error":
                    "CSV contains invalid amounts."

            }), 400

        # ----------------------------------------------------
        # TYPE VALIDATION
        # ----------------------------------------------------

        uploaded_df["type"] = (
            uploaded_df["type"]
            .astype(str)
            .str.lower()
        )

        valid_types = {
            "income",
            "expense"
        }

        invalid_types = (
            set(uploaded_df["type"])
            - valid_types
        )

        if invalid_types:

            return jsonify({

                "error":
                    "CSV contains invalid transaction types.",

                "invalid_types":
                    list(invalid_types)

            }), 400

        # ----------------------------------------------------
        # REMOVE DUPLICATES
        # ----------------------------------------------------

        uploaded_df = (
            uploaded_df
            .drop_duplicates()
            .copy()
        )

        # ----------------------------------------------------
        # NORMALIZE DATE
        # ----------------------------------------------------

        uploaded_df["date"] = (
            uploaded_df["date"]
            .dt.strftime("%Y-%m-%d")
        )

        # ----------------------------------------------------
        # SAVE CSV
        # ----------------------------------------------------

        uploaded_df.to_csv(
            DATA_PATH,
            index=False
        )

        # ----------------------------------------------------
        # SAVE TO SQLITE
        # ----------------------------------------------------

        replace_transactions(
            uploaded_df
        )

        # ----------------------------------------------------
        # REFRESH ANALYSIS
        # ----------------------------------------------------

        importlib.reload(
            analytics
        )

        importlib.reload(
            anomaly_detection
        )

        importlib.reload(
            expense_forecasting
        )

        importlib.reload(
            spending_clustering
        )

        importlib.reload(
            ai_assistant
        )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "message":
                "Transactions uploaded and database updated successfully.",

            "transactions":
                int(
                    len(uploaded_df)
                ),

            "columns":
                list(
                    uploaded_df.columns
                ),

            "database_updated":
                True,

            "analysis_refreshed":
                True

        })

    except Exception as e:

        return jsonify({

            "error":
                "Unable to process CSV file.",

            "details":
                str(e)

        }), 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )