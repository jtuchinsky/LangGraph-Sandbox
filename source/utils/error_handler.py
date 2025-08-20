import traceback
import logging
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from datetime import datetime
import asyncio


class ErrorType(Enum):
    """Типы ошибок"""
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"
    TIMEOUT_ERROR = "timeout_error"
    AUTHENTICATION_ERROR = "auth_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    VALIDATION_ERROR = "validation_error"
    FILE_ERROR = "file_error"
    MCP_ERROR = "mcp_error"
    LLM_ERROR = "llm_error"
    UNKNOWN_ERROR = "unknown_error"


class RecoveryStrategy(Enum):
    """Стратегии восстановления после ошибок"""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    FAIL = "fail"
    SWITCH_LLM = "switch_llm"
    USE_CACHE = "use_cache"


class ErrorContext:
    """Контекст ошибки"""
    def __init__(self, error: Exception, error_type: ErrorType, 
                 component: str, operation: str, metadata: Dict[str, Any] = None):
        self.error = error
        self.error_type = error_type
        self.component = component
        self.operation = operation
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()


class ErrorHandler:
    """Обработчик ошибок с механизмами восстановления"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_history: List[ErrorContext] = []
        self.recovery_strategies: Dict[ErrorType, RecoveryStrategy] = self._default_strategies()
        self.fallback_handlers: Dict[str, Callable] = {}
        self.max_retries = 3
        self.retry_delays = [1, 2, 5]  # seconds
    
    def _default_strategies(self) -> Dict[ErrorType, RecoveryStrategy]:
        """Стратегии восстановления по умолчанию"""
        return {
            ErrorType.NETWORK_ERROR: RecoveryStrategy.RETRY,
            ErrorType.API_ERROR: RecoveryStrategy.RETRY,
            ErrorType.TIMEOUT_ERROR: RecoveryStrategy.RETRY,
            ErrorType.AUTHENTICATION_ERROR: RecoveryStrategy.FAIL,
            ErrorType.RATE_LIMIT_ERROR: RecoveryStrategy.RETRY,
            ErrorType.VALIDATION_ERROR: RecoveryStrategy.FAIL,
            ErrorType.FILE_ERROR: RecoveryStrategy.RETRY,
            ErrorType.MCP_ERROR: RecoveryStrategy.FALLBACK,
            ErrorType.LLM_ERROR: RecoveryStrategy.SWITCH_LLM,
            ErrorType.UNKNOWN_ERROR: RecoveryStrategy.RETRY,
        }
    
    def classify_error(self, error: Exception, component: str = "") -> ErrorType:
        """Классификация типа ошибки"""
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()
        
        # Network errors
        if any(keyword in error_str for keyword in ["connection", "network", "dns", "socket"]):
            return ErrorType.NETWORK_ERROR
        
        # API errors
        if any(keyword in error_str for keyword in ["api", "400", "401", "403", "404", "500", "502", "503"]):
            if "401" in error_str or "unauthorized" in error_str:
                return ErrorType.AUTHENTICATION_ERROR
            elif "429" in error_str or "rate limit" in error_str:
                return ErrorType.RATE_LIMIT_ERROR
            return ErrorType.API_ERROR
        
        # Timeout errors
        if any(keyword in error_str for keyword in ["timeout", "timed out"]):
            return ErrorType.TIMEOUT_ERROR
        
        # File errors
        if any(keyword in error_str for keyword in ["file", "directory", "path", "permission"]):
            return ErrorType.FILE_ERROR
        
        # Validation errors
        if any(keyword in error_str for keyword in ["validation", "invalid", "malformed"]):
            return ErrorType.VALIDATION_ERROR
        
        # MCP errors
        if "mcp_clients" in component.lower() or "mcp_clients" in error_str:
            return ErrorType.MCP_ERROR
        
        # LLM errors
        if any(keyword in component.lower() for keyword in ["llm", "openai", "anthropic", "groq", "mistral"]):
            return ErrorType.LLM_ERROR
        
        return ErrorType.UNKNOWN_ERROR
    
    async def handle_error(self, error: Exception, component: str, operation: str, 
                          metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Обработать ошибку с применением стратегии восстановления"""
        
        error_type = self.classify_error(error, component)
        error_context = ErrorContext(error, error_type, component, operation, metadata)
        
        self.error_history.append(error_context)
        self.logger.error(f"Error in {component}.{operation}: {error}", exc_info=True)
        
        strategy = self.recovery_strategies.get(error_type, RecoveryStrategy.FAIL)
        
        return await self._apply_recovery_strategy(error_context, strategy)
    
    async def _apply_recovery_strategy(self, error_context: ErrorContext, 
                                     strategy: RecoveryStrategy) -> Dict[str, Any]:
        """Применить стратегию восстановления"""
        
        if strategy == RecoveryStrategy.RETRY:
            return await self._retry_operation(error_context)
        
        elif strategy == RecoveryStrategy.FALLBACK:
            return await self._use_fallback(error_context)
        
        elif strategy == RecoveryStrategy.SKIP:
            return {
                "success": False,
                "skipped": True,
                "error": str(error_context.error),
                "recovery": "skipped"
            }
        
        elif strategy == RecoveryStrategy.SWITCH_LLM:
            return {
                "success": False,
                "switch_llm": True,
                "error": str(error_context.error),
                "recovery": "switch_llm_suggested"
            }
        
        elif strategy == RecoveryStrategy.USE_CACHE:
            return await self._use_cache(error_context)
        
        else:  # FAIL
            return {
                "success": False,
                "fatal": True,
                "error": str(error_context.error),
                "recovery": "failed"
            }
    
    async def _retry_operation(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Повторить операцию с задержками"""
        component = error_context.component
        operation = error_context.operation
        
        # Count previous retries for this operation
        retry_count = sum(1 for ctx in self.error_history 
                         if ctx.component == component and ctx.operation == operation)
        
        if retry_count >= self.max_retries:
            return {
                "success": False,
                "max_retries_exceeded": True,
                "error": str(error_context.error),
                "recovery": "retry_failed"
            }
        
        # Wait before retry
        if retry_count < len(self.retry_delays):
            delay = self.retry_delays[retry_count]
        else:
            delay = self.retry_delays[-1]
        
        await asyncio.sleep(delay)
        
        return {
            "success": False,
            "retry": True,
            "retry_count": retry_count + 1,
            "retry_delay": delay,
            "error": str(error_context.error),
            "recovery": "retry_scheduled"
        }
    
    async def _use_fallback(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Использовать резервный обработчик"""
        fallback_key = f"{error_context.component}.{error_context.operation}"
        
        if fallback_key in self.fallback_handlers:
            try:
                fallback_handler = self.fallback_handlers[fallback_key]
                result = await fallback_handler(error_context)
                
                return {
                    "success": True,
                    "fallback_used": True,
                    "result": result,
                    "recovery": "fallback_success"
                }
                
            except Exception as fallback_error:
                return {
                    "success": False,
                    "fallback_failed": True,
                    "original_error": str(error_context.error),
                    "fallback_error": str(fallback_error),
                    "recovery": "fallback_failed"
                }
        
        return {
            "success": False,
            "no_fallback": True,
            "error": str(error_context.error),
            "recovery": "no_fallback_available"
        }
    
    async def _use_cache(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Использовать кэшированный результат"""
        # This would integrate with a caching system
        return {
            "success": False,
            "cache_miss": True,
            "error": str(error_context.error),
            "recovery": "cache_not_implemented"
        }
    
    def register_fallback_handler(self, component: str, operation: str, 
                                 handler: Callable):
        """Зарегистрировать резервный обработчик"""
        key = f"{component}.{operation}"
        self.fallback_handlers[key] = handler
    
    def set_recovery_strategy(self, error_type: ErrorType, strategy: RecoveryStrategy):
        """Установить стратегию восстановления для типа ошибки"""
        self.recovery_strategies[error_type] = strategy
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Получить статистику ошибок"""
        if not self.error_history:
            return {"total_errors": 0}
        
        stats = {
            "total_errors": len(self.error_history),
            "error_types": {},
            "components": {},
            "operations": {},
            "recent_errors": []
        }
        
        for error_ctx in self.error_history:
            # Count by error type
            error_type = error_ctx.error_type.value
            stats["error_types"][error_type] = stats["error_types"].get(error_type, 0) + 1
            
            # Count by component
            component = error_ctx.component
            stats["components"][component] = stats["components"].get(component, 0) + 1
            
            # Count by operation
            operation = error_ctx.operation
            stats["operations"][operation] = stats["operations"].get(operation, 0) + 1
        
        # Recent errors (last 10)
        for error_ctx in self.error_history[-10:]:
            stats["recent_errors"].append({
                "timestamp": error_ctx.timestamp.isoformat(),
                "type": error_ctx.error_type.value,
                "component": error_ctx.component,
                "operation": error_ctx.operation,
                "error": str(error_ctx.error)
            })
        
        return stats
    
    def clear_error_history(self, older_than_hours: int = 24):
        """Очистить историю ошибок"""
        cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
        
        self.error_history = [
            ctx for ctx in self.error_history 
            if ctx.timestamp.timestamp() > cutoff_time
        ]