import pandas as pd

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

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
# SPENDING CLUSTERING
# ============================================================

def cluster_spending():

    df = load_transactions()

    expense_df = df[
        df["type"] == "expense"
    ].copy()

    if expense_df.empty:
        return []

    X = expense_df[["amount"]]

    # K-Means with 3 clusters requires at least 3 records
    if len(expense_df) < 3:
        return []

    # ========================================================
    # SCALE FEATURES
    # ========================================================

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)

    # ========================================================
    # K-MEANS
    # ========================================================

    n_clusters = min(
        3,
        len(expense_df)
    )

    model = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10
    )

    expense_df["cluster"] = model.fit_predict(
        X_scaled
    )

    # ========================================================
    # CLUSTER SUMMARY
    # ========================================================

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
        .sort_values("mean")
    )

    # ========================================================
    # RETURN API-SAFE DATA
    # ========================================================

    clusters = []

    for cluster_id, row in cluster_summary.iterrows():

        clusters.append({
            "cluster": int(cluster_id),
            "count": int(row["count"]),
            "mean": float(row["mean"]),
            "min": float(row["min"]),
            "max": float(row["max"])
        })

    return clusters


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    clusters = cluster_spending()

    print(
        "========== SPENDING BEHAVIOR CLUSTERING =========="
    )

    print("\nCluster Summary:")

    for cluster in clusters:
        print(cluster)

    print(
        "\nSpending clustering completed successfully!"
    )