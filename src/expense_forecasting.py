import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression

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
# CREATE MONTH COLUMN
# ============================================================

expense_df["month"] = (
    expense_df["date"]
    .dt.to_period("M")
    .astype(str)
)


# ============================================================
# MONTHLY EXPENSES
# ============================================================

monthly_expenses = (
    expense_df
    .groupby("month")["amount"]
    .sum()
    .reset_index()
)


# ============================================================
# CREATE NUMERIC MONTH INDEX
# ============================================================

monthly_expenses["month_index"] = (
    np.arange(
        len(monthly_expenses)
    )
)


# ============================================================
# TRAIN FORECASTING MODEL
# ============================================================

X = monthly_expenses[
    ["month_index"]
]

y = monthly_expenses[
    "amount"
]


model = LinearRegression()

model.fit(
    X,
    y
)


# ============================================================
# PREDICT NEXT MONTH
# ============================================================

next_month_index = (
    len(monthly_expenses)
)


predicted_expense = (
    model.predict(
        [[next_month_index]]
    )[0]
)


predicted_expense = max(
    0,
    predicted_expense
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print(
    "========== EXPENSE FORECASTING =========="
)

print(
    "\nHistorical Monthly Expenses:"
)

print(
    monthly_expenses[
        [
            "month",
            "amount"
        ]
    ]
)


print(
    "\nNext Month Expense Forecast:"
)

print(
    f"Predicted Expense: "
    f"₹{predicted_expense:,.2f}"
)


print(
    "\nForecasting model trained successfully!"
)