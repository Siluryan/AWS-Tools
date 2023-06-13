import boto3
import csv

region = 'us-east-1'
s3_client = boto3.client('s3', region_name=region)

response = s3_client.list_buckets()
buckets = response['Buckets']

header = ['Bucket Name', 'Log Bucket', 'Log Prefix']
rows = []

for bucket in buckets:
    bucket_name = bucket['Name']
    print(f"Verificando bucket: {bucket_name}")

    try:
        response = s3_client.get_bucket_logging(Bucket=bucket_name)
        logging_enabled = response.get('LoggingEnabled')
        if logging_enabled:
            log_bucket = logging_enabled.get('TargetBucket')
            log_prefix = logging_enabled.get('TargetPrefix')
        else:
            log_bucket = None
            log_prefix = None

        row = [bucket_name, log_bucket, log_prefix]
        rows.append(row)
        print(f"Bucket de log: {log_bucket}")
        print(f"Prefixo de log: {log_prefix}")
    except Exception as e:
        print(f"Erro ao obter informações do bucket: {bucket_name}")
        print(str(e))
    
    print()

output_file = f'buckets_logging-{region}.csv'
with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(header)
    writer.writerows(rows)