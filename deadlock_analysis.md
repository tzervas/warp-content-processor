
# Timeout Analysis Report for test_timeout_demo.py::TestTimeoutScenarios::test_thread_deadlock_timeout

## Summary
- **Timeout Type**: deadlock
- **Threads Involved**: 3

## Stack Trace Analysis

### Thread 1: Thread-3 (thread2_func) (ID: 136343220987584)

**Stack Frames:**

- `/home/vector_weight/.local/share/uv/python/cpython-3.13.5-linux-x86_64-gnu/lib/python3.13/threading.py:1014` in `_bootstrap()`
  ```python
  self._bootstrap_inner()
  ```

- `/home/vector_weight/.local/share/uv/python/cpython-3.13.5-linux-x86_64-gnu/lib/python3.13/threading.py:1043` in `_bootstrap_inner()`
  ```python
  self.run()
  ```

- `/home/vector_weight/.local/share/uv/python/cpython-3.13.5-linux-x86_64-gnu/lib/python3.13/threading.py:994` in `run()`
  ```python
  self._target(*self._args, **self._kwargs)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/test_timeout_demo.py:61` in `thread2_func()`
  ```python
  with lock1:
  ```

### Thread 2: Thread-2 (thread1_func) (ID: 136343229380288)

**Stack Frames:**

- `/home/vector_weight/.local/share/uv/python/cpython-3.13.5-linux-x86_64-gnu/lib/python3.13/threading.py:1014` in `_bootstrap()`
  ```python
  self._bootstrap_inner()
  ```

- `/home/vector_weight/.local/share/uv/python/cpython-3.13.5-linux-x86_64-gnu/lib/python3.13/threading.py:1043` in `_bootstrap_inner()`
  ```python
  self.run()
  ```

- `/home/vector_weight/.local/share/uv/python/cpython-3.13.5-linux-x86_64-gnu/lib/python3.13/threading.py:994` in `run()`
  ```python
  self._target(*self._args, **self._kwargs)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/test_timeout_demo.py:53` in `thread1_func()`
  ```python
  with lock2:
  ```

### Thread 3: MainThread (ID: 136343266940800)

**Stack Frames:**

- `<frozen runpy>:198` in `_run_module_as_main()`
  ```python
  File "<frozen runpy>", line 88, in _run_code
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/_pytest/config/__init__.py:201` in `console_main()`
  ```python
  code = main()
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/_pytest/config/__init__.py:175` in `main()`
  ```python
  ret: ExitCode | int = config.hook.pytest_cmdline_main(config=config)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/pluggy/_hooks.py:512` in `__call__()`
  ```python
  return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/pluggy/_manager.py:120` in `_hookexec()`
  ```python
  return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/pluggy/_callers.py:121` in `_multicall()`
  ```python
  res = hook_impl.function(*args)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/_pytest/main.py:336` in `pytest_cmdline_main()`
  ```python
  return wrap_session(config, _main)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/_pytest/main.py:289` in `wrap_session()`
  ```python
  session.exitstatus = doit(config, session) or 0
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/_pytest/main.py:343` in `_main()`
  ```python
  config.hook.pytest_runtestloop(session=session)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/pluggy/_hooks.py:512` in `__call__()`
  ```python
  return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/pluggy/_manager.py:120` in `_hookexec()`
  ```python
  return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/pluggy/_callers.py:121` in `_multicall()`
  ```python
  res = hook_impl.function(*args)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/_pytest/main.py:367` in `pytest_runtestloop()`
  ```python
  item.config.hook.pytest_runtest_protocol(item=item, nextitem=nextitem)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/pluggy/_hooks.py:512` in `__call__()`
  ```python
  return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/pluggy/_manager.py:120` in `_hookexec()`
  ```python
  return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/pluggy/_callers.py:121` in `_multicall()`
  ```python
  res = hook_impl.function(*args)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/_pytest/runner.py:117` in `pytest_runtest_protocol()`
  ```python
  runtestprotocol(item, nextitem=nextitem)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/_pytest/runner.py:136` in `runtestprotocol()`
  ```python
  reports.append(call_and_report(item, "call", log))
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/_pytest/runner.py:245` in `call_and_report()`
  ```python
  call = CallInfo.from_call(
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/_pytest/runner.py:344` in `from_call()`
  ```python
  result: TResult | None = func()
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/pluggy/_hooks.py:512` in `__call__()`
  ```python
  return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/pluggy/_manager.py:120` in `_hookexec()`
  ```python
  return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/pluggy/_callers.py:121` in `_multicall()`
  ```python
  res = hook_impl.function(*args)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/_pytest/runner.py:178` in `pytest_runtest_call()`
  ```python
  item.runtest()
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/_pytest/python.py:1671` in `runtest()`
  ```python
  self.ihook.pytest_pyfunc_call(pyfuncitem=self)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/pluggy/_hooks.py:512` in `__call__()`
  ```python
  return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/pluggy/_manager.py:120` in `_hookexec()`
  ```python
  return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/pluggy/_callers.py:121` in `_multicall()`
  ```python
  res = hook_impl.function(*args)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/.venv/lib/python3.13/site-packages/_pytest/python.py:157` in `pytest_pyfunc_call()`
  ```python
  result = testfunction(**testargs)
  ```

- `/home/vector_weight/Downloads/warp-content-processor/test_timeout_demo.py:71` in `test_thread_deadlock_timeout()`
  ```python
  thread1.join()
  ```

- `/home/vector_weight/.local/share/uv/python/cpython-3.13.5-linux-x86_64-gnu/lib/python3.13/threading.py:1094` in `join()`
  ```python
  self._handle.join(timeout)
  ```

## Likely Cause

- **Thread**: Thread-3 (thread2_func)
- **Location**: /home/vector_weight/Downloads/warp-content-processor/test_timeout_demo.py:61
- **Code**: `with lock1:`

- **Thread**: Thread-2 (thread1_func)
- **Location**: /home/vector_weight/Downloads/warp-content-processor/test_timeout_demo.py:53
- **Code**: `with lock2:`

## Recommendations
- Check for deadlock patterns
- Use lock ordering
- Add timeout to join() calls
