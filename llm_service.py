"""
LLM Service for financial document processing
Handles all interactions with Ollama/LangChain
"""
from typing import List, Dict, Any, Optional
from config import settings
from langchain_community.llms import Ollama
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import logging
from prompts import (
    EXTRACTION_PROMPT,
    COMPARISON_PROMPT,
    COMPANY_SUMMARY_PROMPT,
    VALIDATION_PROMPT,
    get_extraction_prompt
)
from models import FinancialStatement
import json

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.llm = None
        self.extraction_chain = None
        self.comparison_chain = None
        self.summary_chain = None
        self.validation_chain = None

    async def initialize(self):
        """Initialize LLM connections and chains"""
        try:
            callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
            
            self.llm = Ollama(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                callback_manager=callback_manager,
                base_url=settings.ollama_base_url,
                timeout=settings.llm_timeout
            )
            
            # Initialize chains using the new Runnable syntax
            self.extraction_chain = (
                RunnablePassthrough.assign(
                    text=lambda x: x["text"],
                    company_name=lambda x: x.get("company_name", ""),
                    year=lambda x: x.get("year", "")
                )
                | EXTRACTION_PROMPT
                | self.llm
            )
            
            self.comparison_chain = (
                RunnablePassthrough.assign(
                    company_name=lambda x: x["current_year"].company_name,
                    current_year_data=lambda x: x["current_year"].to_dict(),
                    previous_year_data=lambda x: x["previous_year"].to_dict()
                )
                | COMPARISON_PROMPT
                | self.llm
            )
            
            self.summary_chain = (
                RunnablePassthrough.assign(
                    company_name=lambda x: x["statements"][0].company_name,
                    financial_data=lambda x: json.dumps([s.to_dict() for s in x["statements"]])
                )
                | COMPANY_SUMMARY_PROMPT
                | self.llm
            )
            
            self.validation_chain = (
                RunnablePassthrough.assign(
                    extracted_data=lambda x: json.dumps(x["data"])
                )
                | VALIDATION_PROMPT
                | self.llm
            )
            
            logger.info("LLM Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM Service: {str(e)}")
            raise

    async def extract_financial_data(self, text: str, company_name: str = None, year: str = None) -> Dict[str, Any]:
        """Extract structured financial data from text"""
        try:
            result = await self.extraction_chain.ainvoke({
                "text": text,
                "company_name": company_name,
                "year": year
            })
            
            # Clean the JSON output
            json_start = result.find('{')
            json_end = result.rfind('}') + 1
            json_str = result[json_start:json_end]
            
            return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            raise ValueError(f"Failed to extract financial data: {str(e)}")

    async def generate_comparison(self, current_year: FinancialStatement, previous_year: FinancialStatement) -> str:
        """Generate financial comparison analysis"""
        return await self.comparison_chain.ainvoke({
            "current_year": current_year,
            "previous_year": previous_year
        })

    async def generate_company_summary(self, statements: List[FinancialStatement]) -> str:
        """Generate company financial summary"""
        return await self.summary_chain.ainvoke({
            "statements": statements
        })

    async def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extracted financial data"""
        result = await self.validation_chain.ainvoke({
            "data": data
        })
        
        # Clean the JSON output
        json_start = result.find('{')
        json_end = result.rfind('}') + 1
        json_str = result[json_start:json_end]
        
        return json.loads(json_str)