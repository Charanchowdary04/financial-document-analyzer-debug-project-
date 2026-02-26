"""CrewAI agents for financial document analysis."""
import os
from dotenv import load_dotenv
load_dotenv()

from crewai import Agent
from tools import read_financial_document

# Load LLM: CrewAI accepts model string (uses OPENAI_API_KEY or GOOGLE_API_KEY via env)
# Set OPENAI_API_KEY for OpenAI, or GOOGLE_API_KEY for Gemini
_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
if os.getenv("GOOGLE_API_KEY") and not os.getenv("OPENAI_API_KEY"):
    _model = os.getenv("LLM_MODEL", "gemini/gemini-1.5-flash")
llm = _model

financial_analyst = Agent(
    role="Senior Financial Analyst",
    goal="Provide accurate, evidence-based investment analysis and risk assessment based on the financial document. Address the user's query using the document path and content provided in the task.",
    verbose=True,
    memory=True,
    backstory=(
        "You are an experienced CFA with deep expertise in equity research, financial statements, and risk management. "
        "You base your recommendations on the actual numbers and disclosures in the report, and you clearly separate facts from assumptions. "
        "You comply with regulatory and professional standards when giving investment-related guidance."
    ),
    tools=[read_financial_document],
    llm=llm,
    max_iter=5,
    allow_delegation=False,
)

verifier = Agent(
    role="Financial Document Verifier",
    goal="Verify that the given document is a valid financial document and summarize its type and key identifiers.",
    verbose=True,
    memory=True,
    backstory=(
        "You are a compliance-oriented analyst who checks document type, presence of financial data, and basic structure before analysis."
    ),
    tools=[read_financial_document],
    llm=llm,
    max_iter=3,
    allow_delegation=False,
)
