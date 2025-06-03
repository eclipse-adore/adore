
import psutil


def kill_process_and_children(pid):
    """Ensure all child processes of a launch file are killed."""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)  # Get all child processes
        for child in children:
            child.terminate()
        gone, alive = psutil.wait_procs(children, timeout=5)
        for child in alive:
            child.kill()  # Force kill if still alive
        parent.terminate()
        parent.wait(5)
    except psutil.NoSuchProcess:
        pass