import functools
import logging
import boto3
import io
import subprocess
import datetime

## importe esse código e use o decorador @function_logger()
## na função que deseja capturar os logs e enviá-los
## para um bucket do s3, apenas se certifique de usar logger
## para capturar os logs ao invés de logging

def function_logger():
    branch_name = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip().decode('utf-8')
    bucket_name = f'logs-{branch_name}'  
    folder_name = 'logs'

    s3 = boto3.client('s3')
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

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
            s3_key = f'{folder_name}/{func.__name__}_{current_datetime}.log'
            s3.put_object(Body=log_content, Bucket=bucket_name, Key=s3_key)

            logger.removeHandler(ch)

            return result

        return wrapper

    return decorator