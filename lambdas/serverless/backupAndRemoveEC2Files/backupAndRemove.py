import os
import boto3
import paramiko
import tempfile
from zipfile import ZipFile
from datetime import datetime

ec2 = boto3.client('ec2')
s3 = boto3.client('s3')
ssm = boto3.client('ssm')

def lambda_handler(event, context):
    try:
        INSTANCE_ID = os.getenv('INSTANCE_ID')
        BUCKET_NAME = os.getenv('BUCKET_NAME')
        PATH = os.getenv('PATH')
        YEAR_LIMIT = int(os.getenv('YEAR_LIMIT'))
        SSH_PRIVATE_KEY = os.getenv('SSH_PRIVATE_KEY_PARAMETER_STORE_NAME')

        response = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
        internal_ip = response['Reservations'][0]['Instances'][0]['PrivateIpAddress']

        key_param = ssm.get_parameter(Name=SSH_PRIVATE_KEY, WithDecryption=True)
        private_key = key_param['Parameter']['Value']

        files = get_files(internal_ip, PATH, private_key)

        filtered_files = [file for file in files if datetime.strptime(file['lastModifiedDate'], '%Y-%m-%d %H:%M:%S').year < YEAR_LIMIT]

        with tempfile.NamedTemporaryFile(delete=False) as tmp_zip_file:
            with ZipFile(tmp_zip_file, 'w') as zipf:
                for file in filtered_files:
                    download_file(internal_ip, PATH, file['fileName'], zipf, private_key)

            tmp_zip_file.seek(0)
            s3.upload_fileobj(tmp_zip_file, BUCKET_NAME, 'files.zip')

        return {
            'statusCode': 200,
            'body': 'Files transferred and compressed successfully.'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }

def get_files(ip_address, PATH, private_key):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    key = paramiko.RSAKey.from_private_key_file(file_obj=private_key)
    ssh.connect(ip_address, username=os.getenv('USERNAME'), pkey=key)

    command = f"ls -l --time-style=long-iso {PATH} | grep -v '^d'"
    stdin, stdout, stderr = ssh.exec_command(command)

    files = []
    for line in stdout.readlines():
        parts = line.split()
        if len(parts) >= 8:
            file_info = {
                'fileName': parts[-1],
                'lastModifiedDate': ' '.join(parts[5:8]),
            }
            files.append(file_info)

    ssh.close()

    return files

def download_file(ip_address, PATH, file_name, zipf, private_key):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    key = paramiko.RSAKey.from_private_key_file(file_obj=private_key)
    ssh.connect(ip_address, username=os.getenv('USERNAME'), pkey=key)

    sftp = ssh.open_sftp()
    remote_PATH = os.path.join(PATH, file_name)
    local_PATH = os.path.join('/tmp', file_name)
    sftp.get(remote_PATH, local_PATH)
    sftp.close()

    ssh.close()

    zipf.write(local_PATH, arcname=file_name)