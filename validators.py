"""
Pydantic models for financial data validation
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator, model_validator, ConfigDict
from datetime import datetime
import re


class FinancialData(BaseModel):
    """
    Main financial data validation model
    """
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "company_name": "ACME Corporation",
                "year": "2023",
                "revenue": 1000000,
                "cogs": 600000,
                "gross_profit": 400000,
                "operating_expenses": 200000,
                "operating_income": 200000,
                "net_income": 150000,
                "total_assets": 2000000,
                "total_liabilities": 800000,
                "equity": 1200000
            }
        }
    )
    
    company_name: str = Field(..., min_length=1, max_length=255, description="Company name")
    year: str = Field(..., pattern=r'^\d{4}$', description="Year in YYYY format")

    # Income Statement Items
    revenue: Optional[int] = Field(None, ge=0, description="Total revenue/sales")
    cogs: Optional[int] = Field(None, ge=0, description="Cost of goods sold")
    gross_profit: Optional[int] = Field(None, description="Gross profit (can be negative)")
    operating_expenses: Optional[int] = Field(None, ge=0, description="Operating expenses")
    operating_income: Optional[int] = Field(None, description="Operating income (can be negative)")
    net_income: Optional[int] = Field(None, description="Net income (can be negative)")
    
    # Balance Sheet Items
    total_assets: Optional[int] = Field(None, ge=0, description="Total assets")
    total_liabilities: Optional[int] = Field(None, ge=0, description="Total liabilities")
    equity: Optional[int] = Field(None, description="Shareholders equity (can be negative)")
    
    # Calculated fields (optional)
    gross_margin: Optional[float] = Field(None, ge=0, le=100, description="Gross margin percentage")
    operating_margin: Optional[float] = Field(None, ge=-100, le=100, description="Operating margin percentage")
    net_margin: Optional[float] = Field(None, ge=-100, le=100, description="Net margin percentage")
    
    @validator('company_name')
    def validate_company_name(cls, v: str) -> str:
        """Clean and validate company name"""
        if not v or not v.strip():
            raise ValueError('Company name cannot be empty')
        
        # Clean the name
        v = v.strip()
        v = re.sub(r'\s+', ' ', v)  # Normalize whitespace
        
        return v
    
    @validator('year')
    def validate_year(cls, v: str) -> str:
        """Validate year is reasonable"""
        year_int = int(v)
        current_year = datetime.now().year
        
        if year_int < 1900 or year_int > current_year + 1:
            raise ValueError(f'Year must be between 1900 and {current_year + 1}')
        
        return v
    
    @validator('revenue', 'cogs', 'operating_expenses', 'total_assets', 'total_liabilities')
    def validate_positive_values(cls, v: Optional[int]) -> Optional[int]:
        """Ensure certain fields are non-negative when provided"""
        if v is not None and v < 0:
            raise ValueError(f'Field cannot be negative')
        return v
    
    @model_validator(mode='after')
    def validate_financial_logic(self) -> 'FinancialData':
        """Validate financial relationships and logic"""
        errors = []
        
        # Gross profit validation
        if self.revenue is not None and self.cogs is not None and self.gross_profit is not None:
            expected_gross_profit = self.revenue - self.cogs
            tolerance = max(1000, abs(expected_gross_profit) * 0.01)  # 1% tolerance or $1000 min
            
            if abs(self.gross_profit - expected_gross_profit) > tolerance:
                errors.append(
                    f"Gross profit ({self.gross_profit:,}) doesn't match Revenue - COGS "
                    f"({self.revenue:,} - {self.cogs:,} = {expected_gross_profit:,})"
                )
        
        # Operating income validation
        if self.gross_profit is not None and self.operating_expenses is not None and self.operating_income is not None:
            expected_operating_income = self.gross_profit - self.operating_expenses
            tolerance = max(1000, abs(expected_operating_income) * 0.01)
            
            if abs(self.operating_income - expected_operating_income) > tolerance:
                errors.append(
                    f"Operating income ({self.operating_income:,}) doesn't match Gross Profit - Operating Expenses "
                    f"({self.gross_profit:,} - {self.operating_expenses:,} = {expected_operating_income:,})"
                )
        
        # Balance sheet validation
        if self.total_assets is not None and self.total_liabilities is not None and self.equity is not None:
            expected_equity = self.total_assets - self.total_liabilities
            tolerance = max(1000, abs(expected_equity) * 0.01)
            
            if abs(self.equity - expected_equity) > tolerance:
                errors.append(
                    f"Equity ({self.equity:,}) doesn't match Assets - Liabilities "
                    f"({self.total_assets:,} - {self.total_liabilities:,} = {expected_equity:,})"
                )
        
        # Logical order validation
        if self.revenue is not None and self.gross_profit is not None:
            if self.gross_profit > self.revenue:
                errors.append(f"Gross profit ({self.gross_profit:,}) cannot exceed revenue ({self.revenue:,})")
        
        if self.gross_profit is not None and self.operating_income is not None:
            if self.operating_income > self.gross_profit:
                errors.append(f"Operating income ({self.operating_income:,}) cannot exceed gross profit ({self.gross_profit:,})")
        
        if self.operating_income is not None and self.net_income is not None:
            if self.net_income > self.operating_income * 1.5 and self.operating_income > 0:
                errors.append(
                    f"Net income ({self.net_income:,}) is unusually high compared to operating income ({self.operating_income:,}). "
                    "Please verify non-operating income."
                )
        
        if errors:
            raise ValueError(f"Financial logic validation failed: {'; '.join(errors)}")
        
        return self

    def calculate_margins(self) -> Dict[str, Optional[float]]:
        """Calculate financial margins"""
        margins = {}
        
        if self.revenue and self.revenue > 0:
            if self.gross_profit is not None:
                margins['gross_margin'] = (self.gross_profit / self.revenue) * 100
            
            if self.operating_income is not None:
                margins['operating_margin'] = (self.operating_income / self.revenue) * 100
            
            if self.net_income is not None:
                margins['net_margin'] = (self.net_income / self.revenue) * 100
        
        return margins
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of data completeness and quality"""
        total_fields = 12  # Main financial fields
        completed_fields = sum(1 for field in [
            self.revenue, self.cogs, self.gross_profit, self.operating_expenses,
            self.operating_income, self.net_income, self.total_assets,
            self.total_liabilities, self.equity
        ] if field is not None)
        
        return {
            'completeness_score': completed_fields / total_fields,
            'completed_fields': completed_fields,
            'total_fields': total_fields,
            'has_income_statement': all(x is not None for x in [self.revenue, self.net_income]),
            'has_balance_sheet': all(x is not None for x in [self.total_assets, self.total_liabilities, self.equity]),
            'margins': self.calculate_margins()
        }


class FinancialDataBatch(BaseModel):
    """
    Model for batch processing multiple financial records
    """
    records: List[FinancialData] = Field(..., min_items=1, description="List of financial records")
    batch_id: Optional[str] = Field(None, description="Batch identifier")
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('records')
    def validate_unique_company_years(cls, v: List[FinancialData]) -> List[FinancialData]:
        """Ensure no duplicate company-year combinations"""
        seen = set()
        for record in v:
            key = (record.company_name.lower(), record.year)
            if key in seen:
                raise ValueError(f"Duplicate record found for {record.company_name} - {record.year}")
            seen.add(key)
        return v


class SaaSFinancialData(FinancialData):
    """
    Extended model for SaaS-specific financial data
    """
    recurring_revenue: Optional[int] = Field(None, ge=0, description="Recurring revenue")
    annual_recurring_revenue: Optional[int] = Field(None, ge=0, description="ARR")
    monthly_recurring_revenue: Optional[int] = Field(None, ge=0, description="MRR")
    customer_acquisition_cost: Optional[int] = Field(None, ge=0, description="CAC")
    customer_lifetime_value: Optional[int] = Field(None, ge=0, description="LTV")
    churn_rate: Optional[float] = Field(None, ge=0, le=100, description="Monthly churn rate %")
    
    @model_validator(mode='after')
    def validate_saas_metrics(self) -> 'SaaSFinancialData':
        """Validate SaaS-specific relationships"""
        super().validate_financial_logic()
        
        if self.annual_recurring_revenue is not None and self.monthly_recurring_revenue is not None:
            expected_arr = self.monthly_recurring_revenue * 12
            tolerance = max(1000, expected_arr * 0.05)  # 5% tolerance
            
            if abs(self.annual_recurring_revenue - expected_arr) > tolerance:
                raise ValueError(
                    f"ARR ({self.annual_recurring_revenue:,}) doesn't match MRR * 12 ({self.monthly_recurring_revenue:,} * 12 = {expected_arr:,})"
                )
        
        return self


class RetailFinancialData(FinancialData):
    """
    Extended model for retail-specific financial data
    """
    same_store_sales: Optional[int] = Field(None, description="Same store sales")
    comparable_store_sales: Optional[int] = Field(None, description="Comparable store sales")
    inventory: Optional[int] = Field(None, ge=0, description="Inventory value")
    store_count: Optional[int] = Field(None, ge=0, description="Number of stores")
    sales_per_square_foot: Optional[float] = Field(None, ge=0, description="Sales per sq ft")
    inventory_turnover: Optional[float] = Field(None, ge=0, description="Inventory turnover ratio")


def validate_financial_data(data: Dict[str, Any], industry: str = "general") -> FinancialData:
    """
    Factory function to validate financial data based on industry
    
    Args:
        data: Raw financial data dictionary
        industry: Industry type for specialized validation
        
    Returns:
        Validated FinancialData instance
    """
    if industry.lower() in ("saas", "software"):
        return SaaSFinancialData(**data)
    elif industry.lower() in ("retail", "ecommerce"):
        return RetailFinancialData(**data)
    return FinancialData(**data)


def clean_financial_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and normalize raw financial data before validation
    
    Args:
        raw_data: Raw extracted data
        
    Returns:
        Cleaned data dictionary
    """
    cleaned = {}
    
    for key, value in raw_data.items():
        if value is None or value == "null" or value == "":
            cleaned[key] = None
            continue
        
        if isinstance(value, str):
            if key in ['revenue', 'cogs', 'gross_profit', 'operating_expenses', 
                      'operating_income', 'net_income', 'total_assets', 'total_liabilities', 'equity']:
                cleaned_value = re.sub(r'[\$,\(\)]', '', value)
                try:
                    cleaned[key] = -int(float(cleaned_value)) if '(' in value and ')' in value else int(float(cleaned_value))
                except (ValueError, TypeError):
                    cleaned[key] = None
            else:
                cleaned[key] = value.strip()
        else:
            cleaned[key] = value
    
    return cleaned


if __name__ == "__main__":
    # Test validation
    sample_data = {
        "company_name": "ACME Corp",
        "year": "2023",
        "revenue": 1000000,
        "cogs": 600000,
        "gross_profit": 400000,
        "operating_expenses": 200000,
        "operating_income": 200000,
        "net_income": 150000
    }
    
    try:
        validated_data = validate_financial_data(sample_data)
        print("Validation successful!")
        print(f"Summary: {validated_data.get_validation_summary()}")
        print(f"Margins: {validated_data.calculate_margins()}")
    except Exception as e:
        print(f"Validation failed: {e}")