"""Tools for financial document analysis: PDF reader and optional search."""
import os
from dotenv import load_dotenv
load_dotenv()

from crewai.tools import tool

# Optional: web search (requires SERPER_API_KEY in .env)
try:
    from crewai_tools.tools.serper_dev_tool import SerperDevTool
    search_tool = SerperDevTool()
except Exception:
    search_tool = None


@tool("Read Financial Document")
def read_financial_document(path: str) -> str:
    """Read and return the text content from a PDF financial document.
    Use this tool with the exact file path provided in the task (e.g. the path to the uploaded document).
    Args:
        path: Full path to the PDF file (e.g. data/uploads/financial_document_xxx.pdf).
    Returns:
        The full text content of the financial document.
    """
    from langchain_community.document_loaders import PyPDFLoader

    if not path or not os.path.isfile(path):
        return f"Error: File not found at path: {path}"

    loader = PyPDFLoader(file_path=path)
    docs = loader.load()

    full_report = ""
    for data in docs:
        content = data.page_content or ""
        while "\n\n" in content:
            content = content.replace("\n\n", "\n")
        full_report += content + "\n"

    return full_report.strip() or "(No text extracted from PDF)"


# Legacy class names for backwards compatibility; primary tool is read_financial_document
class FinancialDocumentTool:
    read_data_tool = read_financial_document
