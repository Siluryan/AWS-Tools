import json
import boto3
import logging
import requests
import zipfile
from io import BytesIO
from botocore.exceptions import ClientError

# Lista de nomes das funções a serem processadas
region_name = 'sa-east-1'
function_names = ['teste-archive-lambdas']

bucket_name = 'tec-backups'
archive_folder = 'backup-lambdas'

logging.basicConfig(level=logging.INFO)

session = boto3.Session(region_name=region_name)
s3 = session.resource('s3')
client = session.client('lambda')

bucket = s3.Bucket(bucket_name)
archive_folder_exists = any(obj.key == f'{archive_folder}/' for obj in bucket.objects.filter(Prefix=f'{archive_folder}/'))

if not archive_folder_exists:
    bucket.put_object(Key=f'{archive_folder}/')
    logging.info(f'{archive_folder} folder created in {bucket_name} bucket.')

for function_name in function_names:
    try:
        code_response = client.get_function(FunctionName=function_name)
        code_zip_file = BytesIO(requests.get(code_response['Code']['Location']).content)

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
                    layer_zip_file = BytesIO(requests.get(layer_response['Content']['Location']).content)
                    z.writestr(layer['Arn'].split(':')[-1] + '.zip', layer_zip_file.read())

            zip_file_buffer.seek(0)
            s3.Object(bucket_name, f'{archive_folder}/{region_name}/{function_name}.zip').put(Body=zip_file_buffer.read())
            logging.info(f'The file {function_name}.zip was saved to the {bucket_name}/{archive_folder}/{region_name} path.')
    except ClientError as e:
        logging.error(f'Error processing function {function_name}: {e}')