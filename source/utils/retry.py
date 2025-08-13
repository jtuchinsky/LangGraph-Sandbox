import asyncio
import random
from typing import Callable, Any, Optional, List
from functools import wraps


class RetryManager:
    """Менеджер повторных попыток с различными стратегиями"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    async def retry_with_exponential_backoff(self, 
                                           func: Callable,
                                           *args, 
                                           max_retries: Optional[int] = None,
                                           base_delay: Optional[float] = None,
                                           max_delay: float = 60.0,
                                           jitter: bool = True,
                                           **kwargs) -> Any:
        """Повторить функцию с экспоненциальной задержкой"""
        
        max_retries = max_retries or self.max_retries
        base_delay = base_delay or self.base_delay
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                
                if attempt == max_retries:
                    break
                
                # Calculate delay with exponential backoff
                delay = min(base_delay * (2 ** attempt), max_delay)
                
                # Add jitter to prevent thundering herd
                if jitter:
                    delay *= (0.5 + random.random() * 0.5)
                
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                await asyncio.sleep(delay)
        
        raise last_exception
    
    async def retry_with_linear_backoff(self,
                                      func: Callable,
                                      *args,
                                      max_retries: Optional[int] = None,
                                      delay: Optional[float] = None,
                                      **kwargs) -> Any:
        """Повторить функцию с линейной задержкой"""
        
        max_retries = max_retries or self.max_retries
        delay = delay or self.base_delay
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                
                if attempt == max_retries:
                    break
                
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        raise last_exception
    
    async def retry_with_custom_delays(self,
                                     func: Callable,
                                     delays: List[float],
                                     *args,
                                     **kwargs) -> Any:
        """Повторить функцию с пользовательскими задержками"""
        
        last_exception = None
        
        for attempt, delay in enumerate(delays):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                
                if attempt == len(delays) - 1:
                    break
                
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        # Try one final time without delay
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
        
        raise last_exception


def retry_on_exception(max_retries: int = 3, 
                      base_delay: float = 1.0,
                      exceptions: tuple = (Exception,),
                      backoff: str = "exponential"):
    """Декоратор для повторных попыток"""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            retry_manager = RetryManager(max_retries, base_delay)
            
            if backoff == "exponential":
                return await retry_manager.retry_with_exponential_backoff(func, *args, **kwargs)
            elif backoff == "linear":
                return await retry_manager.retry_with_linear_backoff(func, *args, **kwargs)
            else:
                raise ValueError(f"Unknown backoff strategy: {backoff}")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, run in event loop
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Convenience decorators for common retry patterns
def retry_on_network_error(max_retries: int = 3, base_delay: float = 1.0):
    """Повторить при сетевых ошибках"""
    network_exceptions = (
        ConnectionError,
        TimeoutError,
        OSError,
    )
    return retry_on_exception(max_retries, base_delay, network_exceptions)


def retry_on_api_error(max_retries: int = 3, base_delay: float = 2.0):
    """Повторить при API ошибках"""
    api_exceptions = (
        ConnectionError,
        TimeoutError,
        Exception,  # Broad exception for API errors
    )
    return retry_on_exception(max_retries, base_delay, api_exceptions)