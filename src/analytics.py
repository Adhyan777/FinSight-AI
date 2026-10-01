import pandas as pd
from database import get_connection


# ============================================================
# LOAD TRANSACTIONS FROM DATABASE
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

    # ========================================================
    # PREPARE DATA
    # ========================================================

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
# MAIN ANALYTICS FUNCTION
# ============================================================

def get_analytics():

    df = load_transactions()

    # ========================================================
    # SEPARATE INCOME AND EXPENSES
    # ========================================================

    income_df = df[
        df["type"] == "income"
    ]

    expense_df = df[
        df["type"] == "expense"
    ]

    # ========================================================
    # CORE FINANCIAL METRICS
    # ========================================================

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

    # ========================================================
    # MONTHLY EXPENSES
    # ========================================================

    monthly_expenses = (
        expense_df
        .assign(
            month=(
                expense_df["date"]
                .dt.to_period("M")
                .astype(str)
            )
        )
        .groupby("month")["amount"]
        .sum()
    )

    # ========================================================
    # CATEGORY EXPENSES
    # ========================================================

    category_expenses = (
        expense_df
        .groupby("category")["amount"]
        .sum()
        .sort_values(
            ascending=False
        )
    )

    # ========================================================
    # HIGHEST SPENDING CATEGORY
    # ========================================================

    if not category_expenses.empty:

        highest_category = (
            category_expenses.index[0]
        )

        highest_category_amount = (
            category_expenses.iloc[0]
        )

    else:

        highest_category = None
        highest_category_amount = 0

    # ========================================================
    # LARGEST TRANSACTION
    # ========================================================

    if not expense_df.empty:

        largest_transaction = (
            expense_df.loc[
                expense_df["amount"].idxmax()
            ]
        )

        largest_transaction_data = {
            "description": str(
                largest_transaction["description"]
            ),
            "amount": float(
                largest_transaction["amount"]
            ),
            "category": str(
                largest_transaction["category"]
            )
        }

    else:

        largest_transaction_data = {
            "description": None,
            "amount": 0,
            "category": None
        }

    # ========================================================
    # RETURN API-SAFE DATA
    # ========================================================

    return {
        "total_income": float(total_income),
        "total_expenses": float(total_expenses),
        "total_savings": float(total_savings),
        "savings_rate": float(savings_rate),

        "monthly_expenses": [
            {
                "month": str(month),
                "amount": float(amount)
            }
            for month, amount
            in monthly_expenses.items()
        ],

        "category_expenses": [
            {
                "category": str(category),
                "amount": float(amount)
            }
            for category, amount
            in category_expenses.items()
        ],

        "highest_category": highest_category,
        "highest_category_amount": float(
            highest_category_amount
        ),

        "largest_transaction":
            largest_transaction_data
    }


# ============================================================
# LOCAL DISPLAY / TEST
# ============================================================

if __name__ == "__main__":

    analytics = get_analytics()

    print(
        "========== FINANCIAL ANALYTICS =========="
    )

    print(
        f"Total Income: "
        f"₹{analytics['total_income']:,.2f}"
    )

    print(
        f"Total Expenses: "
        f"₹{analytics['total_expenses']:,.2f}"
    )

    print(
        f"Total Savings: "
        f"₹{analytics['total_savings']:,.2f}"
    )

    print(
        f"Savings Rate: "
        f"{analytics['savings_rate']:.2f}%"
    )

    print(
        "\n========== MONTHLY EXPENSES =========="
    )

    print(
        analytics["monthly_expenses"]
    )

    print(
        "\n========== CATEGORY EXPENSES =========="
    )

    print(
        analytics["category_expenses"]
    )

    print(
        "\n========== HIGHEST SPENDING CATEGORY =========="
    )

    print(
        f"Category: "
        f"{analytics['highest_category']}"
    )

    print(
        f"Amount: "
        f"₹{analytics['highest_category_amount']:,.2f}"
    )

    print(
        "\n========== LARGEST EXPENSE TRANSACTION =========="
    )

    print(
        f"Description: "
        f"{analytics['largest_transaction']['description']}"
    )

    print(
        f"Amount: "
        f"₹{analytics['largest_transaction']['amount']:,.2f}"
    )

    print(
        f"Category: "
        f"{analytics['largest_transaction']['category']}"
    )

    print(
        "\nAnalytics engine completed successfully!"
    )