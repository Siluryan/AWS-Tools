import pandas as pd
import time

MESES_SEM_USO = 6
CSV_INPUT = 'infoLambdas_us-east-1.csv'
CSV_OUTPUT = 'filter-infoLambdas_us-east-1.csv'

df = pd.read_csv(CSV_INPUT)

data_limite = int(time.time() * 1000) - (MESES_SEM_USO * 30 * 24 * 60 * 60 * 1000)

colunas_filtradas = []

for coluna in df.columns:    
    colunas_filtradas.append(coluna)

df_filtrado = df[colunas_filtradas]

df_filtrado = df_filtrado[(df_filtrado['LastEventTimestamp'].isnull()) | (df_filtrado['LastEventTimestamp'] <= data_limite)]

df_filtrado.to_csv(CSV_OUTPUT, index=False)