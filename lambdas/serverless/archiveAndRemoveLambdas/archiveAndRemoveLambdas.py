import json
import boto3
import logging
import zipfile
from io import BytesIO
from botocore.exceptions import ClientError
import datetime
import urllib.request

def create_archive_folder(bucket, archive_folder):
    archive_folder_exists = any(obj.key == f'{archive_folder}/' for obj in bucket.objects.filter(Prefix=f'{archive_folder}/'))
    if not archive_folder_exists:
        bucket.put_object(Key=f'{archive_folder}/')
        logging.info(f'{archive_folder} folder created in {bucket.name} bucket.')

def should_archive_function(client, function, current_date):
    response = client.list_tags(Resource=function['FunctionArn'])
    tags = response.get('Tags', {})
    return tags.get('Quarantine') == 'true' and tags.get('dateToArchive') == current_date

def archive_function(client, s3, bucket_name, archive_folder, region_name, function):
    function_name = function['FunctionName']
    
    try:
        code_response = client.get_function(FunctionName=function_name)
        code_zip_file = BytesIO(urllib.request.urlopen(code_response['Code']['Location']).read())

        env_response = client.get_function_configuration(FunctionName=function_name)
        env_variables = env_response.get('Environment', {}).get('Variables', {})
        layers = env_response.get('Layers', [])

        function_data = {
            'FunctionName': function_name,
            'Code': code_response['Code'],
            'Environment': {'Variables': env_variables},
            'Layers': layers,
            'Role': env_response.get('Role', ''),
            'Timeout': env_response.get('Timeout', 0),
            'MemorySize': env_response.get('MemorySize', 0)
        }

        with BytesIO() as zip_file_buffer:
            with zipfile.ZipFile(zip_file_buffer, mode='w') as z:
                z.writestr(f'{function_name}.json', json.dumps(function_data, indent=2).encode())
                z.writestr(function_name + '.zip', code_zip_file.read())

                for layer in layers:
                    layer_response = client.get_layer_version(
                        LayerName=layer['Arn'].split(':')[-2],
                        VersionNumber=int(layer['Arn'].split(':')[-1])
                    )
                    layer_zip_file = BytesIO(urllib.request.urlopen(layer_response['Content']['Location']).read())
                    z.writestr(layer['Arn'].split(':')[-1] + '.zip', layer_zip_file.read())

            zip_file_buffer.seek(0)
            s3.Object(bucket_name, f'{archive_folder}/{region_name}/{function_name}.zip').put(Body=zip_file_buffer.read())
            logging.info(f'The file {function_name}.zip was saved to the {bucket_name}/{archive_folder}/{region_name} path.')

    except ClientError as e:
        logging.error(f'Error processing function {function_name}: {e}')


def delete_function(client, function_name):
    try:
        client.delete_function(FunctionName=function_name)
        logging.info(f'The function {function_name} was deleted.')
    except ClientError as e:
        logging.error(f'Error deleting function {function_name}: {e}')

def lambda_handler(event, context):
    region_name = 'sa-east-1'
    bucket_name = 'NOME-DO-BUCKET'
    archive_folder = 'NOME-DA-PASTA'

    logging.basicConfig(level=logging.INFO)

    session = boto3.Session(region_name=region_name)
    s3 = session.resource('s3')
    client = session.client('lambda')

    bucket = s3.Bucket(bucket_name)
    create_archive_folder(bucket, archive_folder)

    current_date = datetime.datetime.now().strftime('%Y-%m-%d')

    functions_to_archive = []

    paginator = client.get_paginator('list_functions')
    for page in paginator.paginate():
        functions_to_archive.extend(filter(lambda f: should_archive_function(client, f, current_date), page['Functions']))

    for function in functions_to_archive:
        try:
            archive_function(client, s3, bucket_name, archive_folder, region_name, function)
            delete_function(client, function['FunctionName'])
        except Exception as e:
            logging.error(f'Error processing function {function["FunctionName"]}: {e}')