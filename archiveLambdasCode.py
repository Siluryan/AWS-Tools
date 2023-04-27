import boto3
import requests
import logging
from botocore.exceptions import ClientError

region_name = 'us-east-1'
bucket_name = f'tecsinapse-lambda-code-archive-{region_name}'

logging.basicConfig(level=logging.INFO)

session = boto3.session.Session(region_name=region_name)

s3 = session.resource('s3')

try:
    s3.meta.client.head_bucket(Bucket=bucket_name)
    logging.info(f'O bucket {bucket_name} já existe.')
except ClientError:
    s3.create_bucket(Bucket=bucket_name)
    logging.info(f'O bucket {bucket_name} foi criado com sucesso.')

client = session.client('lambda')

response = client.list_functions()

for function in response['Functions']:
    code_response = client.get_function(FunctionName=function['FunctionName'])
    env_response = client.get_function_configuration(FunctionName=function['FunctionName'])
    env_variables = env_response.get('Environment', {}).get('Variables', {})
    layers = env_response.get('Layers', [])

    file_name = function['FunctionName'] + '.zip'

    r = requests.get(code_response['Code']['Location'])
    s3 = session.resource('s3')
    s3.Bucket(bucket_name).put_object(Key=file_name, Body=r.content)
    logging.info(f'O arquivo {file_name} foi salvo no bucket {bucket_name}.')