import threading
import time
import sys
import datetime
import os

# Define the Job structure
class Job:
    def __init__(self, name, exec_time, priority):
        self.name = name
        self.time = exec_time
        self.priority = priority
        self.arrival_time = time.time() # Used for exact sorting calculations
        self.arrival_time_str = datetime.datetime.now().strftime("%H:%M:%S") # Used for the list display
        self.status = "Wait"

# Global Queue and Synchronization Variables
job_queue = []
MAX_JOBS = 100
current_policy = "FCFS"
running_job = None
running_job_start_time = 0

# Global counters for job tracking
total_jobs_submitted = 0
total_jobs_processed = 0

# Threading locks for synchronization (US 5)
queue_lock = threading.Lock()
queue_cond = threading.Condition(queue_lock)

# Flag to signal threads to exit cleanly
keep_running = True

def print_help():
    print("run <job> <time> <pri>: submit a job")
    print("list: display the job status")
    print("fcfs: change policy to FCFS")
    print("sjf: change policy to SJF")
    print("priority: change policy to Priority")
    print("test <benchmark> ... : run automated benchmark")
    print("quit: exit CSUbatch")

def reorder_queue():
    """Sorts the job queue based on the current scheduling policy."""
    # The running_job is deliberately excluded from this list to enforce non-preemption.
    global job_queue, current_policy
    if current_policy == "FCFS":
        job_queue.sort(key=lambda j: j.arrival_time)
    elif current_policy == "SJF":
        job_queue.sort(key=lambda j: (j.time, j.arrival_time))
    elif current_policy == "PRIORITY":
        # Assumes lowest integer value = highest priority. Falls back to arrival time on tie.
        job_queue.sort(key=lambda j: (j.priority, j.arrival_time))

def scheduler_thread():
    """
    Acts as an asynchronous monitor. In this design, the main thread 
    handles active scheduling logic upon command input to ensure instant UI feedback.
    This thread can be expanded in Cycle 3 for automated benchmarking.
    """
    global keep_running
    while keep_running:
        time.sleep(1)

def dispatcher_thread():
    """Handles executing jobs and enforces non-preemption."""
    global keep_running, job_queue, running_job, running_job_start_time
    
    while keep_running:
        job_to_run = None
        
        with queue_cond:
            # Wait for jobs to be added to the queue
            while len(job_queue) == 0 and keep_running:
                queue_cond.wait(timeout=1.0) 
            
            if not keep_running:
                break
                
            if len(job_queue) > 0:
                # Retrieve from the head of the already-sorted queue
                job_to_run = job_queue.pop(0)
                running_job = job_to_run
                running_job.status = "Run"
                running_job_start_time = time.time()
                
        # Execute job OUTSIDE the lock so the scheduler/UI isn't blocked 
        if job_to_run:
            # --- Cycle 2 Feature: execv() placeholder ---
            # In a native C Linux environment, you would use fork() and execv().
            # Below is the Python equivalent structure, with a sleep simulation.
            
            """
            pid = os.fork()
            if pid == 0:
                # Child process
                os.execv("./batch_job", ["batch_job", str(job_to_run.time)])
            else:
                # Parent dispatcher waits for the job to complete
                os.waitpid(pid, 0)
            """
            
            # Simulated execution
            time.sleep(job_to_run.time)
            
            # Clean up the running job state after completion
            with queue_lock:
                running_job = None
                global total_jobs_processed
                total_jobs_processed += 1

def main():
    global current_policy, keep_running, job_queue, running_job, running_job_start_time
    
    # Initialize background threads for Cycle 1 infrastructure
    scheduler = threading.Thread(target=scheduler_thread)
    dispatcher = threading.Thread(target=dispatcher_thread)
    
    scheduler.start()
    dispatcher.start()

    print("Welcome to CSUbatch v1.0")
    print("Developer: Group 1")
    print("Type 'help' to find more about CSUbatch commands.")

    # Interactive Command Shell Loop (US 1)
    while True:
        try:
            # Print the prompt without adding a newline
            print("> ", end="", flush=True)
            input_line = sys.stdin.readline().strip()
        except KeyboardInterrupt:
            break

        if not input_line:
            continue

        parts = input_line.split()
        command = parts[0].lower()

        if command == "help":
            print_help()
        if command =="test":
            print("Running automated benchmark")
            
        elif command == "run":
            if len(parts) == 4:
                job_name = parts[1]
                try:
                    exec_time = int(parts[2])
                    priority = int(parts[3])
                    
                    # Lock mutex before modifying queue
                    with queue_cond:
                        if len(job_queue) < MAX_JOBS:
                            new_job = Job(job_name, exec_time, priority)
                            job_queue.append(new_job)
                            
                            # Increment total submitted counter
                            global total_jobs_submitted
                            total_jobs_submitted += 1
                            
                            # Enforce chosen policy immediately
                            reorder_queue()
                            
                            # Cycle 2 logic: Calculate expected waiting time
                            wait_time = sum(j.time for j in job_queue)
                            if running_job:
                                elapsed = time.time() - running_job_start_time
                                remaining_time = max(0, running_job.time - elapsed)
                                wait_time += remaining_time
                            
                            print(f"Job {job_name} was submitted.")
                            print(f"Total number of jobs in the queue: {len(job_queue) + (1 if running_job else 0)}")
                            print(f"Expected waiting time: {int(wait_time)} seconds")
                            print(f"Scheduling Policy: {current_policy}.")
                            
                            # Signal dispatcher that a new job is available
                            queue_cond.notify()
                        else:
                            print("Error: Job queue is full.")
                except ValueError:
                    print("Error: <time> and <priority> must be integers.")
            else:
                print("Usage: run <job> <time> <priority>")
                
        elif command == "list":
            with queue_lock:
                total_jobs = len(job_queue) + (1 if running_job else 0)
                print(f"Total number of jobs in the queue: {total_jobs}")
                print(f"Scheduling Policy: {current_policy}.")
                print(f"{'Name':<15}{'CPU_Time':<10}{'Pri':<5}{'Arrival_time':<15}{'Progress'}")
                
                # Print active job first
                if running_job:
                    print(f"{running_job.name:<15}{running_job.time:<10}{running_job.priority:<5}{running_job.arrival_time_str:<15}Run")
                
                # Print waiting jobs
                for job in job_queue:
                    print(f"{job.name:<15}{job.time:<10}{job.priority:<5}{job.arrival_time_str:<15}Wait")
                    
        elif command in ["fcfs", "sjf", "priority"]:
            with queue_lock:
                current_policy = command.upper()
                reorder_queue()
                print(f"Scheduling policy is switched to {current_policy}. All {len(job_queue)} waiting jobs have been rescheduled.")
                
        elif command == "quit":
            print(f"Total jobs submitted: {total_jobs_submitted}")
            print(f"Total jobs processed: {total_jobs_processed}")
            print("Exiting CSUbatch.")
            break
            
        else:
            print("Unknown command. Type 'help' for available commands.")

    # Cleanup threads gracefully
    keep_running = False
    with queue_cond:
        queue_cond.notify_all() # Wake up dispatcher if sleeping
        
    scheduler.join()
    dispatcher.join()

if __name__ == "__main__":
    main()