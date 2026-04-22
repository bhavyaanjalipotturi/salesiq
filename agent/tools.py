import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pickle
import pandas as pd
from langchain.tools import tool
from database.database import SessionLocal, engine
from database.models import Customer, Transaction, SupportTicket
from sqlalchemy import text


@tool
def query_database(sql_query: str) -> str:
    """
    Use this tool to query the sales database.
    The database has 3 tables:
    - customers (id, name, email, plan, industry, company_size, region, monthly_spend, churned)
    - transactions (id, customer_id, amount, product, status, created_at)
    - support_tickets (id, customer_id, subject, priority, status, created_at)
    Use standard SQL SELECT statements only.
    Example: SELECT plan, COUNT(*) as total FROM customers GROUP BY plan
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            rows = result.fetchall()
            columns = result.keys()
            if not rows:
                return "No results found."
            # Format as readable table
            output = " | ".join(columns) + "\n"
            output += "-" * 60 + "\n"
            for row in rows[:20]:  # limit to 20 rows
                output += " | ".join(str(v) for v in row) + "\n"
            if len(rows) > 20:
                output += f"... and {len(rows) - 20} more rows"
            return output
    except Exception as e:
        return f"Database error: {str(e)}"


@tool
def predict_churn(customer_name: str) -> str:
    """
    Use this tool to predict whether a specific customer is at risk of churning.
    Provide the customer's name or part of their name.
    Returns churn probability and risk level.
    """
    try:
        # Load model
        with open("ml/models/churn_model.pkl", "rb") as f:
            model = pickle.load(f)
        with open("ml/models/feature_names.pkl", "rb") as f:
            feature_names = pickle.load(f)

        db = SessionLocal()
        try:
            # Find customer
            customer = db.query(Customer).filter(
                Customer.name.ilike(f"%{customer_name}%")
            ).first()

            if not customer:
                return f"Customer '{customer_name}' not found in database."

            # Build features
            total_transactions = len(customer.transactions)
            total_spend = sum(t.amount for t in customer.transactions)
            refund_count = sum(1 for t in customer.transactions if t.status == "refunded")
            total_tickets = len(customer.tickets)
            high_priority_tickets = sum(1 for t in customer.tickets
                                       if t.priority in ["high", "critical"])
            open_tickets = sum(1 for t in customer.tickets
                              if t.status in ["open", "in_progress"])

            # Encode categorical features same way as training
            plan_map = {"basic": 0, "enterprise": 1, "pro": 2}
            size_map = {"large": 0, "medium": 1, "small": 2}
            region_map = {"asia_pacific": 0, "europe": 1, "latam": 2, "north_america": 3}
            industry_map = {"education": 0, "finance": 1, "healthcare": 2,
                           "logistics": 3, "retail": 4, "technology": 5}

            features = pd.DataFrame([{
                "plan":                  plan_map.get(customer.plan, 0),
                "industry":              industry_map.get(customer.industry, 0),
                "company_size":          size_map.get(customer.company_size, 0),
                "region":                region_map.get(customer.region, 0),
                "monthly_spend":         customer.monthly_spend,
                "total_transactions":    total_transactions,
                "total_spend":           total_spend,
                "refund_count":          refund_count,
                "total_tickets":         total_tickets,
                "high_priority_tickets": high_priority_tickets,
                "open_tickets":          open_tickets
            }])

            # Predict
            prob = model.predict_proba(features)[0][1]
            risk = "HIGH" if prob > 0.6 else "MEDIUM" if prob > 0.3 else "LOW"

            return (
                f"Customer: {customer.name}\n"
                f"Plan: {customer.plan} | Spend: ${customer.monthly_spend}/mo\n"
                f"Support Tickets: {total_tickets} | High Priority: {high_priority_tickets}\n"
                f"Churn Probability: {prob:.1%}\n"
                f"Risk Level: {risk}\n"
                f"Recommendation: {'Immediate attention needed!' if risk == 'HIGH' else 'Monitor closely.' if risk == 'MEDIUM' else 'Customer looks healthy.'}"
            )
        finally:
            db.close()
    except Exception as e:
        return f"Prediction error: {str(e)}"


@tool
def get_churn_risk_list(limit: int = 10) -> str:
    """
    Use this tool to get a list of customers most at risk of churning.
    Returns top customers ranked by churn risk.
    """
    try:
        with open("ml/models/churn_model.pkl", "rb") as f:
            model = pickle.load(f)

        db = SessionLocal()
        try:
            customers = db.query(Customer).filter(Customer.churned == 0).all()
            results = []

            for c in customers:
                total_transactions = len(c.transactions)
                total_spend = sum(t.amount for t in c.transactions)
                refund_count = sum(1 for t in c.transactions if t.status == "refunded")
                total_tickets = len(c.tickets)
                high_priority_tickets = sum(1 for t in c.tickets
                                           if t.priority in ["high", "critical"])
                open_tickets = sum(1 for t in c.tickets
                                  if t.status in ["open", "in_progress"])

                plan_map = {"basic": 0, "enterprise": 1, "pro": 2}
                size_map = {"large": 0, "medium": 1, "small": 2}
                region_map = {"asia_pacific": 0, "europe": 1, "latam": 2, "north_america": 3}
                industry_map = {"education": 0, "finance": 1, "healthcare": 2,
                               "logistics": 3, "retail": 4, "technology": 5}

                features = pd.DataFrame([{
                    "plan":                  plan_map.get(c.plan, 0),
                    "industry":              industry_map.get(c.industry, 0),
                    "company_size":          size_map.get(c.company_size, 0),
                    "region":                region_map.get(c.region, 0),
                    "monthly_spend":         c.monthly_spend,
                    "total_transactions":    total_transactions,
                    "total_spend":           total_spend,
                    "refund_count":          refund_count,
                    "total_tickets":         total_tickets,
                    "high_priority_tickets": high_priority_tickets,
                    "open_tickets":          open_tickets
                }])

                prob = model.predict_proba(features)[0][1]
                results.append((c.name, c.plan, c.monthly_spend, prob))

            # Sort by churn probability
            results.sort(key=lambda x: x[3], reverse=True)
            top = results[:limit]

            output = f"Top {limit} customers at risk of churning:\n"
            output += "-" * 60 + "\n"
            for i, (name, plan, spend, prob) in enumerate(top, 1):
                risk = "HIGH" if prob > 0.6 else "MEDIUM" if prob > 0.3 else "LOW"
                output += f"{i}. {name} | {plan} | ${spend}/mo | {prob:.1%} risk | {risk}\n"
            return output

        finally:
            db.close()
    except Exception as e:
        return f"Error: {str(e)}"