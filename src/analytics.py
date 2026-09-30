import pandas as pd
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
# SEPARATE INCOME AND EXPENSES
# ============================================================

income_df = df[
    df["type"] == "income"
]

expense_df = df[
    df["type"] == "expense"
]


# ============================================================
# CORE FINANCIAL METRICS
# ============================================================

total_income = income_df["amount"].sum()

total_expenses = expense_df["amount"].sum()

total_savings = (
    total_income - total_expenses
)

savings_rate = (
    (total_savings / total_income) * 100
    if total_income > 0
    else 0
)


# ============================================================
# MONTHLY EXPENSES
# ============================================================

monthly_expenses = (
    expense_df
    .assign(
        month=
        expense_df["date"]
        .dt.to_period("M")
        .astype(str)
    )
    .groupby("month")["amount"]
    .sum()
)


# ============================================================
# CATEGORY EXPENSES
# ============================================================

category_expenses = (
    expense_df
    .groupby("category")["amount"]
    .sum()
    .sort_values(
        ascending=False
    )
)


# ============================================================
# HIGHEST SPENDING CATEGORY
# ============================================================

highest_category = (
    category_expenses.index[0]
)

highest_category_amount = (
    category_expenses.iloc[0]
)


# ============================================================
# LARGEST TRANSACTION
# ============================================================

largest_transaction = (
    expense_df.loc[
        expense_df["amount"].idxmax()
    ]
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print(
    "========== FINANCIAL ANALYTICS =========="
)

print(
    f"Total Income: ₹{total_income:,.2f}"
)

print(
    f"Total Expenses: ₹{total_expenses:,.2f}"
)

print(
    f"Total Savings: ₹{total_savings:,.2f}"
)

print(
    f"Savings Rate: {savings_rate:.2f}%"
)

print(
    "\n========== MONTHLY EXPENSES =========="
)

print(monthly_expenses)

print(
    "\n========== CATEGORY EXPENSES =========="
)

print(category_expenses)

print(
    "\n========== HIGHEST SPENDING CATEGORY =========="
)

print(
    f"Category: {highest_category}"
)

print(
    f"Amount: ₹{highest_category_amount:,.2f}"
)

print(
    "\n========== LARGEST EXPENSE TRANSACTION =========="
)

print(
    f"Description: "
    f"{largest_transaction['description']}"
)

print(
    f"Amount: "
    f"₹{largest_transaction['amount']:,.2f}"
)

print(
    f"Category: "
    f"{largest_transaction['category']}"
)

print(
    "\nAnalytics engine completed successfully!"
)