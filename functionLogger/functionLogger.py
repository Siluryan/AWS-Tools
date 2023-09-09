import functools
import logging
import io
import datetime
import atexit
import os
from createDictionary import create_dictionary

log_contents = dict()

def get_utc_minus_3():
    return datetime.datetime.utcnow() - datetime.timedelta(hours=3)

def function_logger():
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            logger.setLevel(logging.INFO)

            log_stream = io.StringIO()
            ch = logging.StreamHandler(log_stream)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            logger.addHandler(ch)

            result = func(*args, **kwargs)

            log_content = log_stream.getvalue()

            if func.__name__ in log_contents:
                log_contents[func.__name__] += log_content
            else:
                log_contents[func.__name__] = log_content

            logger.removeHandler(ch)

            return result
        
        return wrapper

    def store_aggregated_logs():
        current_time = get_utc_minus_3()

        aggregated_log_content = '\n'.join([f"=== {func_name} ===\n{log}" for func_name, log in log_contents.items()])
        
        year_folder = current_time.strftime("%Y")
        month_folder = current_time.strftime("%m")
        timestamp = current_time.strftime("%Y-%m-%d_%H-%M-%S")
        
        log_dir = os.path.join(os.getcwd(), "aggregated_logs", year_folder, month_folder)
        os.makedirs(log_dir, exist_ok=True)
        
        log_file_path = os.path.join(log_dir, f"logs_{timestamp}.log")
        
        with open(log_file_path, "w") as log_file:
            log_file.write(aggregated_log_content)

    atexit.register(store_aggregated_logs)

    return decorator

atexit.register(create_dictionary)