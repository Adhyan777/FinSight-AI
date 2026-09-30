import pandas as pd

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

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
# FEATURES
# ============================================================

X = expense_df[
    ["amount"]
]


# ============================================================
# SCALE FEATURES
# ============================================================

scaler = StandardScaler()

X_scaled = scaler.fit_transform(
    X
)


# ============================================================
# K-MEANS CLUSTERING
# ============================================================

model = KMeans(
    n_clusters=3,
    random_state=42,
    n_init=10
)


expense_df["cluster"] = (
    model.fit_predict(
        X_scaled
    )
)


# ============================================================
# CLUSTER SUMMARY
# ============================================================

cluster_summary = (
    expense_df
    .groupby("cluster")["amount"]
    .agg(
        [
            "count",
            "mean",
            "min",
            "max"
        ]
    )
    .sort_values(
        "mean"
    )
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print(
    "========== SPENDING BEHAVIOR CLUSTERING =========="
)

print(
    "\nCluster Summary:"
)

print(
    cluster_summary
)


print(
    "\n========== TRANSACTIONS WITH CLUSTERS =========="
)

print(
    expense_df[
        [
            "date",
            "description",
            "category",
            "amount",
            "cluster"
        ]
    ].to_string(
        index=False
    )
)


print(
    "\nSpending clustering completed successfully!"
)