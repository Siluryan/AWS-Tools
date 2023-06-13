import logging
import boto3

FUNCTIONS_TO_DELETE = ['lambda-teste-para-excluir']
REGION_NAME = 'us-east-1'  

client = boto3.client('lambda', region_name=REGION_NAME)

logging.basicConfig(level=logging.INFO, format='%(message)s')

for function_name in FUNCTIONS_TO_DELETE:
    client.delete_function(FunctionName=function_name)
    logging.info(f"Função Lambda {function_name} removida com sucesso.")