from typing import Optional, Callable, Any

class Aqueue:
    """A high-performance thread pool implementation for Python.
    
    This class provides a thread pool that can execute Python callables concurrently.
    It manages a fixed number of worker threads and provides a queue for submitting jobs.
    
    Warning:
        Setting max_workers higher than (CPU count * 2) will generate a warning as it
        may not provide better performance and could cause resource contention.
    
    Example:
        >>> with Aqueue(4) as pool:  # Creates a pool with 4 worker threads
        ...     pool.add_job(lambda: print("Hello"))
    """
    
    def __init__(self, max_workers: Optional[int] = None) -> None:
        """Initialize the thread pool.
        
        Args:
            max_workers: The number of worker threads to create. If None, defaults to
                        the number of CPU cores available. A warning is issued if this
                        exceeds (CPU count * 2).
        """
        ...

    def add_job(self, job: Callable[[], Any]) -> None:
        """Add a job to the thread pool's queue.
        
        Args:
            job: A callable (function or method) that will be executed by one of the
                 worker threads.
        
        Raises:
            RuntimeError: If the thread pool has been shutdown.
        """
        ...

    def stop(self) -> None: ...

    def active_jobs(self) -> int:
        """Get the number of jobs currently being processed.
        
        Returns:
            The number of jobs that have been submitted but not yet completed.
        """
        ...

    def __enter__(self) -> 'Aqueue':
        """Context manager entry.
        
        Returns:
            The Aqueue instance itself.
        """
        ...

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Context manager exit.
        
        This ensures proper cleanup of the thread pool when used with a 'with' statement.
        """
        ...

    @property
    def pool_size(self) -> int:
        """Get the total number of worker threads in the pool.
        
        Returns:
            The number of worker threads configured for this thread pool.
        """
        ...

    @property
    def active_workers(self) -> int:
        """Get the number of currently active worker threads.
        
        Returns:
            The number of worker threads that are currently running.
        """
        ...

    @property
    def running(self) -> bool:
        """Check if the thread pool is currently running.
        
        Returns:
            True if the thread pool is active and accepting new jobs,
            False if it has been shutdown.
        """
        ... 