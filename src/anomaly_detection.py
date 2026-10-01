import pandas as pd
from sklearn.ensemble import IsolationForest

from database import get_connection


# ============================================================
# LOAD TRANSACTIONS
# ============================================================

def load_transactions():

    connection = get_connection()

    try:
        df = pd.read_sql_query(
            """
            SELECT
                date,
                description,
                category,
                type,
                amount,
                payment_method
            FROM transactions
            """,
            connection
        )
    finally:
        connection.close()

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    )

    return df


# ============================================================
# ANOMALY DETECTION
# ============================================================

def detect_anomalies():

    df = load_transactions()

    expense_df = df[
        df["type"] == "expense"
    ].copy()

    if expense_df.empty:
        return []

    X = expense_df[["amount"]]

    # Need enough transactions for Isolation Forest
    if len(expense_df) < 5:
        return []

    model = IsolationForest(
        contamination=0.05,
        random_state=42
    )

    expense_df["anomaly"] = model.fit_predict(X)

    anomalies = expense_df[
        expense_df["anomaly"] == -1
    ].copy()

    results = []

    for _, row in anomalies.iterrows():

        results.append({
            "date": (
                row["date"].strftime("%Y-%m-%d")
                if pd.notna(row["date"])
                else None
            ),
            "description": str(
                row["description"]
            ),
            "category": str(
                row["category"]
            ),
            "amount": float(
                row["amount"]
            ),
            "payment_method": str(
                row["payment_method"]
            )
        })

    return results


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    anomalies = detect_anomalies()

    print(
        "========== ANOMALY DETECTION =========="
    )

    print(
        f"Anomalies detected: {len(anomalies)}"
    )

    if anomalies:
        print("\nAnomalous Transactions:")

        for anomaly in anomalies:
            print(anomaly)

    else:
        print(
            "No unusual transactions detected."
        )

    print(
        "\nAnomaly detection completed successfully!"
    )