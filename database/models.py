from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    email         = Column(String(150), unique=True, nullable=False)
    plan          = Column(String(50))        # basic / pro / enterprise
    industry      = Column(String(100))       # retail / healthcare / finance etc
    company_size  = Column(String(50))        # small / medium / large
    region        = Column(String(50))        # north_america / europe / asia_pacific
    monthly_spend = Column(Float)             # how much they pay per month
    signup_date   = Column(DateTime, default=datetime.utcnow)
    churned       = Column(Integer, default=0) # 0 = active, 1 = cancelled

    transactions = relationship("Transaction", back_populates="customer")
    tickets      = relationship("SupportTicket", back_populates="customer")


class Transaction(Base):
    __tablename__ = "transactions"

    id          = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    amount      = Column(Float)
    product     = Column(String(100))
    status      = Column(String(50))   # completed / refunded / pending
    created_at  = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="transactions")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id          = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    subject     = Column(String(200))
    description = Column(Text)
    priority    = Column(String(50))   # low / medium / high / critical
    status      = Column(String(50))   # open / in_progress / resolved
    created_at  = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    customer = relationship("Customer", back_populates="tickets")