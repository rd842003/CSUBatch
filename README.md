# CSUbatch

## Description

CSUbatch is a multi-threaded batch job scheduling system designed to manage and process tasks efficiently. The system follows a “Digital Traffic Controller” metaphor: it ensures jobs (tasks) are executed in a safe, orderly sequence on the computer’s processor. 

This version (Cycle 3) finalizes the core infrastructure by introducing automated workload generation, native process execution, and detailed performance metric tracking to evaluate the efficiency of our dynamic scheduling policies (FCFS, SJF, and Priority).

## Getting Started

### Dependencies

* Python 3.x
* **Linux Environment:** Required for native process execution. The `dispatcher_thread` utilizes native Linux system calls (`os.fork()` and `os.execv()`).
* `pytest`: Required for running the automated testing suite.

### Installing

* Download or clone the repository to your local machine.
* Ensure both `CSUBatch.py` and `test_csubatch.py` are located in the same directory.

### Executing program

* To start the scheduling system, open your terminal and run:
```bash
python CSUBatch.py
```
* At the prompt (`>`), you can use the following commands to interact with the batch scheduler:
```bash
help        # display available commands
run <job> <time> <priority>  # submit a manual job
list        # display queued jobs and progress
fcfs        # switch scheduling policy to First-Come, First-Served
sjf         # switch scheduling policy to Shortest Job First
priority    # switch scheduling policy to Priority-based
test <benchmark_name> <policy> <num_jobs> <arrival_rate> <max_cpu> <max_pri> # run automated benchmark workloads
quit        # exit CSUbatch
```
* To run the automated test suite, open a new terminal in the directory and run:
```bash
pytest
```

## Help

**Windows Execution Warning:** Native process execution requires a Unix/Linux environment. If executed on Windows, the application will throw an `AttributeError` for `os.fork()`. The application gracefully catches this error and falls back to a simulated `time.sleep()` execution to prevent crashing during local development. For full benchmarking and system call functionality, utilize a Linux environment or WSL.

## Authors

* Robert Daniel 
* Victor Dudley
* Khushi Jani

## Version History

* 3.0 (Cycle 3)
    * Added native process execution using `/bin/sleep` via `os.fork()` and `os.execv()`.
    * Added automated benchmarking (`test` command) to generate randomized, high-volume workloads.
    * Added advanced performance analytics tracking Turnaround Time, System Throughput, and Average Waiting Time.
* 2.0 (Cycle 2)
    * Implemented dynamic queue reordering based on FCFS, SJF, and Priority algorithms.
    * Added thread-safe job queue using Python condition variables and locks.
    * Integrated interactive command-line interface and job progress tracking.
* 1.0 (Cycle 1)
    * Initial Release Framework and architecture planning.

## Acknowledgments

* CPSC 6179 Software Project Planning and Management
* Columbus State University