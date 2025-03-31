import nornir
import time
import threading

# Simple worker wrapper
class Worker:
    def __init__(self, num_workers=4):
        print(f"Creating worker with {num_workers} threads")
        self.queue = nornir.Aqueue(num_workers)
        self.completion_flag = threading.Event()
        self.result = None

    def add_job(self, job):
        print("Adding job to queue")
        self.queue.add_job(job)
    
    def get_active_jobs(self):
        count = self.queue.active_jobs()
        print(f"Active jobs: {count}")
        return count
    
    def close(self):
        print("Closing worker")
        del self.queue
        print("Worker closed")

def simple_job():
    """A very simple job that just prints and returns"""
    print("Job started")
    time.sleep(0.5)  # Short sleep
    print("Job completed")
    return "Job result"

def job_with_callback(callback):
    """A job that sets a flag when done"""
    print("Callback job started")
    time.sleep(0.5)  # Short sleep
    print("Callback job completed")
    callback()
    return "Callback job result"

def diagnose_basic_operation():
    """Test if a single job works at all"""
    print("\n==== Testing basic operation ====")
    
    # Create worker with just 2 threads
    worker = Worker(2)
    
    # Define a job that sets a flag when complete
    completion_flag = threading.Event()
    
    def completion_callback():
        print("Setting completion flag")
        completion_flag.set()
    
    # Add the job
    print("Adding job with callback")
    worker.add_job(lambda: job_with_callback(completion_callback))
    
    # Check initial active jobs
    print(f"Initial active jobs: {worker.get_active_jobs()}")
    
    # Wait with timeout
    print("Waiting for job completion (max 5 seconds)...")
    job_completed = completion_flag.wait(5.0)
    
    if job_completed:
        print("Job completed successfully!")
    else:
        print("WARNING: Job did not complete within timeout!")
    
    # Check final active jobs
    print(f"Final active jobs: {worker.get_active_jobs()}")
    
    # Try to close the worker
    try:
        worker.close()
        print("Worker closed successfully")
    except Exception as e:
        print(f"Error closing worker: {e}")

def diagnose_multiple_jobs():
    """Test if multiple jobs work"""
    print("\n==== Testing multiple jobs ====")
    
    # Create worker with 4 threads
    worker = Worker(4)
    
    # Define counters
    completed_jobs = 0
    job_count = 5
    completion_lock = threading.Lock()
    all_completed = threading.Event()
    
    def completion_counter():
        nonlocal completed_jobs
        with completion_lock:
            completed_jobs += 1
            print(f"Job completed. Total completed: {completed_jobs}/{job_count}")
            if completed_jobs >= job_count:
                all_completed.set()
    
    # Add multiple jobs
    for i in range(job_count):
        print(f"Adding job {i+1}/{job_count}")
        worker.add_job(lambda: job_with_callback(completion_counter))
    
    # Wait with timeout
    print("Waiting for all jobs to complete (max 10 seconds)...")
    all_jobs_completed = all_completed.wait(10.0)
    
    if all_jobs_completed:
        print("All jobs completed successfully!")
    else:
        print(f"WARNING: Only {completed_jobs}/{job_count} jobs completed within timeout!")
    
    # Check active jobs
    print(f"Final active jobs reported by nornir: {worker.get_active_jobs()}")
    
    # Close the worker
    worker.close()

def diagnostics_report():
    """Print diagnostic information"""
    print("\n==== Diagnostics Report ====")
    try:
        import sys
        print(f"Python version: {sys.version}")
    except (ImportError, AttributeError) as e:
        print(f"Could not determine Python version: {e}")
    
    try:
        import os
        print(f"Operating system: {os.name}")
        if hasattr(os, 'uname'):
            print(f"OS details: {os.uname()}")
    except (ImportError, AttributeError) as e:
        print(f"Could not determine OS details: {e}")
    
    # Try to get nornir version or details
    try:
        print("Nornir details:")
        queue = nornir.Aqueue(1)
        print("  - Can create Aqueue: Yes")
        print(f"  - Active workers: {queue.active_workers}")
        print(f"  - Pool size: {queue.pool_size}")
        print(f"  - Running: {queue.running}")
        del queue
    except Exception as e:
        print(f"Error getting nornir details: {e}")

def simple_manual_test():
    """A simple test that you can manually interrupt if needed"""
    print("\n==== Simple Manual Test ====")
    print("This is a very simple test you can stop at any time with Ctrl+C")
    
    # Create worker
    worker = Worker(2)
    
    # Define a simple job
    def simple_counted_job(job_id):
        print(f"Job {job_id} started")
        # Simple calculation
        result = sum(i for i in range(1000))
        print(f"Job {job_id} finished with result: {result}")
        return result
    
    # Add a few jobs
    job_count = 3
    for i in range(job_count):
        print(f"Adding job {i+1}")
        worker.add_job(lambda idx=i: simple_counted_job(idx+1))
    
    # Monitor until user interrupts
    try:
        max_wait = 20  # Maximum 20 seconds
        start_time = time.time()
        while time.time() - start_time < max_wait:
            active = worker.get_active_jobs()
            print(f"Active jobs: {active}")
            if active == 0:
                print("All jobs complete!")
                break
            time.sleep(1)
        
        # Check if we timed out
        if time.time() - start_time >= max_wait:
            print("Test timed out, but will proceed with cleanup")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    finally:
        print("Attempting to close worker...")
        try:
            worker.close()
            print("Worker closed successfully")
        except Exception as e:
            print(f"Error closing worker: {e}")

if __name__ == "__main__":
    print("Starting Nornir diagnostic tests...")
    
    try:
        # Print diagnostics information
        diagnostics_report()
        
        # Run the simplest possible test
        simple_manual_test()
        
        # Run basic test
        diagnose_basic_operation()
        
        # Test multiple jobs
        diagnose_multiple_jobs()
        
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    except Exception as e:
        print(f"Error during tests: {e}")
    
    print("\nTests completed. Check the output above for any issues.")