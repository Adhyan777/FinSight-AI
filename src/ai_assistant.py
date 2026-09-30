import os
import pandas as pd
import ollama

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
].copy()

expense_df = df[
    df["type"] == "expense"
].copy()


# ============================================================
# FINANCIAL SUMMARY
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
# CATEGORY SPENDING
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
# MONTHLY SPENDING
# ============================================================

expense_df["month"] = (
    expense_df["date"]
    .dt.to_period("M")
    .astype(str)
)

monthly_expenses = (
    expense_df
    .groupby("month")["amount"]
    .sum()
)


# ============================================================
# BUILD FINANCIAL CONTEXT
# ============================================================

def build_financial_context():

    category_text = "\n".join(
        [
            f"{category}: ₹{amount:,.2f}"

            for category, amount
            in category_expenses.items()
        ]
    )

    monthly_text = "\n".join(
        [
            f"{month}: ₹{amount:,.2f}"

            for month, amount
            in monthly_expenses.items()
        ]
    )

    transaction_text = expense_df[
        [
            "date",
            "description",
            "category",
            "type",
            "amount",
            "payment_method"
        ]
    ].copy()

    transaction_text["date"] = (
        transaction_text["date"]
        .dt.strftime("%Y-%m-%d")
    )

    transaction_text["amount"] = (
        transaction_text["amount"]
        .map(
            lambda x:
            f"₹{x:,.2f}"
        )
    )

    transactions = (
        transaction_text
        .to_string(
            index=False
        )
    )

    context = f"""
FinSight AI Financial Data

========== FINANCIAL SUMMARY ==========

Total Income:
₹{total_income:,.2f}

Total Expenses:
₹{total_expenses:,.2f}

Total Savings:
₹{total_savings:,.2f}

Savings Rate:
{savings_rate:.2f}%


========== SPENDING BY CATEGORY ==========

{category_text}


========== MONTHLY EXPENSES ==========

{monthly_text}


========== EXPENSE TRANSACTIONS ==========

{transactions}
"""

    return context


# ============================================================
# ASK AI
# ============================================================

def ask_ai(question):

    # --------------------------------------------------------
    # CHECK AI AVAILABILITY
    # --------------------------------------------------------

    cloud_mode = (
        os.getenv(
            "CLOUD_MODE",
            "false"
        ).lower() == "true"
    )

    if cloud_mode:

        return (
            "FinSight AI's local Qwen3 model is "
            "available when running FinSight AI locally. "
            "The cloud deployment currently provides "
            "the analytics and machine-learning features."
        )


    # --------------------------------------------------------
    # BUILD CONTEXT
    # --------------------------------------------------------

    financial_context = (
        build_financial_context()
    )


    # --------------------------------------------------------
    # AI PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are FinSight AI, a personal finance
analysis assistant.

Your job is to answer questions using ONLY
the financial data provided below.

IMPORTANT RULES:

1. Do not invent financial information.

2. Do not assume transactions that are
   not present.

3. Use transaction-level data when the
   question requires specific transactions.

4. Use category and monthly summaries when
   they are sufficient.

5. If the requested information is not
   available, clearly say that it is not
   available in the data.

6. Perform calculations carefully when
   necessary.

7. Keep responses concise but informative.

8. When mentioning money, use Indian
   Rupee formatting such as ₹18,000.

9. Do not give generic financial advice
   unless the user specifically asks
   for advice.

FINANCIAL DATA:

{financial_context}

USER QUESTION:

{question}

Answer the user's question using the
financial data above.
"""


    # --------------------------------------------------------
    # LOCAL QWEN3
    # --------------------------------------------------------

    response = ollama.chat(

        model="qwen3:8b",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]

    )

    return response[
        "message"
    ][
        "content"
    ]