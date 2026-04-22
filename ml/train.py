import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import LabelEncoder
import pickle
from database.database import SessionLocal
from database.models import Customer, Transaction, SupportTicket

def load_data():
    """Load data from database and build features for ML model"""
    db = SessionLocal()
    try:
        customers = db.query(Customer).all()
        data = []
        for c in customers:
            # Count transactions
            total_transactions = len(c.transactions)
            total_spend = sum(t.amount for t in c.transactions)
            refund_count = sum(1 for t in c.transactions if t.status == "refunded")

            # Count support tickets
            total_tickets = len(c.tickets)
            high_priority_tickets = sum(1 for t in c.tickets
                                       if t.priority in ["high", "critical"])
            open_tickets = sum(1 for t in c.tickets
                              if t.status in ["open", "in_progress"])

            data.append({
                "plan":                  c.plan,
                "industry":              c.industry,
                "company_size":          c.company_size,
                "region":                c.region,
                "monthly_spend":         c.monthly_spend,
                "total_transactions":    total_transactions,
                "total_spend":           total_spend,
                "refund_count":          refund_count,
                "total_tickets":         total_tickets,
                "high_priority_tickets": high_priority_tickets,
                "open_tickets":          open_tickets,
                "churned":               c.churned
            })
        return pd.DataFrame(data)
    finally:
        db.close()

def train():
    print("Step 1/5: Loading data from database...")
    df = load_data()
    print(f"         Loaded {len(df)} customers")

    print("Step 2/5: Preparing features...")
    # Convert text columns to numbers
    le = LabelEncoder()
    for col in ["plan", "industry", "company_size", "region"]:
        df[col] = le.fit_transform(df[col])

    # Split features and target
    X = df.drop("churned", axis=1)
    y = df["churned"]

    print(f"         Features: {list(X.columns)}")
    print(f"         Churned: {y.sum()} | Active: {(y==0).sum()}")

    print("Step 3/5: Training model...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        random_state=42
    )
    model.fit(X_train, y_train)

    print("Step 4/5: Evaluating model...")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print("\n--- Model Performance ---")
    print(classification_report(y_test, y_pred))
    print(f"ROC-AUC Score: {roc_auc_score(y_test, y_prob):.3f}")

    # Feature importance
    importance = pd.DataFrame({
        "feature": X.columns,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False)
    print("\n--- Top Features ---")
    print(importance.head(5).to_string(index=False))

    print("\nStep 5/5: Saving model...")
    os.makedirs("ml/models", exist_ok=True)
    with open("ml/models/churn_model.pkl", "wb") as f:
        pickle.dump(model, f)

    # Save feature names so we can use them later
    with open("ml/models/feature_names.pkl", "wb") as f:
        pickle.dump(list(X.columns), f)

    print("         Model saved to ml/models/churn_model.pkl")
    print("\nPhase 2 complete! ML model is ready.")

if __name__ == "__main__":
    train()