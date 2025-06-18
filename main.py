"""
AI-Powered Financial Document Ingestion Engine
FastAPI Backend with LangChain + Ollama Integration
"""
from config import settings
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import logging
from datetime import datetime

# Local imports
from models import get_db, FinancialStatement, Base, engine
from utils import extract_pdf_text, clean_text
from prompts import EXTRACTION_PROMPT, COMPARISON_PROMPT
from validators import FinancialData, validate_financial_data
from llm_service import LLMService

# Initialize FastAPI app
app = FastAPI(
    title="AI Financial Document Processor",
    description="Process financial PDFs with local LLMs",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize LLM service
llm_service = LLMService()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Financial Document Processor...")
    await llm_service.initialize()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "AI Financial Document Processor API",
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    company_name: str = None,
    year: str = None,
    db: Session = Depends(get_db)
):
    """
    Ingest PDF financial document and extract structured data
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        logger.info(f"Processing file: {file.filename}")
        
        # Extract text from PDF
        pdf_content = await file.read()
        extracted_text = extract_pdf_text(pdf_content)
        
        if not extracted_text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Clean and prepare text
        cleaned_text = clean_text(extracted_text)
        logger.info(f"Extracted {len(cleaned_text)} characters from PDF")
        
        # Use LLM to extract structured data
        structured_data = await llm_service.extract_financial_data(
            text=cleaned_text,
            company_name=company_name,
            year=year
        )
        
        # Validate extracted data
        try:
            financial_data = validate_financial_data(structured_data)
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(status_code=422, detail=f"Data validation failed: {str(e)}")
        
        # Check if record already exists
        existing_record = db.query(FinancialStatement).filter(
            FinancialStatement.company_name == financial_data.company_name,
            FinancialStatement.year == financial_data.year
        ).first()
        
        if existing_record:
            raise HTTPException(
                status_code=409, 
                detail=f"Financial data for {financial_data.company_name} - {financial_data.year} already exists"
            )
        
        # Save to database
        db_record = FinancialStatement(
            company_name=financial_data.company_name,
            year=financial_data.year,
            revenue=financial_data.revenue,
            cogs=financial_data.cogs,
            gross_profit=financial_data.gross_profit,
            operating_expenses=financial_data.operating_expenses,
            operating_income=financial_data.operating_income,
            net_income=financial_data.net_income,
            total_assets=financial_data.total_assets,
            total_liabilities=financial_data.total_liabilities,
            equity=financial_data.equity,
            raw_text=cleaned_text[:5000],  # Store first 5000 chars
            uploaded_at=datetime.utcnow()
        )
        
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        
        logger.info(f"Successfully saved financial data for {financial_data.company_name} - {financial_data.year}")
        
        return {
            "message": "Document processed successfully",
            "data": financial_data.dict(),
            "id": db_record.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/companies")
async def get_companies(db: Session = Depends(get_db)):
    """Get list of all companies in database"""
    try:
        companies = db.query(FinancialStatement.company_name).distinct().all()
        return {"companies": [company[0] for company in companies]}
    except Exception as e:
        logger.error(f"Error fetching companies: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch companies")


@app.get("/company/{company_name}")
async def get_company_data(company_name: str, db: Session = Depends(get_db)):
    """Get all financial data for a specific company"""
    try:
        records = db.query(FinancialStatement).filter(
            FinancialStatement.company_name.ilike(f"%{company_name}%")
        ).order_by(FinancialStatement.year.desc()).all()
        
        if not records:
            raise HTTPException(status_code=404, detail=f"No data found for company: {company_name}")
        
        return {
            "company": company_name,
            "years": len(records),
            "data": [
                {
                    "id": record.id,
                    "year": record.year,
                    "revenue": record.revenue,
                    "gross_profit": record.gross_profit,
                    "operating_income": record.operating_income,
                    "net_income": record.net_income,
                    "total_assets": record.total_assets,
                    "uploaded_at": record.uploaded_at.isoformat()
                }
                for record in records
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch company data")


@app.get("/compare/{company_name}")
async def compare_financial_data(company_name: str, db: Session = Depends(get_db)):
    """
    Compare financial data across years for a company using LLM analysis
    """
    try:
        # Get the two most recent years
        records = db.query(FinancialStatement).filter(
            FinancialStatement.company_name.ilike(f"%{company_name}%")
        ).order_by(FinancialStatement.year.desc()).limit(2).all()
        
        if len(records) < 2:
            raise HTTPException(
                status_code=404, 
                detail=f"Need at least 2 years of data for comparison. Found {len(records)} records."
            )
        
        # Prepare data for LLM analysis
        current_year = records[0]
        previous_year = records[1]
        
        # Generate comparison using LLM
        comparison_analysis = await llm_service.generate_comparison(
            current_year=current_year,
            previous_year=previous_year
        )
        
        return {
            "company": company_name,
            "comparison_period": f"{previous_year.year} vs {current_year.year}",
            "data": {
                "current_year": {
                    "year": current_year.year,
                    "revenue": current_year.revenue,
                    "gross_profit": current_year.gross_profit,
                    "operating_income": current_year.operating_income,
                    "net_income": current_year.net_income
                },
                "previous_year": {
                    "year": previous_year.year,
                    "revenue": previous_year.revenue,
                    "gross_profit": previous_year.gross_profit,
                    "operating_income": previous_year.operating_income,
                    "net_income": previous_year.net_income
                }
            },
            "analysis": comparison_analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating comparison: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate comparison")


@app.get("/summary/{company_name}")
async def get_company_summary(company_name: str, db: Session = Depends(get_db)):
    """
    Generate AI-powered summary of company's financial performance
    """
    try:
        records = db.query(FinancialStatement).filter(
            FinancialStatement.company_name.ilike(f"%{company_name}%")
        ).order_by(FinancialStatement.year.desc()).all()
        
        if not records:
            raise HTTPException(status_code=404, detail=f"No data found for company: {company_name}")
        
        # Generate summary using LLM
        summary = await llm_service.generate_company_summary(records)
        
        return {
            "company": company_name,
            "years_analyzed": len(records),
            "summary": summary,
            "data_range": f"{records[-1].year} - {records[0].year}" if len(records) > 1 else records[0].year
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")


@app.delete("/company/{company_name}/year/{year}")
async def delete_financial_record(company_name: str, year: str, db: Session = Depends(get_db)):
    """Delete a specific financial record"""
    try:
        record = db.query(FinancialStatement).filter(
            FinancialStatement.company_name.ilike(f"%{company_name}%"),
            FinancialStatement.year == year
        ).first()
        
        if not record:
            raise HTTPException(
                status_code=404, 
                detail=f"No record found for {company_name} - {year}"
            )
        
        db.delete(record)
        db.commit()
        
        return {"message": f"Successfully deleted record for {company_name} - {year}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting record: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete record")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        workers=settings.api_workers
    )