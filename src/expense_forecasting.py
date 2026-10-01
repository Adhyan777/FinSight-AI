import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression

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
# EXPENSE FORECASTING
# ============================================================

def forecast_expenses():

    df = load_transactions()

    expense_df = df[
        df["type"] == "expense"
    ].copy()

    if expense_df.empty:
        return {
            "historical": [],
            "forecast": 0.0
        }

    expense_df["month"] = (
        expense_df["date"]
        .dt.to_period("M")
        .astype(str)
    )

    monthly_expenses = (
        expense_df
        .groupby("month")["amount"]
        .sum()
        .reset_index()
        .sort_values("month")
    )

    if len(monthly_expenses) == 0:
        return {
            "historical": [],
            "forecast": 0.0
        }

    # ========================================================
    # CREATE NUMERIC MONTH INDEX
    # ========================================================

    monthly_expenses["month_index"] = np.arange(
        len(monthly_expenses)
    )

    X = monthly_expenses[
        ["month_index"]
    ]

    y = monthly_expenses[
        "amount"
    ]

    # ========================================================
    # TRAIN MODEL
    # ========================================================

    if len(monthly_expenses) >= 2:

        model = LinearRegression()

        model.fit(X, y)

        next_month_index = len(
            monthly_expenses
        )

        predicted_expense = model.predict(
            [[next_month_index]]
        )[0]

    else:

        predicted_expense = (
            monthly_expenses["amount"].iloc[-1]
        )

    predicted_expense = max(
        0,
        float(predicted_expense)
    )

    # ========================================================
    # RETURN API-SAFE DATA
    # ========================================================

    historical = [
        {
            "month": str(row["month"]),
            "amount": float(row["amount"])
        }
        for _, row in monthly_expenses.iterrows()
    ]

    return {
        "historical": historical,
        "forecast": predicted_expense
    }


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    result = forecast_expenses()

    print(
        "========== EXPENSE FORECASTING =========="
    )

    print("\nHistorical Monthly Expenses:")

    for item in result["historical"]:
        print(item)

    print(
        "\nNext Month Expense Forecast:"
    )

    print(
        f"Predicted Expense: "
        f"₹{result['forecast']:,.2f}"
    )

    print(
        "\nForecasting model trained successfully!"
    )