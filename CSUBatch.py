import threading
import time
import sys

# Define the Job structure
class Job:
    def __init__(self, name, exec_time, priority):
        self.name = name
        self.time = exec_time
        self.priority = priority

# Global Queue and Synchronization Variables
job_queue = []
MAX_JOBS = 100
current_policy = "FCFS"

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

def scheduler_thread():
    """Handles policy reordering (To be implemented in a future Sprint)"""
    global keep_running
    while keep_running:
        time.sleep(1)

def dispatcher_thread():
    """Handles executing jobs (To be implemented in a future Sprint)"""
    global keep_running, job_queue
    while keep_running:
        with queue_cond:
            # Wait for jobs to be added to the queue
            while len(job_queue) == 0 and keep_running:
                queue_cond.wait(timeout=1.0) 
            pass

def main():
    global current_policy, keep_running
    
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
                            
                            total_time = sum(job.time for job in job_queue)
                            
                            print(f"Job {job_name} was submitted.")
                            print(f"Total number of jobs in the queue: {len(job_queue)}")
                            print(f"Expected waiting time: {total_time} seconds")
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
                print(f"Total jobs in queue: {len(job_queue)}")
                for job in job_queue:
                    print(f"{job.name}\t{job.time}\t{job.priority}")
                    
        elif command in ["fcfs", "sjf", "priority"]:
            with queue_lock:
                current_policy = command.upper()
                print(f"Scheduling policy switched to {current_policy}. All jobs re-evaluated.")
                
        elif command == "quit":
            with queue_lock:
                print(f"Total jobs submitted: {len(job_queue)}")
            print("Exiting CSUbatch.")
            break
            
        else:
            print("Unknown command. Type 'help' for available commands.")

    # Cleanup threads gracefully
    keep_running = False
    scheduler.join()
    dispatcher.join()

if __name__ == "__main__":
    main()