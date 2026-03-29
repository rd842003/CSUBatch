import pytest
import time
from io import StringIO
from unittest.mock import patch
import CSUBatch

@pytest.fixture(autouse=True)
def reset_csubatch_state():
    """Fixture to reset the global state of the application before each test."""
    CSUBatch.job_queue.clear()
    CSUBatch.current_policy = "FCFS"
    CSUBatch.running_job = None
    CSUBatch.running_job_start_time = 0
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

@patch("threading.Thread.join")  # Added mock for join
@patch("threading.Thread.start") # Mock threads so dispatcher doesn't consume jobs during test
@patch("sys.stdout", new_callable=StringIO)
def test_cli_job_submission_and_list(mock_stdout, mock_thread_start, mock_thread_join):
    """E2E Test: Submit jobs, list them, and verify the CLI output format."""
    
    # Sequence of commands to pipe into the command shell
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
    assert "Expected waiting time: 10 seconds" in output # When job2 is submitted, job1 (10s) is waiting
    
    # Verify List Outputs
    assert "Total number of jobs in the queue: 2" in output
    assert "job1" in output
    assert "job2" in output

@patch("threading.Thread.join")  # Added mock for join
@patch("threading.Thread.start")
@patch("sys.stdout", new_callable=StringIO)
def test_cli_dynamic_policy_switch(mock_stdout, mock_thread_start, mock_thread_join):
    """E2E Test: Verify the policy switch commands correctly reorder the queue."""
    
    inputs = [
        "run long_job 20 2",
        "run short_job 5 1",
        "sjf", # Switch to SJF
        "list",
        "quit"
    ]
    
    with patch("sys.stdin.readline", side_effect=[i + "\n" for i in inputs]):
        CSUBatch.main()
        
    output = mock_stdout.getvalue()
    
    assert "Scheduling policy is switched to SJF" in output
    
    # In SJF, short_job (5s) should appear in the list BEFORE long_job (20s).
    # We can check the string index in the standard output block.
    short_job_idx = output.find("short_job")
    long_job_idx = output.find("long_job", short_job_idx) # Search for long_job AFTER short_job
    
    assert short_job_idx != -1
    assert long_job_idx != -1
    assert short_job_idx < long_job_idx, "short_job was not reordered ahead of long_job by SJF"