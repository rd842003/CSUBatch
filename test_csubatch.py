import pytest
import time
import os
from io import StringIO
from unittest.mock import patch
import CSUBatch

@pytest.fixture(autouse=True)
def reset_csubatch_state():
    """Fixture to reset the global state of the application before each test."""
    CSUBatch.job_queue.clear()
    CSUBatch.completed_jobs.clear()  # Added for Cycle 3
    CSUBatch.current_policy = "FCFS"
    CSUBatch.running_job = None
    CSUBatch.running_job_start_time = 0
    CSUBatch.total_jobs_submitted = 0
    CSUBatch.total_jobs_processed = 0
    CSUBatch.keep_running = True
    yield
    # Cleanup after test finishes
    CSUBatch.keep_running = False

def test_fcfs_reordering():
    """Test First-Come, First-Served ordering logic."""
    CSUBatch.current_policy = "FCFS"
    
    j1 = CSUBatch.Job("j1", 10, 2)
    j2 = CSUBatch.Job("j2", 5, 1)
    j3 = CSUBatch.Job("j3", 8, 3)
    
    # Manually space out arrival times to simulate sequential submission
    j1.arrival_time = 1
    j2.arrival_time = 3
    j3.arrival_time = 2
    
    CSUBatch.job_queue.extend([j1, j2, j3])
    CSUBatch.reorder_queue()
    
    # Expected order: j1 (arr 1) -> j3 (arr 2) -> j2 (arr 3)
    assert [j.name for j in CSUBatch.job_queue] == ["j1", "j3", "j2"]

def test_sjf_reordering():
    """Test Shortest Job First ordering logic."""
    CSUBatch.current_policy = "SJF"
    
    j1 = CSUBatch.Job("j1", 10, 2)
    j2 = CSUBatch.Job("j2", 2, 1)
    j3 = CSUBatch.Job("j3", 5, 3)
    
    CSUBatch.job_queue.extend([j1, j2, j3])
    CSUBatch.reorder_queue()
    
    # Expected order by CPU time: j2 (2s) -> j3 (5s) -> j1 (10s)
    assert [j.name for j in CSUBatch.job_queue] == ["j2", "j3", "j1"]

def test_priority_reordering():
    """Test Priority (lowest integer = highest priority) ordering logic."""
    CSUBatch.current_policy = "PRIORITY"
    
    j1 = CSUBatch.Job("j1", 10, 3) # Lowest priority
    j2 = CSUBatch.Job("j2", 5, 1)  # Highest priority
    j3 = CSUBatch.Job("j3", 8, 2)  # Medium priority
    
    CSUBatch.job_queue.extend([j1, j2, j3])
    CSUBatch.reorder_queue()
    
    # Expected order by priority level: j2 (1) -> j3 (2) -> j1 (3)
    assert [j.name for j in CSUBatch.job_queue] == ["j2", "j3", "j1"]

@patch("threading.Thread.join")  
@patch("threading.Thread.start") 
@patch("sys.stdout", new_callable=StringIO)
def test_cli_job_submission_and_list(mock_stdout, mock_thread_start, mock_thread_join):
    """E2E Test: Submit jobs, list them, and verify the CLI output format."""
    
    inputs = [
        "run job1 10 2",
        "run job2 5 1",
        "list",
        "quit"
    ]
    
    with patch("sys.stdin.readline", side_effect=[i + "\n" for i in inputs]):
        CSUBatch.main()
        
    output = mock_stdout.getvalue()
    
    # Verify Submission Outputs
    assert "Job job1 was submitted." in output
    assert "Job job2 was submitted." in output
    assert "Expected waiting time: 10 seconds" in output 
    
    # Verify List Outputs
    assert "Total number of jobs in the queue: 2" in output
    assert "job1" in output
    assert "job2" in output

@patch("threading.Thread.join")  
@patch("threading.Thread.start")
@patch("sys.stdout", new_callable=StringIO)
def test_cli_dynamic_policy_switch(mock_stdout, mock_thread_start, mock_thread_join):
    """E2E Test: Verify the policy switch commands correctly reorder the queue."""
    
    inputs = [
        "run long_job 20 2",
        "run short_job 5 1",
        "sjf", 
        "list",
        "quit"
    ]
    
    with patch("sys.stdin.readline", side_effect=[i + "\n" for i in inputs]):
        CSUBatch.main()
        
    output = mock_stdout.getvalue()
    
    assert "Scheduling policy is switched to SJF" in output
    
    short_job_idx = output.find("short_job")
    long_job_idx = output.find("long_job", short_job_idx) 
    
    assert short_job_idx != -1
    assert long_job_idx != -1
    assert short_job_idx < long_job_idx, "short_job was not reordered ahead of long_job by SJF"

@patch("threading.Thread.join")
@patch("threading.Thread.start")
@patch("sys.stdout", new_callable=StringIO)
def test_expected_wait_time_includes_running_job(mock_stdout, mock_thread_start, mock_thread_join):
    """E2E Test: expected waiting time includes queued jobs and running job remaining time."""

    running = CSUBatch.Job("running_job", 20, 1)
    running.arrival_time = 0 
    running.status = "Run"
    CSUBatch.running_job = running
    CSUBatch.running_job_start_time = 990 

    CSUBatch.job_queue.extend([
        CSUBatch.Job("wait1", 3, 2),
        CSUBatch.Job("wait2", 4, 3)
    ])

    inputs = ["run job_new 10 2", "quit"]

    with patch("CSUBatch.time.time", side_effect=[1000.0, 1000.0, 1000.0, 1000.0]):
        with patch("sys.stdin.readline", side_effect=[i + "\n" for i in inputs]):
            CSUBatch.main()

    output = mock_stdout.getvalue()

    assert "Expected waiting time: 27 seconds" in output
    assert "Total number of jobs in the queue: 4" in output

def test_single_running_job():
    """Test that list shows running job as 'Run' and queued jobs as 'Wait'."""
    
    CSUBatch.running_job = CSUBatch.Job("running_job", 20, 1)
    CSUBatch.running_job.status = "Run"
    CSUBatch.job_queue = [
        CSUBatch.Job("wait1", 10, 2),
        CSUBatch.Job("wait2", 5, 1)
    ]
    CSUBatch.current_policy = "FCFS"
    
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        with CSUBatch.queue_lock:
            total_jobs = len(CSUBatch.job_queue) + (1 if CSUBatch.running_job else 0)
            print(f"Total number of jobs in the queue: {total_jobs}")
            print(f"Scheduling Policy: {CSUBatch.current_policy}.")
            print(f"{'Name':<15}{'CPU_Time':<10}{'Pri':<5}{'Arrival_time':<15}{'Progress'}")
            
            if CSUBatch.running_job:
                print(f"{CSUBatch.running_job.name:<15}{CSUBatch.running_job.time:<10}{CSUBatch.running_job.priority:<5}{CSUBatch.running_job.arrival_time_str:<15}Run")
            
            for job in CSUBatch.job_queue:
                print(f"{job.name:<15}{job.time:<10}{job.priority:<5}{job.arrival_time_str:<15}Wait")
    
    output = mock_stdout.getvalue()
    
    assert "Total number of jobs in the queue: 3" in output
    assert "running_job" in output and "Run" in output
    assert "wait1" in output and "Wait" in output
    assert "wait2" in output and "Wait" in output
    
    run_idx = output.find("running_job")
    wait1_idx = output.find("wait1")
    wait2_idx = output.find("wait2")
    assert run_idx < wait1_idx < wait2_idx

def test_dispatcher_non_preemptive_behavior():
    """Test that dispatcher pops only one job at a time, setting it as running while others wait."""
    
    CSUBatch.job_queue = [
        CSUBatch.Job("job1", 10, 2),
        CSUBatch.Job("job2", 5, 1),
        CSUBatch.Job("job3", 8, 3)
    ]
    
    job_to_run = CSUBatch.job_queue.pop(0)
    CSUBatch.running_job = job_to_run
    CSUBatch.running_job.status = "Run"
    
    assert CSUBatch.running_job.name == "job1"
    assert CSUBatch.running_job.status == "Run"
    
    assert len(CSUBatch.job_queue) == 2
    assert CSUBatch.job_queue[0].name == "job2"
    assert CSUBatch.job_queue[0].status == "Wait"
    assert CSUBatch.job_queue[1].name == "job3"
    assert CSUBatch.job_queue[1].status == "Wait"

@patch("threading.Thread.join")
@patch("threading.Thread.start")
@patch("sys.stdout", new_callable=StringIO)
def test_job_counters_tracking(mock_stdout, mock_thread_start, mock_thread_join):
    """Test that total_jobs_submitted and total_jobs_processed are tracked correctly."""
    
    inputs = [
        "run job1 10 2",
        "run job2 5 1",
        "run job3 8 3",
        "quit"
    ]
    
    with patch("sys.stdin.readline", side_effect=[i + "\n" for i in inputs]):
        CSUBatch.main()
    
    output = mock_stdout.getvalue()
    
    assert "Total jobs submitted: 3" in output
    assert "Total jobs processed: 0" in output

def test_job_processed_counter_increment():
    """Test that total_jobs_processed increments when a job finishes."""
    
    assert CSUBatch.total_jobs_processed == 0
    
    with CSUBatch.queue_lock:
        CSUBatch.running_job = None
        CSUBatch.total_jobs_processed += 1
    
    assert CSUBatch.total_jobs_processed == 1


# ==========================================
# CYCLE 3 NEW TESTS
# ==========================================

@patch("os.waitpid", create=True)
@patch("os.execv", create=True)
@patch("os.fork", create=True)
def test_dispatcher_uses_linux_system_calls(mock_fork, mock_execv, mock_waitpid):
    """Test that the dispatcher correctly forks and executes a child process."""
    
    dummy_job = CSUBatch.Job("test_sys_job", 5, 1)
    CSUBatch.job_queue = [dummy_job]
    
    # Configure the mock to simulate being the parent process (returns a PID > 0)
    mock_fork.return_value = 1234  

    # Temporarily override keep_running so the thread runs exactly one loop
    def stop_running_after_one_loop():
        yield True
        yield False
    
    loop_controller = stop_running_after_one_loop()
    
    with patch("CSUBatch.keep_running", new_callable=lambda: next(loop_controller)):
        try:
            CSUBatch.dispatcher_thread()
        except StopIteration:
            pass 
            
    # Verify the native Linux calls were made
    mock_fork.assert_called_once()
    mock_waitpid.assert_called_once_with(1234, 0)
    
    # Verify the job was moved to completed_jobs
    assert len(CSUBatch.completed_jobs) == 1
    assert CSUBatch.completed_jobs[0].name == "test_sys_job"

@patch("threading.Thread.start")
@patch("sys.stdout", new_callable=StringIO)
def test_cli_benchmark_command(mock_stdout, mock_thread_start):
    """E2E Test: Verify the 'test' command parses arguments and starts the benchmark thread."""
    
    inputs = [
        "test load_test SJF 5 0.5 10 3",
        "quit"
    ]
    
    with patch("sys.stdin.readline", side_effect=[i + "\n" for i in inputs]):
        CSUBatch.main()
        
    output = mock_stdout.getvalue()
    
    # Ensure the command was accepted without throwing a Usage/Error message
    assert "Usage: test" not in output
    assert "Error:" not in output

@patch("sys.stdout", new_callable=StringIO)
def test_performance_metrics_calculations(mock_stdout):
    """Unit Test: Verify the math for Turnaround, Waiting Time, and Throughput."""
    
    # Setup dummy completed jobs specifically named for a benchmark test
    j1 = CSUBatch.Job("B_metricstest_1", 5, 1)
    j1.arrival_time = 0
    j1.start_time = 2
    j1.finish_time = 7
    # Turnaround: 7 - 0 = 7. Waiting: 2 - 0 = 2
    
    j2 = CSUBatch.Job("B_metricstest_2", 10, 1)
    j2.arrival_time = 0
    j2.start_time = 7
    j2.finish_time = 17
    # Turnaround: 17 - 0 = 17. Waiting: 7 - 0 = 7
    
    CSUBatch.completed_jobs.extend([j1, j2])
    
    # By passing 0 to num_jobs, we bypass the generation loop and jump straight to metrics.
    # We mock time.time to control the test_start_time and test_end_time for Throughput math.
    with patch("CSUBatch.time.time", side_effect=[100.0, 120.0]): 
        # Elapsed time = 120.0 - 100.0 = 20 seconds. 
        # Throughput = 2 jobs / 20 seconds = 0.10 jobs/sec
        CSUBatch.benchmark_runner("metricstest", "FCFS", 0, 0, 1, 1)
    
    output = mock_stdout.getvalue()
    
    # Expected Averages: Turnaround = (7 + 17) / 2 = 12.00
    # Expected Waiting = (2 + 7) / 2 = 4.50
    assert "Average Turnaround:     12.00 seconds" in output
    assert "Average Waiting Time:   4.50 seconds" in output
    assert "System Throughput:      0.10 jobs/sec" in output