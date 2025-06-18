"""
PDF processing and text extraction utilities
"""

import pdfplumber
import re
from typing import Optional, Dict, List
import io
import logging

logger = logging.getLogger(__name__)


def extract_pdf_text(pdf_content: bytes) -> Optional[str]:
    """
    Extract text content from PDF bytes using pdfplumber
    
    Args:
        pdf_content: PDF file content as bytes
        
    Returns:
        Extracted text string or None if extraction fails
    """
    try:
        # Create a file-like object from bytes
        pdf_file = io.BytesIO(pdf_content)
        
        extracted_text = ""
        
        with pdfplumber.open(pdf_file) as pdf:
            logger.info(f"Processing PDF with {len(pdf.pages)} pages")
            
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    # Extract text from page
                    page_text = page.extract_text()
                    
                    if page_text:
                        extracted_text += f"\n--- Page {page_num} ---\n"
                        extracted_text += page_text
                        extracted_text += "\n"
                    
                    # Try to extract tables as well
                    tables = page.extract_tables()
                    if tables:
                        for table_num, table in enumerate(tables, 1):
                            extracted_text += f"\n--- Table {table_num} (Page {page_num}) ---\n"
                            for row in table:
                                if row:  # Skip empty rows
                                    # Join non-None cells with tabs
                                    row_text = "\t".join([str(cell) if cell is not None else "" for cell in row])
                                    extracted_text += row_text + "\n"
                
                except Exception as e:
                    logger.warning(f"Error extracting from page {page_num}: {str(e)}")
                    continue
        
        if not extracted_text.strip():
            logger.error("No text could be extracted from PDF")
            return None
            
        logger.info(f"Successfully extracted {len(extracted_text)} characters from PDF")
        return extracted_text
        
    except Exception as e:
        logger.error(f"PDF extraction failed: {str(e)}")
        return None


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text for better LLM processing
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text string
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove page markers
    text = re.sub(r'--- Page \d+ ---', '', text)
    text = re.sub(r'--- Table \d+ \(Page \d+\) ---', '\nTABLE:\n', text)
    
    # Normalize currency symbols and numbers
    text = re.sub(r'\$\s*', '$', text)  # Fix spaced dollar signs
    text = re.sub(r'(\d),(\d)', r'\1\2', text)  # Remove commas from numbers (but be careful)
    
    # Remove excessive line breaks
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_financial_keywords(text: str) -> Dict[str, List[str]]:
    """
    Extract potential financial keywords and values from text
    This helps with debugging and validation
    
    Args:
        text: Cleaned text
        
    Returns:
        Dictionary with categorized financial keywords found
    """
    keywords = {
        'revenue_terms': [],
        'expense_terms': [],
        'profit_terms': [],
        'balance_sheet_terms': [],
        'numbers': []
    }
    
    # Revenue-related terms
    revenue_patterns = [
        r'(total\s+)?revenue\s*[:=]?\s*\$?[\d,]+',
        r'(net\s+)?sales\s*[:=]?\s*\$?[\d,]+',
        r'income\s+from\s+operations\s*[:=]?\s*\$?[\d,]+',
        r'gross\s+revenue\s*[:=]?\s*\$?[\d,]+'
    ]
    
    # Expense-related terms
    expense_patterns = [
        r'cost\s+of\s+(goods\s+sold|sales)\s*[:=]?\s*\$?[\d,]+',
        r'operating\s+expenses?\s*[:=]?\s*\$?[\d,]+',
        r'total\s+expenses?\s*[:=]?\s*\$?[\d,]+'
    ]
    
    # Profit-related terms
    profit_patterns = [
        r'(net\s+)?income\s*[:=]?\s*\$?[\d,]+',
        r'gross\s+profit\s*[:=]?\s*\$?[\d,]+',
        r'operating\s+income\s*[:=]?\s*\$?[\d,]+',
        r'profit\s*[:=]?\s*\$?[\d,]+'
    ]
    
    # Balance sheet terms
    balance_patterns = [
        r'total\s+assets\s*[:=]?\s*\$?[\d,]+',
        r'total\s+liabilities\s*[:=]?\s*\$?[\d,]+',
        r'(shareholders?\s+)?equity\s*[:=]?\s*\$?[\d,]+'
    ]
    
    # Extract matches
    for pattern in revenue_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        keywords['revenue_terms'].extend(matches)
    
    for pattern in expense_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        keywords['expense_terms'].extend(matches)
    
    for pattern in profit_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        keywords['profit_terms'].extend(matches)
    
    for pattern in balance_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        keywords['balance_sheet_terms'].extend(matches)
    
    # Extract all numbers with currency
    number_pattern = r'\$[\d,]+(?:\.\d{2})?'
    keywords['numbers'] = re.findall(number_pattern, text)
    
    return keywords


def validate_pdf_content(pdf_content: bytes) -> Dict[str, any]:
    """
    Validate PDF content and provide metadata
    
    Args:
        pdf_content: PDF file content as bytes
        
    Returns:
        Dictionary with validation results and metadata
    """
    try:
        pdf_file = io.BytesIO(pdf_content)
        
        with pdfplumber.open(pdf_file) as pdf:
            return {
                'valid': True,
                'page_count': len(pdf.pages),
                'file_size_bytes': len(pdf_content),
                'has_text': any(page.extract_text() for page in pdf.pages[:3]),  # Check first 3 pages
                'has_tables': any(page.extract_tables() for page in pdf.pages[:3]),
                'metadata': pdf.metadata if hasattr(pdf, 'metadata') else {}
            }
    
    except Exception as e:
        logger.error(f"PDF validation failed: {str(e)}")
        return {
            'valid': False,
            'error': str(e),
            'file_size_bytes': len(pdf_content)
        }


def extract_company_info(text: str) -> Dict[str, Optional[str]]:
    """
    Try to extract company name and year from text using regex patterns
    
    Args:
        text: Cleaned text
        
    Returns:
        Dictionary with extracted company info
    """
    company_info = {
        'company_name': None,
        'year': None,
        'report_type': None
    }
    
    # Common company name patterns
    company_patterns = [
        r'([A-Z][a-zA-Z\s&,\.]+(?:Inc|Corp|LLC|Ltd|Company|Corporation))',
        r'COMPANY:\s*([A-Z][a-zA-Z\s&,\.]+)',
        r'([A-Z][A-Z\s&]+)(?:\s+FINANCIAL|\s+ANNUAL|\s+INCOME)'
    ]
    
    # Year patterns
    year_patterns = [
        r'(?:FOR THE YEAR ENDED|YEAR ENDED|DECEMBER 31,?\s+)(\d{4})',
        r'ANNUAL REPORT\s+(\d{4})',
        r'(\d{4})\s+ANNUAL REPORT',
        r'FISCAL YEAR\s+(\d{4})'
    ]
    
    # Report type patterns
    report_patterns = [
        r'(INCOME STATEMENT|PROFIT\s+AND\s+LOSS|P&L)',
        r'(BALANCE SHEET|STATEMENT OF FINANCIAL POSITION)',
        r'(CASH FLOW STATEMENT|STATEMENT OF CASH FLOWS)',
        r'(ANNUAL REPORT|QUARTERLY REPORT|10-K|10-Q)'
    ]
    
    # Extract company name
    for pattern in company_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            company_info['company_name'] = match.group(1).strip()
            break
    
    # Extract year
    for pattern in year_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            company_info['year'] = match.group(1)
            break
    
    # Extract report type
    for pattern in report_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            company_info['report_type'] = match.group(1)
            break
    
    return company_info


def chunk_text_for_llm(text: str, max_chunk_size: int = 4000) -> List[str]:
    """
    Split text into chunks suitable for LLM processing
    
    Args:
        text: Text to chunk
        max_chunk_size: Maximum characters per chunk
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed limit, save current chunk
        if len(current_chunk) + len(paragraph) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = ""
        
        # If single paragraph is too long, split by sentences
        if len(paragraph) > max_chunk_size:
            sentences = paragraph.split('. ')
            for sentence in sentences:
                if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                current_chunk += sentence + ". "
        else:
            current_chunk += paragraph + "\n\n"
    
    # Add the last chunk if it has content
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


def detect_table_structure(text: str) -> List[Dict]:
    """
    Detect and parse table-like structures in text
    
    Args:
        text: Text containing potential tables
        
    Returns:
        List of detected table structures
    """
    tables = []
    lines = text.split('\n')
    
    current_table = []
    in_table = False
    
    for line in lines:
        # Check if line looks like a table row (has tabs or multiple spaces)
        if '\t' in line or re.search(r'\s{3,}', line):
            if not in_table:
                in_table = True
                current_table = []
            
            # Split by tabs or multiple spaces
            if '\t' in line:
                cells = line.split('\t')
            else:
                cells = re.split(r'\s{3,}', line)
            
            # Clean up cells
            cells = [cell.strip() for cell in cells if cell.strip()]
            if cells:
                current_table.append(cells)
        
        else:
            # End of table
            if in_table and current_table:
                tables.append({
                    'rows': current_table,
                    'row_count': len(current_table),
                    'column_count': max(len(row) for row in current_table) if current_table else 0
                })
                current_table = []
            in_table = False
    
    # Don't forget the last table
    if in_table and current_table:
        tables.append({
            'rows': current_table,
            'row_count': len(current_table),
            'column_count': max(len(row) for row in current_table) if current_table else 0
        })
    
    return tables


if __name__ == "__main__":
    # Test function
    sample_text = """
    ACME Corporation
    Annual Report 2023
    
    Revenue                 $1,000,000
    Cost of Goods Sold       $600,000
    Gross Profit             $400,000
    Operating Expenses       $200,000
    Net Income               $200,000
    """
    
    print("Sample text processing:")
    print(f"Cleaned: {clean_text(sample_text)}")
    print(f"Keywords: {extract_financial_keywords(sample_text)}")
    print(f"Company info: {extract_company_info(sample_text)}")
    print(f"Chunks: {len(chunk_text_for_llm(sample_text))}")
    print(f"Tables: {detect_table_structure(sample_text)}")