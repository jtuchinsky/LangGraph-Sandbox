from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class WorkflowState(BaseModel):
    """State class for the workflow graph"""
    
    # Input data
    input_description: str = ""
    
    # Classification results
    work_type: Optional[str] = None
    work_type_confidence: float = 0.0
    
    category: Optional[str] = None
    category_confidence: float = 0.0
    
    search_type: Optional[str] = None
    search_type_confidence: float = 0.0
    
    # Final confidence calculation
    overall_confidence: float = 0.0
    
    # Results and metadata
    result: Optional[Dict[str, Any]] = None
    errors: List[str] = []
    
    # Context and memory
    context_history: List[Dict[str, Any]] = []
    session_id: str = ""
    
    # LLM and MCP related
    selected_llm: str = "openai"
    llm_responses: List[Dict[str, Any]] = []
    mcp_tool_calls: List[Dict[str, Any]] = []
    
    class Config:
        arbitrary_types_allowed = True