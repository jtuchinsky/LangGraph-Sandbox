from typing import Dict, Any
from langgraph.graph import StateGraph, END
from .state import WorkflowState
from .nodes import WorkflowNodes
from ..agents import BaseLLMAgent


class WorkflowGraph:
    def __init__(self, llm_agent: BaseLLMAgent, mcp_host=None):
        self.llm_agent = llm_agent
        self.mcp_host = mcp_host
        self.nodes = WorkflowNodes(llm_agent, mcp_host)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("input", self.nodes.input_node)
        workflow.add_node("work_type_classification", self.nodes.work_type_classification_node)
        workflow.add_node("category_classification", self.nodes.category_classification_node)
        workflow.add_node("search_type_determination", self.nodes.search_type_determination_node)
        workflow.add_node("confidence_calculation", self.nodes.confidence_calculation_node)
        
        # Set entry point
        workflow.set_entry_point("input")
        
        # Add edges (sequential flow)
        workflow.add_edge("input", "work_type_classification")
        workflow.add_edge("work_type_classification", "category_classification")
        workflow.add_edge("category_classification", "search_type_determination")
        workflow.add_edge("search_type_determination", "confidence_calculation")
        workflow.add_edge("confidence_calculation", END)
        
        return workflow.compile()
    
    async def run(self, input_description: str, session_id: str = "default") -> Dict[str, Any]:
        """Run the workflow with given input"""
        
        # Create initial state
        initial_state = WorkflowState(
            input_description=input_description,
            session_id=session_id,
            selected_llm=self.llm_agent.get_provider_name()
        )
        
        try:
            # Run the graph
            result = await self.graph.ainvoke({"state": initial_state})
            final_state = result["state"]
            
            return final_state.result
            
        except Exception as e:
            return {
                "error": f"Workflow execution failed: {str(e)}",
                "input_description": input_description,
                "session_id": session_id
            }
    
    def get_graph_visualization(self) -> str:
        """Get a text representation of the graph structure"""
        return """
📝 Входное описание (input)
      ↓
🔍 Узел классификации типа работы (work_type_classification)
      ↓
📂 Узел классификации категории (category_classification)
      ↓
🎯 Узел определения типа поиска (search_type_determination)
      ↓
📊 Узел расчёта уверенности (confidence_calculation)
      ↓
✅ JSON-результат (END)
"""