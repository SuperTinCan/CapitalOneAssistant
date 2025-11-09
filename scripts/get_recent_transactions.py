import pandas as pd
from datetime import datetime

TRANSACTIONS_PATH = "data/transactions.csv"

def get_recent_transactions(user_id: str, n: int = 5):
    """
    Return the n most recent transactions for a specific user.
    """
    # load file
    df = pd.read_csv(TRANSACTIONS_PATH, parse_dates=["timestamp"], keep_default_na=False)

    # filter this user's transactions
    user_txns = df[df["user_id"] == user_id].copy()

    if user_txns.empty:
        print(f"No transactions found for {user_id}")
        return pd.DataFrame()

    # sort newest first
    user_txns = user_txns.sort_values("timestamp", ascending=False)

    # grab top n
    recent_txns = user_txns.head(n)

    # pretty-print summary
    print(f"Last {len(recent_txns)} transactions for {user_id}:")
    print(recent_txns[["txn_id", "timestamp", "amount", "merchant", "country"]])
    return recent_txns


TXN_PATH = "data/transactions.csv"
FRAUD_PATH = "data/fraud_scores.csv"

def get_recent_transactions_with_scores(user_id: str, n: int = 5):
    """
    Returns the n most recent transactions for a given user,
    joined with fraud_score and fraud_label from fraud_scores.csv.
    """
    # Load both files
    txns = pd.read_csv(TXN_PATH, parse_dates=["timestamp"], keep_default_na=False)
    scores = pd.read_csv(FRAUD_PATH)

    # Filter this user's transactions
    user_txns = txns[txns["user_id"] == user_id].copy()

    if user_txns.empty:
        print(f"No transactions found for {user_id}.")
        return pd.DataFrame()

    # Sort newest first
    user_txns = user_txns.sort_values("timestamp", ascending=False).head(n)

    # Merge fraud scores by txn_id
    merged = user_txns.merge(
        scores[["txn_id", "fraud_score", "fraud_label"]],
        on="txn_id",
        how="left"
    )

    # Fill NaNs if a txn_id has no fraud score yet
    merged["fraud_score"] = merged["fraud_score"].fillna(0.0)
    merged["fraud_label"] = merged["fraud_label"].fillna(0).astype(int)

    # Format a few numeric values nicely for printouts
    merged["fraud_score"] = merged["fraud_score"].round(3)
    merged["amount"] = merged["amount"].round(2)

    print(f"\nLast {len(merged)} transactions with fraud scores for {user_id}:")
    print(merged[["txn_id", "timestamp", "amount", "fraud_score", "fraud_label"]])
    return merged

# Example usage
if __name__ == "__main__":
    user = "user_001"   # change to active user
    df = get_recent_transactions_with_scores(user, n=5)

    user = "user_001"     # change to whichever user is active
    n = 5                 # how many recent transactions
    recent = get_recent_transactions(user, n)

