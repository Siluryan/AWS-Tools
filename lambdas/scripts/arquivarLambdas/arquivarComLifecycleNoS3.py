import json
import boto3
import logging
import requests
import zipfile
from io import BytesIO
from botocore.exceptions import ClientError

bucket_name = 'backups'
archive_folder = 'archive-lambdas'

glacier_deep_archive_days = 365
lifecycle_policy_name = 'GDA-por-365-dias'

region_name = 'sa-east-1'
function_names = ['teste-archive-lambdas']

logging.basicConfig(level=logging.INFO)

session = boto3.Session(region_name=region_name)
s3 = session.resource('s3')
client = session.client('s3')

bucket = s3.Bucket(bucket_name)
archive_folder_exists = any(obj.key == f'{archive_folder}/' for obj in bucket.objects.filter(Prefix=f'{archive_folder}/'))

if not archive_folder_exists:
    bucket.put_object(Key=f'{archive_folder}/')
    logging.info(f'{archive_folder} folder created in {bucket_name} bucket.')

try:
    bucket_lifecycle_configuration = client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
    lifecycle_rules = bucket_lifecycle_configuration.get('Rules', [])
except ClientError as e:
    if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
        lifecycle_rules = []
    else:
        raise

archive_rule_exists = any(rule.get('ID') == lifecycle_policy_name for rule in lifecycle_rules)

if not archive_rule_exists:
    new_rule = {
        'ID': lifecycle_policy_name,
        'Status': 'Enabled',
        'Filter': {
            'Prefix': f'{archive_folder}/'
        },
        'Transitions': [
            {
                'Days': 0,
                'StorageClass': 'DEEP_ARCHIVE'
            }
        ],
        'Expiration': {
            'Days': glacier_deep_archive_days
        }
    }

    lifecycle_rules.append(new_rule)

    lifecycle_configuration = {'Rules': lifecycle_rules}
    client.put_bucket_lifecycle_configuration(Bucket=bucket_name, LifecycleConfiguration=lifecycle_configuration)
    logging.info(f'Lifecycle configuration applied to objects inside {bucket_name}/{archive_folder} path.')
else:
    logging.info(f'Lifecycle configuration already exists for {bucket_name}/{archive_folder} path. Skipping creation.')

client = session.client('lambda')

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