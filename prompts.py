"""
LangChain prompt templates for financial document processing
"""

from langchain.prompts import PromptTemplate
from typing import Dict, Any

# Financial data extraction prompt
EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["text", "company_name", "year"],
    template="""
You are a financial data extraction expert. Extract structured financial data from the following document text.

IMPORTANT INSTRUCTIONS:
1. Extract ONLY the numerical values (no currency symbols, commas, or text)
2. All values should be in actual dollars (not thousands or millions)
3. If a value is stated in thousands, multiply by 1,000
4. If a value is stated in millions, multiply by 1,000,000
5. Use null for any values you cannot find or are uncertain about
6. Ensure mathematical relationships are consistent (e.g., gross_profit = revenue - cogs)

Company: {company_name}
Year: {year}

Document Text:
{text}

Extract the following financial data and return as valid JSON:

{{
    "company_name": "exact company name from document",
    "year": "year of the financial statement",
    "revenue": number_value_or_null,
    "cogs": number_value_or_null,
    "gross_profit": number_value_or_null,
    "operating_expenses": number_value_or_null,
    "operating_income": number_value_or_null,
    "net_income": number_value_or_null,
    "total_assets": number_value_or_null,
    "total_liabilities": number_value_or_null,
    "equity": number_value_or_null
}}

Key terms to look for:
- Revenue: Total Revenue, Net Sales, Sales Revenue, Total Sales
- COGS: Cost of Goods Sold, Cost of Sales, Cost of Revenue
- Gross Profit: Gross Income, Gross Margin
- Operating Expenses: Operating Costs, SG&A, General and Administrative
- Operating Income: Operating Profit, EBIT, Income from Operations
- Net Income: Net Profit, Net Earnings, Profit After Tax
- Total Assets: Total Assets, Sum of Assets
- Total Liabilities: Total Liabilities, Total Debt
- Equity: Shareholders' Equity, Stockholders' Equity, Net Worth

Return only the JSON object, no additional text:
"""
)

# Financial comparison prompt
COMPARISON_PROMPT = PromptTemplate(
    input_variables=["company_name", "current_year_data", "previous_year_data"],
    template="""
You are a financial analyst. Compare the financial performance between two years and provide insights.

Company: {company_name}

Current Year Data ({current_year_data}):
Revenue: ${current_year_data[revenue]:,} if {current_year_data[revenue]} else "N/A"
Gross Profit: ${current_year_data[gross_profit]:,} if {current_year_data[gross_profit]} else "N/A"
Operating Income: ${current_year_data[operating_income]:,} if {current_year_data[operating_income]} else "N/A"
Net Income: ${current_year_data[net_income]:,} if {current_year_data[net_income]} else "N/A"

Previous Year Data ({previous_year_data}):
Revenue: ${previous_year_data[revenue]:,} if {previous_year_data[revenue]} else "N/A"
Gross Profit: ${previous_year_data[gross_profit]:,} if {previous_year_data[gross_profit]} else "N/A"
Operating Income: ${previous_year_data[operating_income]:,} if {previous_year_data[operating_income]} else "N/A"
Net Income: ${previous_year_data[net_income]:,} if {previous_year_data[net_income]} else "N/A"

Provide a comprehensive financial analysis covering:

1. REVENUE ANALYSIS:
   - Revenue growth/decline percentage
   - Key factors that might explain the change

2. PROFITABILITY ANALYSIS:
   - Gross profit margin changes
   - Operating efficiency improvements/deterioration
   - Net profit margin trends

3. KEY INSIGHTS:
   - Most significant positive changes
   - Areas of concern
   - Overall financial health assessment

4. RECOMMENDATIONS:
   - Strategic focus areas
   - Operational improvements needed

Format your response as a structured analysis with clear sections and specific numbers.
"""
)

# Company summary prompt
COMPANY_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["company_name", "financial_data"],
    template="""
You are a financial advisor. Provide a comprehensive summary of the company's financial performance over time.

Company: {company_name}

Financial Data (Multiple Years):
{financial_data}

Create a detailed financial summary that includes:

1. OVERALL PERFORMANCE TRENDS:
   - Revenue growth trajectory
   - Profitability evolution
   - Key financial milestones

2. FINANCIAL STRENGTH INDICATORS:
   - Consistent profit generation
   - Asset management efficiency
   - Financial stability metrics

3. GROWTH PATTERNS:
   - Year-over-year growth rates
   - Seasonal or cyclical patterns
   - Growth sustainability

4. RISK ASSESSMENT:
   - Volatility in performance
   - Potential red flags
   - Financial resilience

5. STRATEGIC RECOMMENDATIONS:
   - Areas for improvement
   - Growth opportunities
   - Risk mitigation strategies

Provide specific numbers and percentages where possible. Make the analysis actionable for business decision-making.
"""
)

# Data validation prompt
VALIDATION_PROMPT = PromptTemplate(
    input_variables=["extracted_data"],
    template="""
You are a data quality expert. Validate the following extracted financial data for logical consistency and accuracy.

Extracted Data:
{extracted_data}

Check for:

1. MATHEMATICAL CONSISTENCY:
   - Does gross_profit = revenue - cogs?
   - Are all values reasonable and in proper scale?
   - Do balance sheet items balance properly?

2. LOGICAL RELATIONSHIPS:
   - Is operating_income <= gross_profit?
   - Is net_income <= operating_income?
   - Are expense ratios reasonable?

3. DATA QUALITY ISSUES:
   - Any obviously wrong values (negative revenue, etc.)?
   - Missing critical data points?
   - Inconsistent units or scaling?

Return a JSON object with validation results:
{{
    "is_valid": true/false,
    "issues": ["list of specific issues found"],
    "corrections": {{
        "field_name": "suggested_correction"
    }},
    "confidence_score": 0.0-1.0,
    "quality_rating": "excellent/good/fair/poor"
}}
"""
)

# Industry-specific prompts
SAAS_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["text", "company_name", "year"],
    template="""
You are a SaaS financial expert. Extract SaaS-specific financial metrics from the following document.

Company: {company_name}
Year: {year}

Document Text:
{text}

Extract both standard financial data AND SaaS-specific metrics:

{{
    "company_name": "exact company name",
    "year": "year",
    "revenue": number_value_or_null,
    "recurring_revenue": number_value_or_null,
    "subscription_revenue": number_value_or_null,
    "gross_profit": number_value_or_null,
    "gross_margin": percentage_or_null,
    "operating_income": number_value_or_null,
    "net_income": number_value_or_null,
    "customer_acquisition_cost": number_value_or_null,
    "customer_lifetime_value": number_value_or_null,
    "churn_rate": percentage_or_null,
    "monthly_recurring_revenue": number_value_or_null,
    "annual_recurring_revenue": number_value_or_null
}}

Look for SaaS-specific terms:
- ARR (Annual Recurring Revenue)
- MRR (Monthly Recurring Revenue)
- CAC (Customer Acquisition Cost)
- LTV (Customer Lifetime Value)
- Churn Rate, Retention Rate
- Subscription Revenue
- Recurring vs Non-recurring Revenue

Return only the JSON object:
"""
)

# Retail-specific prompt
RETAIL_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["text", "company_name", "year"],
    template="""
You are a retail financial expert. Extract retail-specific financial metrics.

Company: {company_name}
Year: {year}

Document Text:
{text}

Extract retail-focused financial data:

{{
    "company_name": "exact company name",
    "year": "year",
    "revenue": number_value_or_null,
    "same_store_sales": number_value_or_null,
    "comparable_store_sales": number_value_or_null,
    "gross_profit": number_value_or_null,
    "inventory": number_value_or_null,
    "cost_of_goods_sold": number_value_or_null,
    "operating_income": number_value_or_null,
    "net_income": number_value_or_null,
    "inventory_turnover": number_value_or_null,
    "gross_margin": percentage_or_null,
    "store_count": number_value_or_null,
    "sales_per_square_foot": number_value_or_null
}}

Look for retail-specific terms:
- Same Store Sales (SSS)
- Comparable Store Sales (Comp Sales)
- Inventory Turnover
- Sales per Square Foot
- Store Count, New Store Openings
- Seasonal Revenue Patterns

Return only the JSON object:
"""
)

# Error handling prompt
ERROR_HANDLING_PROMPT = PromptTemplate(
    input_variables=["error_type", "original_text", "failed_extraction"],
    template="""
The financial data extraction failed. Help debug and retry the extraction.

Error Type: {error_type}
Failed Extraction: {failed_extraction}

Original Text Sample:
{original_text}

Please:
1. Identify why the extraction might have failed
2. Suggest a corrected approach
3. Retry the extraction with a simpler format

Focus on finding the most obvious financial numbers in the text, even if not perfectly labeled.

Return a JSON object with your best attempt at extraction:
{{
    "company_name": "best guess",
    "year": "best guess",
    "revenue": number_or_null,
    "gross_profit": number_or_null,
    "net_income": number_or_null,
    "extraction_confidence": 0.0-1.0,
    "extraction_notes": "explanation of what was found"
}}
"""
)

# Prompt factory function
def get_extraction_prompt(industry: str = "general") -> PromptTemplate:
    """
    Get appropriate extraction prompt based on industry
    
    Args:
        industry: Industry type (general, saas, retail, etc.)
        
    Returns:
        Appropriate PromptTemplate
    """
    prompts = {
        "general": EXTRACTION_PROMPT,
        "saas": SAAS_EXTRACTION_PROMPT,
        "retail": RETAIL_EXTRACTION_PROMPT,
        "software": SAAS_EXTRACTION_PROMPT,  # Alias
        "ecommerce": RETAIL_EXTRACTION_PROMPT  # Alias
    }
    
    return prompts.get(industry.lower(), EXTRACTION_PROMPT)


# Prompt testing function
def test_prompts():
    """Test prompt formatting"""
    sample_data = {
        "company_name": "ACME Corp",
        "year": "2023",
        "text": "Revenue: $1,000,000\nNet Income: $100,000"
    }
    
    # Test extraction prompt
    extraction_prompt = EXTRACTION_PROMPT.format(**sample_data)
    print("Extraction Prompt Preview:")
    print(extraction_prompt[:500] + "...")
    
    # Test comparison prompt
    current_data = {"revenue": 1000000, "net_income": 100000}
    previous_data = {"revenue": 800000, "net_income": 80000}
    
    comparison_prompt = COMPARISON_PROMPT.format(
        company_name="ACME Corp",
        current_year_data=current_data,
        previous_year_data=previous_data
    )
    print("\nComparison Prompt Preview:")
    print(comparison_prompt[:500] + "...")


if __name__ == "__main__":
    test_prompts()