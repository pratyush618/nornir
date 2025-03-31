use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;
use std::sync::{Arc, Mutex};
use std::thread;
use crossbeam_channel::{bounded, Sender, Receiver};
use std::sync::atomic::{AtomicBool, Ordering};

// Job type that can hold a Python callback
type Job = PyObject;

// Message type for communication between threads
enum Message {
    NewJob(Job),
    Terminate,
}

// Worker struct to handle individual threads
struct Worker {
    id: usize,
    thread: Option<thread::JoinHandle<()>>,
}

impl Worker {
    fn new(id: usize, receiver: Arc<Mutex<Receiver<Message>>>, job_count: Arc<Mutex<usize>>) -> Worker {
        // Create a new thread that will process jobs
        let thread = thread::spawn(move || {
            loop {
                // Get a message from the channel
                let message = match receiver.lock().unwrap().recv() {
                    Ok(msg) => msg,
                    Err(_) => {
                        println!("Worker {}: Channel closed, exiting", id);
                        break;
                    }
                };

                match message {
                    Message::NewJob(job) => {
                        // Execute the Python callback with GIL
                        Python::with_gil(|py| {
                            if let Err(e) = job.call0(py) {
                                eprintln!("Worker {}: Job execution error: {:?}", id, e);
                            }
                        });

                        // Decrement job count after executing
                        let mut count = job_count.lock().unwrap();
                        *count = count.saturating_sub(1);
                    }
                    Message::Terminate => {
                        println!("Worker {} terminating", id);
                        break;
                    }
                }
            }
        });

        Worker {
            id,
            thread: Some(thread),
        }
    }
}

// Thread pool implementation
struct ThreadPool {
    workers: Vec<Worker>,
    sender: Option<Sender<Message>>,
    is_running: Arc<AtomicBool>,
    job_count: Arc<Mutex<usize>>,
}

impl ThreadPool {
    fn new(size: usize) -> Result<ThreadPool, String> {
        if size == 0 {
            return Err("Thread pool size must be greater than 0".to_string());
        }

        // Get CPU count and calculate recommended maximum
        let cpu_count = num_cpus::get();
        let max_recommended = cpu_count * 2;

        // Warn if thread count exceeds recommended maximum
        if size > max_recommended {
            eprintln!(
                "Warning: Requested thread count ({}) exceeds recommended maximum ({}) for {} CPUs",
                size, max_recommended, cpu_count
            );
        }

        println!("Creating thread pool with {} workers (CPU count: {})", size, cpu_count);

        // Create channel with appropriate buffer size
        let (sender, receiver) = bounded::<Message>(size * 2); // Increase buffer size based on thread count
        let receiver = Arc::new(Mutex::new(receiver));
        let mut workers = Vec::with_capacity(size);
        let is_running = Arc::new(AtomicBool::new(true));
        let job_count = Arc::new(Mutex::new(0));

        // Create exactly the number of workers requested
        for id in 0..size {
            workers.push(Worker::new(
                id,
                Arc::clone(&receiver),
                Arc::clone(&job_count)
            ));
        }

        Ok(ThreadPool {
            workers,
            sender: Some(sender),
            is_running,
            job_count,
        })
    }

    fn execute(&self, job: Job) -> Result<(), String> {
        if !self.is_running.load(Ordering::SeqCst) {
            return Err("ThreadPool has been shutdown".to_string());
        }

        // Increment the job counter
        {
            let mut count = self.job_count.lock().unwrap();
            *count += 1;
        }

        // Send the job to the channel
        match &self.sender {
            Some(sender) => {
                if let Err(e) = sender.send(Message::NewJob(job)) {
                    return Err(format!("Failed to send job: {:?}", e));
                }
                Ok(())
            }
            None => Err("ThreadPool has been shutdown".to_string()),
        }
    }

    fn shutdown(&mut self) {
        println!("Shutting down thread pool");
        self.is_running.store(false, Ordering::SeqCst);
        
        // Send termination messages to all workers
        if let Some(sender) = &self.sender {
            for _ in &self.workers {
                let _ = sender.send(Message::Terminate);
            }
        }
        
        // Drop the sender to close the channel
        self.sender.take();
        
        // Join all worker threads
        for worker in &mut self.workers {
            if let Some(thread) = worker.thread.take() {
                match thread.join() {
                    Ok(_) => println!("Worker thread joined successfully"),
                    Err(e) => eprintln!("Error joining worker thread: {:?}", e),
                }
            }
        }
        
        // Reset job count
        let mut count = self.job_count.lock().unwrap();
        *count = 0;
    }

    fn active_jobs(&self) -> usize {
        *self.job_count.lock().unwrap()
    }
}

impl Drop for ThreadPool {
    fn drop(&mut self) {
        if self.sender.is_some() {
            self.shutdown();
        }
    }
}

// Python module implementation
#[pyclass]
struct Aqueue {
    pool: Option<ThreadPool>,
    size: usize,
}

#[pymethods]
impl Aqueue {
    #[new]
    fn new(max_workers: Option<usize>) -> PyResult<Self> {
        // Use provided thread count or CPU count as default
        let size = max_workers.unwrap_or_else(|| num_cpus::get());
        println!("Initializing thread pool with requested size: {}", size);
        
        match ThreadPool::new(size) {
            Ok(pool) => {
                let aqueue = Aqueue { pool: Some(pool), size };
                println!("Thread pool created with {} workers", size);
                Ok(aqueue)
            },
            Err(e) => Err(PyRuntimeError::new_err(e)),
        }
    }

    #[getter]
    fn pool_size(&self) -> usize {
        self.size
    }

    #[getter]
    fn active_workers(&self) -> usize {
        if let Some(pool) = &self.pool {
            pool.workers.len()
        } else {
            0
        }
    }

    #[getter]
    fn running(&self) -> bool {
        if let Some(pool) = &self.pool {
            pool.is_running.load(Ordering::SeqCst)
        } else {
            false
        }
    }

    fn add_job(&self, job: Job) -> PyResult<()> {
        if let Some(pool) = &self.pool {
            match pool.execute(job) {
                Ok(_) => Ok(()),
                Err(e) => Err(PyRuntimeError::new_err(e)),
            }
        } else {
            Err(PyRuntimeError::new_err("ThreadPool has been shutdown"))
        }
    }

    fn active_jobs(&self) -> usize {
        if let Some(pool) = &self.pool {
            *pool.job_count.lock().unwrap()
        } else {
            0
        }
    }

    fn __enter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __exit__(
        &mut self,
        _exc_type: Option<&PyAny>,
        _exc_val: Option<&PyAny>,
        _exc_tb: Option<&PyAny>,
    ) -> PyResult<()> {
        if let Some(mut pool) = self.pool.take() {
            pool.shutdown();
        }
        Ok(())
    }
}

/// A Python module implemented in Rust.
#[pymodule]
fn nornir(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Aqueue>()?;
    Ok(())
}