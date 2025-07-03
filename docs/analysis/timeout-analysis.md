# Pytest Timeout Analysis Guide

## Understanding Timeout Stack Traces

When pytest-timeout aborts a hanging test, it provides detailed stack traces that help identify the root cause. Here's how to analyze them:

### 1. Stack Trace Components

The timeout output includes:

- **Timeout marker**: `++++++++++++++++++ Timeout ++++++++++++++++++`
- **Thread information**: Shows all active threads and their current state
- **Stack traces**: Complete call stack for each thread at timeout moment
- **Thread names/IDs**: Helps identify which threads are involved

### 2. Types of Timeout Scenarios and Analysis

#### Simple Sleep/Time-based Timeouts

**Stack trace characteristics:**

- Single thread (MainThread)
- Last frame shows `time.sleep()` call
- Clear line number pointing to sleep statement

**Example from our demo:**

```
File "/path/to/test_timeout_demo.py", line 13, in test_simple_sleep_timeout
  time.sleep(10)  # This will timeout before completing
```

**Analysis:** Easy to identify - the test is explicitly sleeping longer than the timeout.

#### Infinite Loop Timeouts

**Stack trace characteristics:**

- Shows the last executed line in the loop
- Usually points to a line within a `while` or `for` loop
- May show counter or processing statements

**Example from our demo:**

```
File "/path/to/test_timeout_demo.py", line 23, in test_infinite_loop_timeout
  print(f"Counter: {counter}")
```

**Analysis:** Look for loops without proper exit conditions. The line number indicates where the loop was when timeout occurred.

#### Thread Deadlock Timeouts

**Stack trace characteristics:**

- Multiple thread stacks shown
- Threads waiting on locks (`with lock:` statements)
- Main thread often waiting on `thread.join()`

**Example from our demo:**

```
Stack of Thread-3 (thread2_func):
  File "test_timeout_demo.py", line 61, in thread2_func
    with lock1:

Stack of Thread-2 (thread1_func):
  File "test_timeout_demo.py", line 53, in thread1_func
    with lock2:

Stack of MainThread:
  File "test_timeout_demo.py", line 71, in test_thread_deadlock_timeout
    thread1.join()
```

**Analysis:** Classic deadlock pattern - Thread-2 holds lock1 and wants lock2, Thread-3 holds lock2 and wants lock1.

#### Blocking I/O Timeouts

**Stack trace characteristics:**

- Network or file operations in the stack
- Socket operations (`connect`, `recv`, `send`)
- Database connections
- External service calls

**Common indicators:**

- `socket.connect()`
- `requests.get()` without timeout
- Database query execution
- File operations on network shares

### 3. Using Log Files for Deeper Analysis

#### Command to capture logs:

```bash
pytest --timeout=30 --log-file=debug.log --log-level=DEBUG test_file.py
```

#### What to look for in logs:

1. **Last log entries before timeout**: Shows what the test was doing
2. **Database queries**: Long-running or hanging queries
3. **Network requests**: Calls that might be hanging
4. **Resource acquisition**: File locks, database connections
5. **Error patterns**: Repeated failed attempts

### 4. Analysis Workflow

1. **Identify timeout type** from stack trace pattern
2. **Locate hanging operation** using line numbers
3. **Check logs** for context leading to hang
4. **Examine code** around identified lines
5. **Look for missing timeouts** in network/IO operations
6. **Check resource cleanup** (connections, files, locks)

### 5. Common Fixes

#### For Infinite Loops:

- Add proper exit conditions
- Add maximum iteration limits
- Use `itertools.count()` with safeguards

#### For Deadlocks:

- Establish lock ordering
- Use context managers consistently
- Consider using `threading.Lock()` with timeouts

#### For I/O Operations:

- Add explicit timeouts to all network calls
- Use connection pooling with limits
- Implement circuit breakers for external services

#### For Resource Issues:

- Ensure proper cleanup in `finally` blocks
- Use context managers (`with` statements)
- Set reasonable connection/transaction timeouts

### 6. Prevention Strategies

1. **Always set timeouts** on external calls
2. **Use connection limits** and pools
3. **Implement health checks** for external dependencies
4. **Add circuit breakers** for unreliable services
5. **Use async/await** for concurrent operations
6. **Monitor resource usage** in tests
