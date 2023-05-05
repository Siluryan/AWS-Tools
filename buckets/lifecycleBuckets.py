import csv
import boto3

s3 = boto3.client('s3')

response = s3.list_buckets()
buckets = response['Buckets']

with open('lifecycle_policies.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    
    writer.writerow(['Bucket', 'ID', 'Status', 'Transições'])
    
    for bucket in buckets:
        try:
            response = s3.get_bucket_lifecycle_configuration(Bucket=bucket['Name'])
            if 'Rules' in response:
                for rule in response['Rules']:
                    writer.writerow([bucket['Name'], rule['ID'], rule['Status'], rule.get('Transitions', '')])
            else:
                writer.writerow([bucket['Name'], 'N/A', 'N/A', 'N/A'])
        except:
            writer.writerow([bucket['Name'], 'Erro', 'Erro', 'Erro'])
