import threading
import time
import sys
import datetime
import os
import random  


# Define the Job structure
class Job:
    def __init__(self, name, exec_time, priority):
        self.name = name
        self.time = exec_time
        self.priority = priority
        self.arrival_time = time.time()  
        self.arrival_time_str = datetime.datetime.now().strftime("%H:%M:%S")  
        self.status = "Wait"

        # Fields for Metrics Tracking
        self.start_time = 0
        self.finish_time = 0


# Global Queue and Synchronization Variables
job_queue = []
completed_jobs = []  
MAX_JOBS = 100
current_policy = "FCFS"
running_job = None
running_job_start_time = 0

# Global counters for job tracking
total_jobs_submitted = 0
total_jobs_processed = 0

# Threading locks for synchronization 
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
    print("test <benchmark_name> <policy> <num_jobs> <arrival_rate> <max_cpu> <max_pri>: run automated benchmark")
    print("quit: exit CSUbatch")


def reorder_queue():
    """Sorts the job queue based on the current scheduling policy."""
    global job_queue, current_policy
    if current_policy == "FCFS":
        job_queue.sort(key=lambda j: j.arrival_time)
    elif current_policy == "SJF":
        job_queue.sort(key=lambda j: (j.time, j.arrival_time))
    elif current_policy == "PRIORITY":
        job_queue.sort(key=lambda j: (j.priority, j.arrival_time))


def scheduler_thread():
    """Acts as an asynchronous monitor."""
    global keep_running
    while keep_running:
        time.sleep(1)


def dispatcher_thread():
    """Handles executing jobs and enforces non-preemption using Linux System Calls."""
    global keep_running, job_queue, running_job, running_job_start_time, completed_jobs

    while keep_running:
        job_to_run = None

        with queue_cond:
            while len(job_queue) == 0 and keep_running:
                queue_cond.wait(timeout=1.0)

            if not keep_running:
                break

            if len(job_queue) > 0:
                job_to_run = job_queue.pop(0)
                running_job = job_to_run
                running_job.status = "Run"
                running_job_start_time = time.time()

                # Record actual start time
                job_to_run.start_time = time.time()

        # Execute job OUTSIDE the lock using os.fork() and os.execv()
        if job_to_run:
            try:
                pid = os.fork()
                
                if pid == 0:
                    # Child Process: Execute the workload
                    try:
                        # We use /bin/sleep as a native way to consume exact wall-clock time
                        os.execv('/bin/sleep', ['sleep', str(job_to_run.time)])
                    except OSError as e:
                        print(f"\n[Error] Failed to execute job {job_to_run.name}: {e}")
                        os._exit(1) # Critical: force child exit if execv fails to prevent fork bombs
                
                elif pid > 0:
                    # Parent Process (Dispatcher): Wait for the child process to finish
                    os.waitpid(pid, 0)
                    
            except AttributeError:
                # Fallback purely for local development if run on Windows
                time.sleep(job_to_run.time)
            except OSError as e:
                print(f"\n[Error] Fork failed: {e}")

            # Clean up the running job state and log for metrics
            job_to_run.finish_time = time.time()

            with queue_lock:
                running_job = None
                global total_jobs_processed
                total_jobs_processed += 1
                completed_jobs.append(job_to_run)  


def benchmark_runner(benchmark_name, policy, num_jobs, arrival_rate, max_cpu, max_pri):
    """Background thread to generate random workloads and calculate metrics"""
    global total_jobs_submitted, current_policy

    # Switch policy before starting
    with queue_lock:
        current_policy = policy
        reorder_queue()

    print(f"\n[Starting benchmark '{benchmark_name}'...] generating {num_jobs} jobs under {policy} policy.")

    test_start_time = time.time()

    # Generate randomized workloads
    for i in range(1, num_jobs + 1):
        time.sleep(arrival_rate)
        cpu_t = random.randint(1, max_cpu)
        pri = random.randint(1, max_pri)
        job_name = f"B_{benchmark_name}_{i}"

        with queue_cond:
            if len(job_queue) < MAX_JOBS:
                new_job = Job(job_name, cpu_t, pri)
                job_queue.append(new_job)
                total_jobs_submitted += 1
                reorder_queue()
                queue_cond.notify()

    print(f"\n[Benchmark '{benchmark_name}' submission phase complete. Waiting for dispatcher...]")

    # Wait for the queue to empty out
    while True:
        with queue_lock:
            if len(job_queue) == 0 and running_job is None:
                break
        time.sleep(0.5)

    test_end_time = time.time()

    # Calculate Metrics
    print(f"\n=== Benchmark '{benchmark_name}' Metrics ===")

    # Filter completed_jobs to only include this specific benchmark run
    bench_jobs = [j for j in completed_jobs if j.name.startswith(f"B_{benchmark_name}_")]

    if bench_jobs:
        avg_turnaround = sum((j.finish_time - j.arrival_time) for j in bench_jobs) / len(bench_jobs)
        avg_waiting = sum((j.start_time - j.arrival_time) for j in bench_jobs) / len(bench_jobs)
        throughput = len(bench_jobs) / (test_end_time - test_start_time)

        print(f"Total Jobs Completed:   {len(bench_jobs)}")
        print(f"Total Time Elapsed:     {test_end_time - test_start_time:.2f} seconds")
        print(f"System Throughput:      {throughput:.2f} jobs/sec")
        print(f"Average Turnaround:     {avg_turnaround:.2f} seconds")
        print(f"Average Waiting Time:   {avg_waiting:.2f} seconds")
    else:
        print("Error: No benchmark jobs completed.")
    print("=========================================\n> ", end="", flush=True)


def main():
    global current_policy, keep_running, job_queue, running_job, running_job_start_time

    scheduler = threading.Thread(target=scheduler_thread)
    dispatcher = threading.Thread(target=dispatcher_thread)

    scheduler.start()
    dispatcher.start()

    print("Welcome to CSUbatch v1.0")
    print("Developer: Group 1")
    print("Type 'help' to find more about CSUbatch commands.")

    while True:
        try:
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

        elif command == "test":
            if len(parts) >= 6:
                benchmark_name = parts[1]
                policy = parts[2].upper()
                if policy not in ["FCFS", "SJF", "PRIORITY"]:
                    print("Error: Policy must be FCFS, SJF, or PRIORITY.")
                    continue
                try:
                    num_jobs = int(parts[3])
                    arrival_rate = float(parts[4])
                    max_cpu = int(parts[5])
                    max_pri = int(parts[6]) if len(parts) == 7 else 10

                    threading.Thread(target=benchmark_runner,
                                     args=(benchmark_name, policy, num_jobs, arrival_rate, max_cpu, max_pri),
                                     daemon=True).start()

                except ValueError:
                    print("Error: num_jobs, max_cpu, max_priority must be integers; arrival_rate must be a float.")
            else:
                print("Usage: test <benchmark_name> <policy> <num_jobs> <arrival_rate> <max_cpu> <max_priority>")

        elif command == "run":
            if len(parts) == 4:
                job_name = parts[1]
                try:
                    exec_time = int(parts[2])
                    priority = int(parts[3])

                    with queue_cond:
                        if len(job_queue) < MAX_JOBS:
                            new_job = Job(job_name, exec_time, priority)
                            job_queue.append(new_job)

                            global total_jobs_submitted
                            total_jobs_submitted += 1

                            reorder_queue()

                            wait_time = sum(j.time for j in job_queue)
                            if running_job:
                                elapsed = time.time() - running_job_start_time
                                remaining_time = max(0, running_job.time - elapsed)
                                wait_time += remaining_time

                            print(f"Job {job_name} was submitted.")
                            print(f"Total number of jobs in the queue: {len(job_queue) + (1 if running_job else 0)}")
                            print(f"Expected waiting time: {int(wait_time)} seconds")
                            print(f"Scheduling Policy: {current_policy}.")

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

                if running_job:
                    print(
                        f"{running_job.name:<15}{running_job.time:<10}{running_job.priority:<5}{running_job.arrival_time_str:<15}Run")

                for job in job_queue:
                    print(f"{job.name:<15}{job.time:<10}{job.priority:<5}{job.arrival_time_str:<15}Wait")

        elif command in ["fcfs", "sjf", "priority"]:
            with queue_lock:
                current_policy = command.upper()
                reorder_queue()
                print(
                    f"Scheduling policy is switched to {current_policy}. All {len(job_queue)} waiting jobs have been rescheduled.")

        elif command == "quit":
            print(f"Total jobs submitted: {total_jobs_submitted}")
            print(f"Total jobs processed: {total_jobs_processed}")
            print("Exiting CSUbatch.")
            break

        else:
            print("Unknown command. Type 'help' for available commands.")

    keep_running = False
    with queue_cond:
        queue_cond.notify_all()

    scheduler.join()
    dispatcher.join()


if __name__ == "__main__":
    main()