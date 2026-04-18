## CSUBatch Project
CPSC 6179 Software Project Planning and Management

Columbus State University

### Team Members
- Robert Daniel
- Victor Dudley
- Khushi Jani

# CSUbatch v3.0

## Overview
CSUbatch is a multi-threaded batch job scheduling system designed to manage and process tasks efficiently. The system follows a “Digital Traffic Controller” metaphor: it ensures jobs (tasks) are executed in a safe, orderly sequence on the computer’s processor.

This version (Cycle 3) finalizes the core infrastructure by introducing automated workload generation and detailed performance metric tracking to evaluate the efficiency of the dynamic scheduling policies.

## Features Implemented (Cycle 2)
- Interactive command-line interface with command parsing
- Job submission and queue display
- Fully implemented scheduling policies:
    - First-Come, First-Served (FCFS)
    - Shortest Job First (SJF)
    - Priority-based scheduling
- Dynamic queue reordering based on selected policy
- Non-preemptive dispatcher for sequential job execution
- Expected waiting time calculation for queued jobs
- Thread-safe job queue using Python threading (locks & condition variables)
- Global counters for tracking submitted and completed jobs
- Automated testing suite using pytest (unit + end-to-end tests)

## Features Implemented (Cycle 3)

- Automated performance benchmarking (test command) to generate randomized workloads based on user-defined parameters.
- Advanced performance metrics calculations tracking Turnaround time, Throughput, and Average Waiting Time.
- Independent background thread execution (benchmark_runner) to maintain a non-blocking interactive shell during automated tests.
- Scaled thread-safe synchronization verified for Linux environment compatibility to prevent race conditions during rapid job generation.



## Usage (Cycle 2)
```bash
# Start CSUbatch
python csusbatch.py

# At the prompt (>), use commands:
help        # display available commands
run <job> <time> <priority>  # submit a job
list        # display queued jobs
fcfs/sjf/priority  # switch scheduling policy (framework only)
quit        # exit CSUbatch
```

## Running Tests
```bash
# Run all tests using pytest
pytest
```

## Version: v3.0
- Description: Multi-threaded batch scheduler with dynamic scheduling policies and automated testing
- Key Features: Scheduling algorithms, dispatcher, wait time calculation, thread-safe queue, pytest test suite

## Known Issues / Limitations
- Scheduling is non-preemptive (running jobs are not interrupted)
- Multi-threaded execution is simulated and may not reflect real OS-level scheduling
- Performance benchmarking not yet implemented

## Usage ( Cycle 3 )
```bash
 Start CSUbatch
python CSUBatch.py

# At the prompt (>), use commands:
help        # display available commands
run <job> <time> <priority>  # submit a job
list        # display queued jobs
fcfs/sjf/priority  # switch scheduling policy
test <benchmark_name> <policy> <num_jobs> <arrival_rate> <max_cpu> <max_pri> # run automated benchmark workloads
quit        # exit CSUbatch
```