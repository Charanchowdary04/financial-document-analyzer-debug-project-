"""CrewAI tasks for financial document analysis."""
from crewai import Task
from agents import financial_analyst, verifier
from tools import read_financial_document

# Task context: {query} and {file_path} are filled from crew kickoff inputs.

analyze_financial_document = Task(
    description="""Analyze the financial document located at: {file_path}.

First, use the Read Financial Document tool with path exactly: {file_path} to load the document text.
Then address the user's request: {query}

Provide a clear, structured analysis that includes:
- Summary of the document (company, period, type of report)
- Key financial metrics and highlights from the document
- Investment-relevant insights and risks based on the content
- Actionable recommendations only where supported by the document""",

    expected_output="A well-structured analysis with: 1) Document summary, 2) Key metrics and highlights, 3) Investment insights and risks, 4) Evidence-based recommendations. Use bullet points and short paragraphs.",

    agent=financial_analyst,
    tools=[read_financial_document],
)

verification = Task(
    description="""Verify the document at path: {file_path}.

Use the Read Financial Document tool with path: {file_path}.
Confirm whether it appears to be a financial report (10-K, 10-Q, earnings release, annual report, etc.) and state the document type and company/period if visible.""",

    expected_output="Short verification note: document type, company/period if identifiable, and whether it is suitable for financial analysis.",

    agent=verifier,
    tools=[read_financial_document],
)
