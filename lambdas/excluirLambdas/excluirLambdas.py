import pandas as pd
import boto3

CSV_INPUT = 'csv-filtrado.csv' #csv com as lambdas que serão EXCLUIDAS

client = boto3.client('lambda')

df = pd.read_csv(CSV_INPUT)

for function_name in df['FunctionName']:
    response = client.delete_function(FunctionName=function_name)
    print('Função Lambda {} removida com sucesso.'.format(function_name))