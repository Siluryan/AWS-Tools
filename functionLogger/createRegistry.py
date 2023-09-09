import boto3
import os
import json
import logging

aws_access_key_id = os.environ.get('FUNCTION_LOGGER_ACCESS_KEY')
aws_secret_access_key = os.environ.get('FUNCTION_LOGGER_SECRET_KEY')
region = 'REGION-NAME'

table_name = 'TABLE-NAME'

dynamodb = boto3.client(
    'dynamodb',
    region_name=region,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

def processar_arquivo(caminho_arquivo):
    with open(caminho_arquivo, 'r') as arquivo:
        try:
            dados = json.load(arquivo)

            compactacao_item = {
                'BucketOrigem': {'S': dados.get('Bucket de origem:', 'null')},
                'BucketDestino': {'S': dados.get('Bucket de destino:', 'null')},
                'NomeObjetoCompactado': {'S': dados.get('Nome do objeto compactado:', 'null')},
                'ContaOrigem': {'S': dados.get('Conta de origem:', 'null')},
                'ContaDestino': {'S': dados.get('Conta de destino:', 'null')},
                'DataCompactacao': {'S': dados.get('Data da Compactacao', 'null')},
                'HoraCompactacao': {'S': dados.get('Hora da Compactacao', 'null')}
            }

            if 'Prefix:' in dados:
                compactacao_item['PrefixoOrigem'] = {'S': dados['Prefix:']}
            if 'Sufix:' in dados:
                compactacao_item['SufixoOrigem'] = {'S': dados['Sufix:']}

            objetos_deletados = dados.get('Objetos Deletados', [])
            for objeto_deletado in objetos_deletados:
                deleted_object_item = {
                    'ObjetoDeletado': {'S': objeto_deletado},
                }

                deleted_object_item.update(compactacao_item)

                dynamodb.put_item(
                    TableName=table_name,
                    Item=deleted_object_item
                )

        except Exception as e:
            logging.error(f"Error processing JSON file {caminho_arquivo}: {e}")

def percorrer_diretorio(diretorio):
    for raiz, _, arquivos in os.walk(diretorio):
        for arquivo in arquivos:
            if arquivo.endswith('.json'):
                caminho_arquivo = os.path.join(raiz, arquivo)
                processar_arquivo(caminho_arquivo)

def create_registry():
    diretorio_json = os.path.dirname(os.path.abspath(__file__))

    for i in range(3):
        diretorio_json = os.path.dirname(diretorio_json)

    logging.info(f'diretorio{diretorio_json}')

    percorrer_diretorio(diretorio_json)