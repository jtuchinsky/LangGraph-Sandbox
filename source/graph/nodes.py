import json
from typing import Dict, Any
from .state import WorkflowState
from ..agents import BaseLLMAgent


class WorkflowNodes:
    def __init__(self, llm_agent: BaseLLMAgent, mcp_host=None):
        self.llm_agent = llm_agent
        self.mcp_host = mcp_host
    
    async def input_node(self, state: WorkflowState) -> Dict[str, Any]:
        """📝 Входное описание - Process input and prepare for classification"""
        try:
            # Log input to context
            state.context_history.append({
                "node": "input",
                "timestamp": "now",
                "data": {"input_description": state.input_description}
            })
            
            # Validate input
            if not state.input_description.strip():
                state.errors.append("Empty input description provided")
                return {"state": state}
            
            return {"state": state}
            
        except Exception as e:
            state.errors.append(f"Input node error: {str(e)}")
            return {"state": state}
    
    async def work_type_classification_node(self, state: WorkflowState) -> Dict[str, Any]:
        """🔍 Узел классификации типа работы"""
        try:
            prompt = f"""
Analyze the following task description and classify the type of work needed.

Task: {state.input_description}

Classify into one of these categories:
1. file_operations - Working with files (read, create, modify, delete)
2. web_search - Searching for information on the internet
3. data_processing - Processing or analyzing data
4. code_generation - Writing or modifying code
5. communication - Sending messages, emails, or communications
6. system_operations - System administration or configuration tasks
7. other - Any other type of task

Respond with JSON format:
{{
    "work_type": "category_name",
    "confidence": 0.95,
    "reasoning": "explanation of classification"
}}
"""
            
            response = self.llm_agent.invoke(prompt)
            
            try:
                result = json.loads(response)
                state.work_type = result.get("work_type")
                state.work_type_confidence = result.get("confidence", 0.0)
                
                state.llm_responses.append({
                    "node": "work_type_classification",
                    "response": result
                })
                
            except json.JSONDecodeError:
                state.errors.append("Failed to parse work type classification response")
                state.work_type = "other"
                state.work_type_confidence = 0.1
            
            return {"state": state}
            
        except Exception as e:
            state.errors.append(f"Work type classification error: {str(e)}")
            state.work_type = "other"
            state.work_type_confidence = 0.0
            return {"state": state}
    
    async def category_classification_node(self, state: WorkflowState) -> Dict[str, Any]:
        """📂 Узел классификации категории"""
        try:
            prompt = f"""
Based on the work type "{state.work_type}" and the original task, classify the specific category.

Task: {state.input_description}
Work Type: {state.work_type}

For each work type, classify into subcategories:

file_operations: read, write, create, delete, modify, copy, move
web_search: general_search, news_search, academic_search, product_search, image_search
data_processing: analysis, transformation, visualization, filtering, aggregation
code_generation: create_new, modify_existing, debug, test, documentation
communication: email, chat, notification, report, presentation
system_operations: install, configure, monitor, backup, security
other: general, custom, unknown

Respond with JSON format:
{{
    "category": "specific_category",
    "confidence": 0.95,
    "reasoning": "explanation of category classification"
}}
"""
            
            response = self.llm_agent.invoke(prompt)
            
            try:
                result = json.loads(response)
                state.category = result.get("category")
                state.category_confidence = result.get("confidence", 0.0)
                
                state.llm_responses.append({
                    "node": "category_classification",
                    "response": result
                })
                
            except json.JSONDecodeError:
                state.errors.append("Failed to parse category classification response")
                state.category = "general"
                state.category_confidence = 0.1
            
            return {"state": state}
            
        except Exception as e:
            state.errors.append(f"Category classification error: {str(e)}")
            state.category = "general"
            state.category_confidence = 0.0
            return {"state": state}
    
    async def search_type_determination_node(self, state: WorkflowState) -> Dict[str, Any]:
        """🎯 Узел определения типа поиска"""
        try:
            prompt = f"""
Based on the work type "{state.work_type}" and category "{state.category}", determine the optimal search/execution strategy.

Task: {state.input_description}
Work Type: {state.work_type}
Category: {state.category}

Determine the search type:
1. local_only - Task can be completed with local resources only
2. web_required - Requires internet search for current information
3. hybrid - Combination of local and web resources
4. mcp_tools - Requires specific MCP tools
5. llm_only - Can be completed with LLM reasoning alone

Respond with JSON format:
{{
    "search_type": "strategy_name",
    "confidence": 0.95,
    "reasoning": "explanation of search strategy",
    "required_tools": ["tool1", "tool2"],
    "estimated_complexity": "low|medium|high"
}}
"""
            
            response = self.llm_agent.invoke(prompt)
            
            try:
                result = json.loads(response)
                state.search_type = result.get("search_type")
                state.search_type_confidence = result.get("confidence", 0.0)
                
                state.llm_responses.append({
                    "node": "search_type_determination",
                    "response": result
                })
                
            except json.JSONDecodeError:
                state.errors.append("Failed to parse search type determination response")
                state.search_type = "llm_only"
                state.search_type_confidence = 0.1
            
            return {"state": state}
            
        except Exception as e:
            state.errors.append(f"Search type determination error: {str(e)}")
            state.search_type = "llm_only"
            state.search_type_confidence = 0.0
            return {"state": state}
    
    async def confidence_calculation_node(self, state: WorkflowState) -> Dict[str, Any]:
        """📊 Узел расчёта уверенности"""
        try:
            # Calculate overall confidence based on individual confidences
            confidences = [
                state.work_type_confidence,
                state.category_confidence,
                state.search_type_confidence
            ]
            
            # Filter out zero confidences and calculate weighted average
            valid_confidences = [c for c in confidences if c > 0]
            
            if valid_confidences:
                state.overall_confidence = sum(valid_confidences) / len(valid_confidences)
            else:
                state.overall_confidence = 0.0
            
            # Adjust confidence based on errors
            error_penalty = len(state.errors) * 0.1
            state.overall_confidence = max(0.0, state.overall_confidence - error_penalty)
            
            # Create final result JSON
            state.result = {
                "input_description": state.input_description,
                "classification": {
                    "work_type": state.work_type,
                    "work_type_confidence": state.work_type_confidence,
                    "category": state.category,
                    "category_confidence": state.category_confidence,
                    "search_type": state.search_type,
                    "search_type_confidence": state.search_type_confidence
                },
                "overall_confidence": state.overall_confidence,
                "errors": state.errors,
                "session_id": state.session_id,
                "selected_llm": state.selected_llm
            }
            
            return {"state": state}
            
        except Exception as e:
            state.errors.append(f"Confidence calculation error: {str(e)}")
            state.overall_confidence = 0.0
            state.result = {
                "error": "Failed to calculate confidence",
                "errors": state.errors
            }
            return {"state": state}