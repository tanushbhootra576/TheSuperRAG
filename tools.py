import ast
import re
import math
import statistics
import datetime
import io
import sys
from dateutil.parser import parse
from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    """Evaluate mathematical expressions, unit conversions, and percentage calculations. Do not use for anything else."""
    try:
        # Whitelist characters for safety
        if not re.match(r'^[\d\.\+\-\*\/\(\)\s\^e]+$', expression):
            return "Error: Invalid characters in expression."
        # Using eval is safe if strictly validated
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    except Exception as e:
        return f"Error computing expression: {e}"

@tool
def datetime_parser(date_query: str) -> str:
    """Answer questions about dates and time parsing. Example: 'days between X and Y'"""
    # Simply using dateutil to parse a date, for complex ones LLM parses the results.
    try:
        parsed = parse(date_query, fuzzy=True)
        return f"Parsed Date: {parsed.isoformat()}"
    except Exception as e:
        return f"Error parsing date: {e}"

@tool
def web_search_tool(query: str) -> str:
    """Perform a web search using DuckDuckGo when internal documents lack confidence or the router explicitly requested a web search. Returns top 3 results."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        formatted = []
        for r in results:
            formatted.append(f"[Web: {r.get('title', 'Untitled')}]\nURL: {r.get('href', '')}\nSnippet: {r.get('body', '')}")
        return "\n\n".join(formatted) if formatted else "No web results found."
    except ImportError:
        return "Error: duckduckgo-search package not installed."
    except Exception as e:
        return f"Error performing web search: {e}"

@tool
def python_executor(code: str) -> str:
    """Execute python pandas queries for data analysis. Whitelisted: pandas, numpy, math, statistics. Returns stdout."""
    # Safety checks
    forbidden_patterns = [
        r"import\s+(?!pandas|numpy|math|statistics)",
        r"__import__",
        r"open\(",
        r"read_csv",
        r"read_excel",
        r"requests",
        r"urllib",
        r"os\.",
        r"sys\.",
        r"subprocess"
    ]
    for pattern in forbidden_patterns:
        if re.search(pattern, code):
            return "Error: Forbidden operations detected (imports, file IO, network calls not allowed)."
            
    # Restricted execution environment
    try:
        import pandas as pd
        import numpy as np
    except ImportError:
        pass # Handle gracefully if not installed
    
    safe_globals = {
        "__builtins__": {"print": print, "range": range, "len": len, "sum": sum, "min": min, "max": max, "abs": abs, "list": list, "dict": dict, "set": set, "tuple": tuple, "int": int, "float": float, "str": str, "bool": bool},
        "math": math,
        "statistics": statistics
    }
    if 'pd' in locals(): safe_globals['pd'] = pd
    if 'np' in locals(): safe_globals['np'] = np
    
    # Capture stdout
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout
    try:
        exec(code, safe_globals, {})
        output = new_stdout.getvalue()
        return output.strip() if output.strip() else "Executed successfully without output."
    except Exception as e:
        return f"Execution Error: {e}"
    finally:
        sys.stdout = old_stdout
