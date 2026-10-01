import os
import pandas as pd
import ollama

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

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    return df


# ============================================================
# CLOUD QUESTION ANSWERING
# ============================================================

def answer_cloud_question(question):
    df = load_transactions()

    income_df = df[df["type"] == "income"].copy()
    expense_df = df[df["type"] == "expense"].copy()

    total_income = income_df["amount"].sum()
    total_expenses = expense_df["amount"].sum()
    total_savings = total_income - total_expenses

    savings_rate = (
        (total_savings / total_income) * 100
        if total_income > 0
        else 0
    )

    category_expenses = (
        expense_df
        .groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    monthly_expenses = (
        expense_df
        .assign(month=expense_df["date"].dt.to_period("M").astype(str))
        .groupby("month")["amount"]
        .sum()
    )

    largest_transaction = expense_df.loc[
        expense_df["amount"].idxmax()
    ]

    q = question.lower().strip()

    # --------------------------------------------------------
    # TOTAL SPENDING
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "total spending",
            "total spent",
            "total expense",
            "total expenses",
            "how much did i spend",
            "how much have i spent"
        ]
    ):
        return (
            f"Your total spending is "
            f"₹{total_expenses:,.2f}."
        )

    # --------------------------------------------------------
    # TOTAL INCOME
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "total income",
            "my income",
            "how much did i earn",
            "how much have i earned"
        ]
    ):
        return (
            f"Your total income is "
            f"₹{total_income:,.2f}."
        )

    # --------------------------------------------------------
    # SAVINGS
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "total savings",
            "my savings",
            "how much did i save",
            "how much have i saved"
        ]
    ):
        return (
            f"Your total savings are "
            f"₹{total_savings:,.2f}, "
            f"with a savings rate of "
            f"{savings_rate:.2f}%."
        )

    # --------------------------------------------------------
    # SAVINGS RATE
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "savings rate",
            "saving rate",
            "percentage saved"
        ]
    ):
        return (
            f"Your savings rate is "
            f"{savings_rate:.2f}%."
        )

    # --------------------------------------------------------
    # HIGHEST SPENDING CATEGORY
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "highest spending category",
            "highest expense category",
            "most expensive category",
            "where do i spend the most",
            "where am i spending the most"
        ]
    ):
        category = category_expenses.index[0]
        amount = category_expenses.iloc[0]

        return (
            f"Your highest spending category is "
            f"{category}, with spending of "
            f"₹{amount:,.2f}."
        )

    # --------------------------------------------------------
    # CATEGORY-SPECIFIC SPENDING
    # --------------------------------------------------------

    for category in category_expenses.index:

        if category.lower() in q:

            amount = category_expenses[category]

            return (
                f"You spent "
                f"₹{amount:,.2f} on "
                f"{category}."
            )

    # --------------------------------------------------------
    # LARGEST TRANSACTION
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "largest transaction",
            "biggest transaction",
            "highest transaction",
            "most expensive transaction"
        ]
    ):
        return (
            f"Your largest expense was "
            f"{largest_transaction['description']} "
            f"for ₹{largest_transaction['amount']:,.2f} "
            f"in the {largest_transaction['category']} category."
        )

    # --------------------------------------------------------
    # MONTHLY SPENDING
    # --------------------------------------------------------

    for month in monthly_expenses.index:

        month_name = pd.to_datetime(
            month
        ).strftime("%B").lower()

        if month_name in q or month in q:

            amount = monthly_expenses[month]

            return (
                f"Your total spending in "
                f"{pd.to_datetime(month).strftime('%B %Y')} "
                f"was ₹{amount:,.2f}."
            )

    # --------------------------------------------------------
    # DEFAULT CLOUD RESPONSE
    # --------------------------------------------------------

    return (
        "I can answer questions about your "
        "total income, total spending, savings, "
        "savings rate, spending categories, "
        "monthly expenses, and largest transactions."
    )


# ============================================================
# FINANCIAL CONTEXT FOR LOCAL AI
# ============================================================

def build_financial_context():

    df = load_transactions()

    income_df = df[df["type"] == "income"].copy()
    expense_df = df[df["type"] == "expense"].copy()

    total_income = income_df["amount"].sum()
    total_expenses = expense_df["amount"].sum()
    total_savings = total_income - total_expenses

    savings_rate = (
        (total_savings / total_income) * 100
        if total_income > 0
        else 0
    )

    category_expenses = (
        expense_df
        .groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    monthly_expenses = (
        expense_df
        .assign(month=expense_df["date"].dt.to_period("M").astype(str))
        .groupby("month")["amount"]
        .sum()
    )

    category_text = "\n".join(
        f"{category}: ₹{amount:,.2f}"
        for category, amount in category_expenses.items()
    )

    monthly_text = "\n".join(
        f"{month}: ₹{amount:,.2f}"
        for month, amount in monthly_expenses.items()
    )

    transactions = expense_df[
        [
            "date",
            "description",
            "category",
            "type",
            "amount",
            "payment_method"
        ]
    ].copy()

    transactions["date"] = transactions["date"].dt.strftime(
        "%Y-%m-%d"
    )

    transactions["amount"] = transactions["amount"].map(
        lambda x: f"₹{x:,.2f}"
    )

    transaction_text = transactions.to_string(index=False)

    return f"""
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

{transaction_text}
"""


# ============================================================
# LOCAL QWEN3
# ============================================================

def ask_ai(question):

    cloud_mode = (
        os.getenv(
            "CLOUD_MODE",
            "false"
        ).lower() == "true"
    )

    # Cloud deployment
    if cloud_mode:
        return answer_cloud_question(question)

    # Local Qwen3
    financial_context = build_financial_context()

    prompt = f"""
You are FinSight AI, a personal finance
analysis assistant.

Answer using ONLY the financial data below.

Do not invent information.

Keep the answer concise and informative.

When mentioning money, use Indian Rupee
formatting such as ₹18,000.

FINANCIAL DATA:

{financial_context}

USER QUESTION:

{question}

Answer the user's question.
"""

    response = ollama.chat(
        model="qwen3:8b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]


# ============================================================
# API FUNCTION
# ============================================================

def ask_question(question):
    return ask_ai(question)