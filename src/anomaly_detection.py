import pandas as pd
from sklearn.ensemble import IsolationForest

from database import get_connection


# ============================================================
# LOAD TRANSACTIONS FROM DATABASE
# ============================================================

connection = get_connection()

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

connection.close()


# ============================================================
# PREPARE DATA
# ============================================================

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)

df["amount"] = pd.to_numeric(
    df["amount"],
    errors="coerce"
)


# ============================================================
# EXPENSE TRANSACTIONS
# ============================================================

expense_df = df[
    df["type"] == "expense"
].copy()


# ============================================================
# ANOMALY DETECTION
# ============================================================

X = expense_df[
    ["amount"]
]


model = IsolationForest(
    contamination=0.05,
    random_state=42
)


model.fit(X)


expense_df["anomaly"] = (
    model.predict(X)
)


expense_df["is_anomaly"] = (
    expense_df["anomaly"] == -1
)


anomalies = expense_df[
    expense_df["is_anomaly"]
].copy()


# ============================================================
# DISPLAY RESULTS
# ============================================================

print(
    "========== ANOMALY DETECTION =========="
)

print(
    f"Total expense transactions: "
    f"{len(expense_df)}"
)

print(
    f"Anomalies detected: "
    f"{len(anomalies)}"
)

print(
    "\n========== ANOMALOUS TRANSACTIONS =========="
)


if len(anomalies) == 0:

    print(
        "No unusual transactions detected."
    )

else:

    print(
        anomalies[
            [
                "date",
                "description",
                "category",
                "amount",
                "payment_method"
            ]
        ].to_string(
            index=False
        )
    )


print(
    "\nAnomaly detection completed successfully!"
)