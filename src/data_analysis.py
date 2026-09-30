import pandas as pd

# Load transaction data
df = pd.read_csv("data/transactions.csv")

print("========== ORIGINAL DATA ==========")
print(df.head())

# Convert date column to datetime
df["date"] = pd.to_datetime(df["date"])

# Make sure amount is numeric
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

# Check missing values
print("\n========== MISSING VALUES ==========")
print(df.isnull().sum())

# Check duplicate transactions
print("\n========== DUPLICATES ==========")
print("Duplicate rows:", df.duplicated().sum())

# Remove duplicate rows
df = df.drop_duplicates()

# Create a month column
df["month"] = df["date"].dt.to_period("M").astype(str)

# Separate income and expenses
income_df = df[df["type"] == "income"]
expense_df = df[df["type"] == "expense"]

print("\n========== DATASET SUMMARY ==========")
print("Total transactions:", len(df))
print("Total income:", income_df["amount"].sum())
print("Total expenses:", expense_df["amount"].sum())
print("Total savings:", income_df["amount"].sum() - expense_df["amount"].sum())

print("\n========== MONTHLY EXPENSES ==========")
monthly_expenses = expense_df.groupby("month")["amount"].sum()
print(monthly_expenses)

print("\n========== EXPENSE BY CATEGORY ==========")
category_expenses = expense_df.groupby("category")["amount"].sum()
print(category_expenses)

print("\n========== FINAL DATA ==========")
print(df.head())

print("\nData preprocessing completed successfully!")