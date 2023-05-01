import boto3
import requests
import logging
import zipfile
import json
from io import BytesIO
from botocore.exceptions import ClientError

region_name = 'us-east-1'
bucket_name = f'tecsinapse-lambda-archive-prod-{region_name}'

logging.basicConfig(level=logging.INFO)

session = boto3.session.Session(region_name=region_name)

s3 = session.resource('s3')

try:
    s3.meta.client.head_bucket(Bucket=bucket_name)
    logging.info(f'The {bucket_name} bucket already exists.')
except ClientError:
    create_bucket_configuration = {}
    if region_name != 'us-east-1':
        create_bucket_configuration = {'CreateBucketConfiguration': {'LocationConstraint': region_name}}
    s3.create_bucket(Bucket=bucket_name, **create_bucket_configuration)
    logging.info(f'The {bucket_name} bucket was successfully created.')

client = session.client('lambda')

paginator = client.get_paginator('list_functions')
response_iterator = paginator.paginate()

for response in response_iterator:
    for function in response['Functions']:
        function_name = function['FunctionName']
        file_name = function_name + '.zip'

        code_response = client.get_function(FunctionName=function_name)
        code_zip_file = BytesIO(requests.get(code_response['Code']['Location']).content)

        env_response = client.get_function_configuration(FunctionName=function_name)
        env_variables = env_response.get('Environment', {}).get('Variables', {})
        layers = env_response.get('Layers', [])

        function_data = {
            'FunctionName': function_name,
            'Code': code_response['Code'],
            'Environment': env_response.get('Environment', {}),
            'Layers': layers
        }

        function_data['Configuration'] = env_response

        with BytesIO() as zip_file_buffer:
            with zipfile.ZipFile(zip_file_buffer, mode='w') as z:
                list_functions_json = json.dumps(function_data, indent=2).encode()
                z.writestr('list-functions.json', list_functions_json)

                z.writestr(function_name + '.zip', code_zip_file.read())

                for layer in layers:
                    layer_response = client.get_layer_version(
                        LayerName=layer['Arn'].split(':')[-2],
                        VersionNumber=int(layer['Arn'].split(':')[-1])
                    )
                    layer_zip_file = BytesIO(requests.get(layer_response['Content']['Location']).content)
                    z.writestr(layer['Arn'].split(':')[-1] + '.zip', layer_zip_file.read())

            zip_file_buffer.seek(0)
            s3.Bucket(bucket_name).put_object(Key=file_name, Body=zip_file_buffer.read())
            logging.info(f'The file {file_name} was saved to the {bucket_name} bucket.')