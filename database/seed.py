import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import datetime, timedelta
from faker import Faker
from database.database import engine, SessionLocal
from database.models import Base, Customer, Transaction, SupportTicket

fake = Faker()
random.seed(42)

PLANS             = ["basic", "pro", "enterprise"]
INDUSTRIES        = ["retail", "healthcare", "finance", "technology", "education", "logistics"]
COMPANY_SIZES     = ["small", "medium", "large"]
REGIONS           = ["north_america", "europe", "asia_pacific", "latam"]
PRODUCTS          = ["Analytics Suite", "Data Connector", "AI Reports", "Dashboard Pro", "API Access"]
TX_STATUSES       = ["completed", "completed", "completed", "refunded", "pending"]
TICKET_PRIORITIES = ["low", "medium", "high", "critical"]
TICKET_STATUSES   = ["resolved", "resolved", "open", "in_progress"]
TICKET_SUBJECTS   = [
    "Login issue", "Billing question", "Data not loading",
    "Export feature broken", "Performance slow", "Integration failing",
    "Password reset", "Feature request", "API rate limit hit", "Report missing data"
]

def random_date(start_days_ago=730, end_days_ago=0):
    delta = random.randint(end_days_ago, start_days_ago)
    return datetime.utcnow() - timedelta(days=delta)

def make_customers(n=200):
    customers = []
    for _ in range(n):
        plan = random.choice(PLANS)
        spend_ranges = {
            "basic":      (50,   200),
            "pro":        (200,  800),
            "enterprise": (800, 5000)
        }
        lo, hi = spend_ranges[plan]
        spend = round(random.uniform(lo, hi), 2)

        churn_prob = 0.05
        if plan == "basic":      churn_prob += 0.15
        if spend < 100:          churn_prob += 0.10
        if plan == "enterprise": churn_prob -= 0.03

        customers.append(Customer(
            name          = fake.company(),
            email         = fake.unique.company_email(),
            plan          = plan,
            industry      = random.choice(INDUSTRIES),
            company_size  = random.choice(COMPANY_SIZES),
            region        = random.choice(REGIONS),
            monthly_spend = spend,
            signup_date   = random_date(730, 30),
            churned       = 1 if random.random() < churn_prob else 0
        ))
    return customers

def make_transactions(customers):
    transactions = []
    for customer in customers:
        for _ in range(random.randint(1, 15)):
            transactions.append(Transaction(
                customer_id = customer.id,
                amount      = round(random.uniform(20, customer.monthly_spend * 1.5), 2),
                product     = random.choice(PRODUCTS),
                status      = random.choice(TX_STATUSES),
                created_at  = random_date(365, 0)
            ))
    return transactions

def make_tickets(customers):
    tickets = []
    for customer in customers:
        n_tickets = random.randint(3, 8) if customer.churned else random.randint(0, 4)
        for _ in range(n_tickets):
            created     = random_date(365, 0)
            status      = random.choice(TICKET_STATUSES)
            resolved_at = (created + timedelta(days=random.randint(1, 10))
                          if status == "resolved" else None)
            tickets.append(SupportTicket(
                customer_id = customer.id,
                subject     = random.choice(TICKET_SUBJECTS),
                description = fake.paragraph(nb_sentences=2),
                priority    = random.choice(TICKET_PRIORITIES),
                status      = status,
                created_at  = created,
                resolved_at = resolved_at
            ))
    return tickets

def seed():
    print("Step 1/4: Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("Step 2/4: Clearing old data...")
        db.query(SupportTicket).delete()
        db.query(Transaction).delete()
        db.query(Customer).delete()
        db.commit()

        print("Step 3/4: Seeding data...")
        customers = make_customers(200)
        db.add_all(customers)
        db.commit()
        for c in customers:
            db.refresh(c)

        transactions = make_transactions(customers)
        db.add_all(transactions)
        db.commit()

        tickets = make_tickets(customers)
        db.add_all(tickets)
        db.commit()

        total_churned = db.query(Customer).filter(Customer.churned == 1).count()
        print(f"\nStep 4/4: Done!")
        print(f"  Customers   : 200  ({total_churned} churned, {200 - total_churned} active)")
        print(f"  Transactions: {db.query(Transaction).count()}")
        print(f"  Tickets     : {db.query(SupportTicket).count()}")
        print(f"\n  Database file created: salesiq.db")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()