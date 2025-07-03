import threading
import time
from unittest.mock import Mock


class TestTimeoutScenarios:
    """Test cases that demonstrate different timeout scenarios for analysis."""

    def test_simple_sleep_timeout(self):
        """A test that times out due to simple sleep - easy to identify."""
        print("Starting simple sleep test...")
        time.sleep(10)  # nosec B311 - Intentional timeout test scenario
        print("This should never print")

    def test_infinite_loop_timeout(self):
        """A test that times out due to infinite loop - harder to identify."""
        print("Starting infinite loop test...")
        counter = 0
        while True:  # Infinite loop
            counter += 1
            if counter % 100000 == 0:
                print(f"Counter: {counter}")

    def test_blocking_io_timeout(self):
        """A test that times out due to blocking I/O operation."""
        import socket

        print("Starting blocking I/O test...")

        # Try to connect to a non-responsive endpoint
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(None)  # No timeout, will block
        try:
            # This will hang waiting for connection
            sock.connect(("10.255.255.1", 80))  # Non-routable IP
        except Exception as e:
            print(f"Exception: {e}")
        finally:
            sock.close()

    def test_thread_deadlock_timeout(self):
        """A test that times out due to thread deadlock."""
        print("Starting thread deadlock test...")

        lock1 = threading.Lock()
        lock2 = threading.Lock()

        def thread1_func():
            with lock1:
                print("Thread 1 acquired lock1")
                time.sleep(0.1)  # nosec B311 - Intentional deadlock test timing
                print("Thread 1 trying to acquire lock2")
                with lock2:
                    print("Thread 1 acquired lock2")

        def thread2_func():
            with lock2:
                print("Thread 2 acquired lock2")
                time.sleep(0.1)  # nosec B311 - Intentional deadlock test timing
                print("Thread 2 trying to acquire lock1")
                with lock1:
                    print("Thread 2 acquired lock1")

        thread1 = threading.Thread(target=thread1_func)
        thread2 = threading.Thread(target=thread2_func)

        thread1.start()
        thread2.start()

        # Wait for threads to complete (they won't due to deadlock)
        thread1.join()
        thread2.join()

    def test_mock_hanging_operation(self):
        """A test that simulates a hanging external service call."""
        print("Starting mock hanging operation test...")

        # Simulate a service that hangs
        mock_service = Mock()

        def hanging_call(*args, **kwargs):
            print("Service call started...")
            time.sleep(20)  # nosec B311 - Intentional timeout test simulation
            return "success"

        mock_service.make_request = hanging_call

        # This will timeout waiting for the service
        result = mock_service.make_request("some_data")
        assert result == "success"
