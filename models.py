"""
Database models and session management for Financial Document Processor
"""
from config import settings

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, BigInteger, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from typing import Generator

# Database configuration
DATABASE_URL = str(settings.database_url)

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


class FinancialStatement(Base):
    """
    Financial statement data model
    Stores structured financial data extracted from PDF documents
    """
    __tablename__ = "financial_statements"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Company identification
    company_name = Column(String(255), nullable=False, index=True)
    year = Column(String(10), nullable=False, index=True)
    
    # Income Statement Data
    revenue = Column(BigInteger, nullable=True, comment="Total Revenue/Sales")
    cogs = Column(BigInteger, nullable=True, comment="Cost of Goods Sold")
    gross_profit = Column(BigInteger, nullable=True, comment="Revenue - COGS")
    operating_expenses = Column(BigInteger, nullable=True, comment="Operating Expenses")
    operating_income = Column(BigInteger, nullable=True, comment="Operating Income/EBIT")
    net_income = Column(BigInteger, nullable=True, comment="Net Income After Tax")
    
    # Balance Sheet Data
    total_assets = Column(BigInteger, nullable=True, comment="Total Assets")
    total_liabilities = Column(BigInteger, nullable=True, comment="Total Liabilities")
    equity = Column(BigInteger, nullable=True, comment="Shareholders Equity")
    
    # Additional financial metrics (can be calculated or extracted)
    gross_margin = Column(Float, nullable=True, comment="Gross Profit Margin %")
    operating_margin = Column(Float, nullable=True, comment="Operating Margin %")
    net_margin = Column(Float, nullable=True, comment="Net Profit Margin %")
    
    # Metadata
    raw_text = Column(Text, nullable=True, comment="Raw extracted text from PDF")
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional fields for better tracking
    file_name = Column(String(500), nullable=True, comment="Original PDF filename")
    extraction_confidence = Column(Float, nullable=True, comment="LLM extraction confidence score")
    
    def __repr__(self):
        return f"<FinancialStatement(company='{self.company_name}', year='{self.year}', revenue={self.revenue})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'company_name': self.company_name,
            'year': self.year,
            'revenue': self.revenue,
            'cogs': self.cogs,
            'gross_profit': self.gross_profit,
            'operating_expenses': self.operating_expenses,
            'operating_income': self.operating_income,
            'net_income': self.net_income,
            'total_assets': self.total_assets,
            'total_liabilities': self.total_liabilities,
            'equity': self.equity,
            'gross_margin': self.gross_margin,
            'operating_margin': self.operating_margin,
            'net_margin': self.net_margin,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def calculate_margins(self):
        """Calculate financial margins"""
        if self.revenue and self.revenue > 0:
            if self.gross_profit is not None:
                self.gross_margin = (self.gross_profit / self.revenue) * 100
            if self.operating_income is not None:
                self.operating_margin = (self.operating_income / self.revenue) * 100
            if self.net_income is not None:
                self.net_margin = (self.net_income / self.revenue) * 100


class Company(Base):
    """
    Company master data (for future normalization)
    """
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    industry = Column(String(100), nullable=True)
    sector = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Company(name='{self.name}', industry='{self.industry}')>"


class ProcessingLog(Base):
    """
    Log table to track document processing history
    """
    __tablename__ = "processing_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    file_name = Column(String(500), nullable=False)
    company_name = Column(String(255), nullable=True)
    year = Column(String(10), nullable=True)
    
    # Processing status
    status = Column(String(50), nullable=False, default="processing")  # processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Processing metrics
    processing_time_seconds = Column(Float, nullable=True)
    extracted_text_length = Column(Integer, nullable=True)
    llm_model_used = Column(String(100), nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<ProcessingLog(file='{self.file_name}', status='{self.status}')>"


def get_db() -> Generator:
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all database tables
    """
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def drop_tables():
    """
    Drop all database tables (use with caution!)
    """
    Base.metadata.drop_all(bind=engine)
    print("Database tables dropped!")


if __name__ == "__main__":
    # Create tables when run directly
    create_tables()