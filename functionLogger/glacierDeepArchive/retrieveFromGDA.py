import boto3
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

sts_client = boto3.client('sts', region_name='us-east-1')

conta_destino_role_map = {
    'dev': 'arn:aws:iam::000000000000:role/dev',
    'homolog': 'arn:aws:iam::000000000000:role/homolog',
    'prod': 'arn:aws:iam::000000000000:role/prod',
}

def assumir_role(role_arn):
    try:
        response = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName='session-name'
        )
        return response['Credentials']
    except Exception as e:
        logging.error(f"Erro ao assumir a role: {e}")
        return None

def initiate_glacier_retrieval(bucket_name, object_key, s3_credentials):
    try:
        s3_client = boto3.client(
            's3',
            region_name='us-east-1',
            aws_access_key_id=s3_credentials['AccessKeyId'],
            aws_secret_access_key=s3_credentials['SecretAccessKey'],
            aws_session_token=s3_credentials['SessionToken']
        )

        restore_request = {
            'Days': 1,
            'GlacierJobParameters': {
                'Tier': 'Standard'
            }
        }

        response = s3_client.restore_object(
            Bucket=bucket_name,
            Key=object_key,
            RestoreRequest=restore_request
        )
        logging.info(f"Initiated retrieval job for object '{object_key}' in bucket '{bucket_name}'")
        return response
    except Exception as e:
        logging.error(f"Error initiating retrieval job: {e}")
        return None

def wait_for_retrieval_confirmation(bucket_name, object_key, s3_credentials):
    try:
        s3_client = boto3.client(
            's3',
            region_name='us-east-1',
            aws_access_key_id=s3_credentials['AccessKeyId'],
            aws_secret_access_key=s3_credentials['SecretAccessKey'],
            aws_session_token=s3_credentials['SessionToken']
        )

        waiter = s3_client.get_waiter('object_exists')
        waiter.wait(
            Bucket=bucket_name,
            Key=object_key,
            WaiterConfig={'Delay': 60, 'MaxAttempts': 60}
        )
        logging.info(f"Retrieval confirmed for object '{object_key}' in bucket '{bucket_name}'")
    except Exception as e:
        logging.error(f"Error waiting for retrieval confirmation: {e}")

def consultar_dynamodb(partition_key_value, dynamodb_credentials):
    dynamodb_client = boto3.client(
        'dynamodb',
        region_name='us-east-1',
        aws_access_key_id=dynamodb_credentials['AccessKeyId'],
        aws_secret_access_key=dynamodb_credentials['SecretAccessKey'],
        aws_session_token=dynamodb_credentials['SessionToken']
    )

    try:
        response = dynamodb_client.get_item(
            TableName='compact-s3-logs',
            Key={
                'ObjetoOrigem': {'S': partition_key_value}
            }
        )
        return response.get('Item')
    except Exception as e:
        logging.error(f"Erro ao consultar o DynamoDB: {e}")
        return None

def marcar_objeto_como_recuperado(partition_key_value, dynamodb_credentials):
    dynamodb_client = boto3.client(
        'dynamodb',
        region_name='us-east-1',
        aws_access_key_id=dynamodb_credentials['AccessKeyId'],
        aws_secret_access_key=dynamodb_credentials['SecretAccessKey'],
        aws_session_token=dynamodb_credentials['SessionToken']
    )

    try:
        response = dynamodb_client.update_item(
            TableName='compact-s3-logs',
            Key={
                'ObjetoOrigem': {'S': partition_key_value}
            },
            UpdateExpression="SET RecuperadoDoGDA = :val",
            ExpressionAttributeValues={
                ":val": {"S": "true"}
            }
        )
        logging.info(f"Objeto '{partition_key_value}' marcado como recuperado na tabela DynamoDB")
    except Exception as e:
        logging.error(f"Erro ao marcar objeto como recuperado na tabela DynamoDB: {e}")

def main():
    partition_key_value = input("Digite o valor da partition key 'ObjetoOrigem': ")

    dynamodb_role_arn = 'arn:aws:iam::000000000000:role/main'
    dynamodb_credentials = assumir_role(dynamodb_role_arn)

    if dynamodb_credentials:
        item = consultar_dynamodb(partition_key_value, dynamodb_credentials)

        if item:
            conta_destino = item.get('ContaDestino', {}).get('S')
            nome_objeto_compactado = item.get('NomeObjetoCompactado', {}).get('S')

            if conta_destino and nome_objeto_compactado:
                role_arn = conta_destino_role_map.get(conta_destino)

                if role_arn:
                    conta_destino_credentials = assumir_role(role_arn)

                    if conta_destino_credentials:
                        bucket_destino = item.get('BucketDestino', {}).get('S')
                        retrieval_response = initiate_glacier_retrieval(bucket_destino, nome_objeto_compactado, conta_destino_credentials)

                        if retrieval_response:
                            wait_for_retrieval_confirmation(bucket_destino, nome_objeto_compactado, conta_destino_credentials)

                            marcar_objeto_como_recuperado(partition_key_value, dynamodb_credentials)

                    else:
                        logging.error("Não foi possível assumir a role na conta de destino.")
                else:
                    logging.error(f"ARN de role não encontrado para a conta destino: {conta_destino}")
            else:
                logging.error("Não foram encontrados valores para ContaDestino ou NomeObjetoCompactado.")
        else:
            logging.error(f"Objeto com partition key {partition_key_value} não encontrado no DynamoDB.")
    else:
        logging.error("Não foi possível assumir a role para acessar o DynamoDB.")

if __name__ == "__main__":
    main()