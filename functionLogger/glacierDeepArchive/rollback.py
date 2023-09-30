import boto3
import zipfile
import os
import botocore.exceptions

partition_key_value = input("Digite o valor da partition key (ObjetoOrigem): ")

original_credentials = boto3.Session().get_credentials()

conta_role_map = {
    "dev": "arn:aws:iam::000000000000:role/dev",
    "homolog": "arn:aws:iam::000000000000:role/homolog",
    "prod": "arn:aws:iam::000000000000:role/prod",
}

def assumir_role(role_arn, original_credentials):
    sts_client = boto3.client('sts')
    try:
        response = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName='AssumeRoleSession'
        )
        return response['Credentials']
    except botocore.exceptions.ClientError as e:
        print(f"Erro ao assumir a role {role_arn}: {str(e)}")
        return original_credentials

def buscar_informacoes_dynamodb(partition_key_value):
    dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
    table_name = 'compact-s3-logs'

    response = dynamodb_client.query(
        TableName=table_name,
        KeyConditionExpression='ObjetoOrigem = :value',
        ExpressionAttributeValues={
            ':value': {'S': partition_key_value}
        }
    )

    if not response['Items']:
        print("Nenhum item encontrado.")
        return

    item = response['Items'][0]
    recuperado_do_gda = item.get('RecuperadoDoGDA', {}).get('S')

    if recuperado_do_gda != "true":
        print("A execução foi interrompida porque RecuperadoDoGDA não é true.")
        return

    return item

def buscar_objeto_s3(bucket_name, nome_objeto):
    s3_client = boto3.client('s3')

    try:
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key=nome_objeto
        )
        return response['Body'].read()
    except Exception as e:
        print(f"Erro ao buscar objeto no S3: {str(e)}")
        return None

def buscar_valor_em_zip(zip_data, valor_busca):
    with open('temp.zip', 'wb') as temp_zip_file:
        temp_zip_file.write(zip_data)

    valor_busca = valor_busca.split("/")[-1]

    with zipfile.ZipFile('temp.zip', 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            if valor_busca in file_info.filename:
                with zip_ref.open(file_info.filename) as extracted_file:
                    with open(valor_busca, 'wb') as local_file:
                        local_file.write(extracted_file.read())
                return True

        for file_info in zip_ref.infolist():
            if file_info.is_dir():
                subfolder = file_info.filename
                for subfile_info in zip_ref.infolist():
                    if valor_busca in os.path.join(subfolder, subfile_info.filename):
                        with zip_ref.open(os.path.join(subfolder, subfile_info.filename)) as extracted_file:
                            with open(valor_busca, 'wb') as local_file:
                                local_file.write(extracted_file.read())
                        return True

    return False

def main():
    role_arn_prod = conta_role_map.get('prod')

    if role_arn_prod:
        prod_credentials = assumir_role(role_arn_prod, original_credentials)

    if prod_credentials:
        boto3.setup_default_session(
            aws_access_key_id=prod_credentials['AccessKeyId'],
            aws_secret_access_key=prod_credentials['SecretAccessKey'],
            aws_session_token=prod_credentials['SessionToken']
        )

    item = buscar_informacoes_dynamodb(partition_key_value)

    boto3.setup_default_session(
        aws_access_key_id=original_credentials.access_key,
        aws_secret_access_key=original_credentials.secret_key,
        aws_session_token=original_credentials.token
    )
    if item:
        conta_origem = item.get('ContaOrigem', {}).get('S')
        conta_destino = item.get('ContaDestino', {}).get('S')
        bucket_origem = item.get('BucketOrigem', {}).get('S')
        bucket_destino = item.get('BucketDestino', {}).get('S')
        nome_objeto_compactado = item.get('NomeObjetoCompactado', {}).get('S')
        prefix = item.get('prefix', {}).get('S', '')  
        
        role_arn_origem = conta_role_map.get(conta_origem)
        role_arn_destino = conta_role_map.get(conta_destino)

        if role_arn_destino:
            conta_destino_credentials = assumir_role(role_arn_destino, original_credentials)
            boto3.setup_default_session(
                aws_access_key_id=conta_destino_credentials['AccessKeyId'],
                aws_secret_access_key=conta_destino_credentials['SecretAccessKey'],
                aws_session_token=conta_destino_credentials['SessionToken']
            )
            
            objeto_zip = buscar_objeto_s3(bucket_destino, nome_objeto_compactado)
            
            if objeto_zip:
                nome_objeto_original = partition_key_value.rsplit('/', 1)
                valor_busca = nome_objeto_original[-1] 
                if buscar_valor_em_zip(objeto_zip, valor_busca):
                    print(f"Valor '{valor_busca}' encontrado no arquivo ZIP.")
                    
                    boto3.setup_default_session(
                        aws_access_key_id=original_credentials.access_key,
                        aws_secret_access_key=original_credentials.secret_key,
                        aws_session_token=original_credentials.token
                    )
                    
                    if role_arn_origem:
                        conta_origem_credentials = assumir_role(role_arn_origem, original_credentials)
                        boto3.setup_default_session(
                            aws_access_key_id=conta_origem_credentials['AccessKeyId'],
                            aws_secret_access_key=conta_origem_credentials['SecretAccessKey'],
                            aws_session_token=conta_origem_credentials['SessionToken']
                        )
                        
                        s3_client = boto3.client('s3')

                        if prefix != 'null':
                            s3_key = os.path.join(prefix, valor_busca)
                        else:
                            s3_key = valor_busca
                        
                        try:
                            s3_client.upload_file(valor_busca, bucket_origem, s3_key)
                            print(f"Arquivo '{valor_busca}' enviado para o bucket '{bucket_origem}' com sucesso.")
                        except Exception as e:
                            print(f"Erro ao enviar o arquivo para o bucket: {str(e)}")
                    
                else:
                    print(f"Valor '{valor_busca}' não encontrado no arquivo ZIP.")

    boto3.setup_default_session(
        aws_access_key_id=original_credentials.access_key,
        aws_secret_access_key=original_credentials.secret_key,
        aws_session_token=original_credentials.token
    )

if __name__=="__main__":
    main()