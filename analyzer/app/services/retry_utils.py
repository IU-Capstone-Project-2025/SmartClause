import asyncio
import functools
import logging
from typing import Any, Callable, TypeVar, Awaitable
from ..core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryMixin:
    """Mixin class providing retry functionality with exponential backoff"""
    
    async def retry_async(
        self,
        func: Callable[..., Awaitable[T]],
        *args,
        max_retries: int = None,
        initial_delay: float = None,
        backoff_factor: float = None,
        timeout: float = None,
        **kwargs
    ) -> T:
        """
        Retry an async function with exponential backoff
        
        Args:
            func: The async function to retry
            *args: Positional arguments for the function
            max_retries: Maximum number of retry attempts (default from settings)
            initial_delay: Initial delay between retries (default from settings)
            backoff_factor: Exponential backoff factor (default from settings)
            timeout: Timeout for each attempt (optional)
            **kwargs: Keyword arguments for the function
        """
        max_retries = max_retries or settings.max_retries
        initial_delay = initial_delay or settings.retry_delay
        backoff_factor = backoff_factor or settings.retry_backoff_factor
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                if timeout:
                    return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
                else:
                    return await func(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries:
                    delay = initial_delay * (backoff_factor ** attempt)
                    error_msg = str(e) if str(e).strip() else type(e).__name__
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed: {error_msg}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    await asyncio.sleep(delay)
                else:
                    error_msg = str(e) if str(e).strip() else type(e).__name__
                    logger.error(f"All {max_retries + 1} attempts failed. Last error: {error_msg}")
        
        raise last_exception


class ConcurrencyManager:
    """Manages concurrency limits for different types of operations"""
    
    def __init__(self):
        # Create semaphores for different operation types
        self.global_semaphore = asyncio.Semaphore(settings.max_concurrent_threads)
        self.llm_semaphore = asyncio.Semaphore(settings.max_concurrent_llm_calls)
        self.embedding_semaphore = asyncio.Semaphore(settings.max_concurrent_embeddings)
        
        logger.info(
            f"Initialized concurrency manager - "
            f"Global: {settings.max_concurrent_threads}, "
            f"LLM: {settings.max_concurrent_llm_calls}, "
            f"Embeddings: {settings.max_concurrent_embeddings}"
        )
    
    async def with_global_limit(self, coro: Awaitable[T]) -> T:
        """Execute coroutine with global concurrency limit"""
        async with self.global_semaphore:
            return await coro
    
    async def with_llm_limit(self, coro: Awaitable[T]) -> T:
        """Execute coroutine with LLM concurrency limit"""
        async with self.llm_semaphore:
            return await coro
    
    async def with_embedding_limit(self, coro: Awaitable[T]) -> T:
        """Execute coroutine with embedding concurrency limit"""
        async with self.embedding_semaphore:
            return await coro
    
    async def batch_execute(
        self, 
        coros: list[Awaitable[T]], 
        semaphore: asyncio.Semaphore = None,
        return_exceptions: bool = True
    ) -> list[T]:
        """
        Execute a batch of coroutines with optional semaphore limiting
        
        Args:
            coros: List of coroutines to execute
            semaphore: Optional semaphore to limit concurrency
            return_exceptions: Whether to return exceptions instead of raising them
        """
        if semaphore:
            async def limited_coro(coro):
                async with semaphore:
                    return await coro
            coros = [limited_coro(coro) for coro in coros]
        
        return await asyncio.gather(*coros, return_exceptions=return_exceptions)


# Global concurrency manager instance
concurrency_manager = ConcurrencyManager()


def with_retry(
    max_retries: int = None,
    initial_delay: float = None,
    backoff_factor: float = None,
    timeout: float = None
):
    """
    Decorator for adding retry functionality to async functions
    
    Usage:
        @with_retry(max_retries=3, timeout=10)
        async def my_function():
            # function implementation
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            retry_mixin = RetryMixin()
            return await retry_mixin.retry_async(
                func, *args,
                max_retries=max_retries,
                initial_delay=initial_delay,
                backoff_factor=backoff_factor,
                timeout=timeout,
                **kwargs
            )
        return wrapper
    return decorator


def with_concurrency_limit(semaphore_type: str = "global"):
    """
    Decorator for adding concurrency limits to async functions
    
    Args:
        semaphore_type: Type of semaphore to use ("global", "llm", "embedding")
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            if semaphore_type == "llm":
                return await concurrency_manager.with_llm_limit(func(*args, **kwargs))
            elif semaphore_type == "embedding":
                return await concurrency_manager.with_embedding_limit(func(*args, **kwargs))
            else:  # global
                return await concurrency_manager.with_global_limit(func(*args, **kwargs))
        return wrapper
    return decorator 