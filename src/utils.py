import time

def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        if isinstance(result, dict) and 'error' not in result:
            result['execution_time'] = execution_time
        return result, execution_time
    return wrapper