# CSUbatch v1.0

## Overview
CSUbatch is a multi-threaded batch job scheduling system designed to manage and process tasks efficiently. The system is inspired by the “Digital Traffic Controller” metaphor: it ensures jobs (tasks) are executed in a safe, orderly sequence on the computer’s processor.

This version (Cycle 1) focuses on core infrastructure, including:

- Interactive command-line interface
- Basic job submission
- Multi-threaded queue management (producer-consumer model)
- Framework for dynamic scheduling policies (FCFS, SJF, Priority)

## Features Implemented (Cycle 1)
- Command shell with prompt and help menu
- Job submission and queue display (FIFO)
- Thread-safe queue using Python’s `threading` library
- Basic framework for policy switching
- Unit, integration, and system tests for core components

## Features Planned for Future Cycles
- Full implementation of scheduling policies (FCFS, SJF, Priority)
- Dynamic queue reordering based on active policy
- Automated performance benchmarking
- Linux system call integration
- Advanced performance metrics (throughput, turnaround time, CPU utilization)

## Usage (Cycle 1)
```bash
# Start CSUbatch
python csusbatch.py

# At the prompt (>), use commands:
help        # display available commands
run <job> <time> <priority>  # submit a job
list        # display queued jobs
fcfs/sjf/priority  # switch scheduling policy (framework only)
quit        # exit CSUbatch