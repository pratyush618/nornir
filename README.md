# Nornir Thread Pool

A high-performance thread pool implementation in Rust with Python bindings.

## Overview

Nornir is a lightweight and efficient thread pool implementation that provides a simple interface for parallel task execution in Python applications. It's written in Rust for performance and safety, with Python bindings for easy integration.

## Features

- Fast and efficient thread pool implementation in Rust
- Simple Python API
- Support for both CPU-bound and I/O-bound tasks
- Automatic thread management
- Thread-safe job queue
- Built-in diagnostics and monitoring

## Installation

```bash
pip install nornir
```

## Quick Start

```python
from nornir import Aqueue

# Create a thread pool with 4 workers
queue = Aqueue(4)

# Define a task
def my_task():
    # Your task code here
    return "Task completed"

# Add tasks to the queue
queue.add_job(my_task)

# Get number of active jobs
active_jobs = queue.active_jobs()

# Clean up when done
del queue
```

## Development

### Prerequisites

- Rust (latest stable version)
- Python 3.7+
- pip

### Building from Source

1. Clone the repository:
```bash
git clone https://github.com/pratyush618/nornir.git
cd nornir
```

2. Build the Rust library:
```bash
cargo build --release
```

3. Install the Python package:
```bash
pip install -e .
```

### Using Maturin

This project uses Maturin for building Python extensions in Rust. To build and install using Maturin:

```bash
# Install Maturin
pip install maturin

# Build and install in development mode
maturin develop

# Or build and install in release mode
maturin develop --release
```

For more information about Maturin, visit [Maturin's documentation](https://www.maturin.rs/).

## Testing

Run the test suite:
```bash
python tests/test.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


## Acknowledgments

- Inspired by Python's ThreadPoolExecutor
- Built with Rust for performance and safety 