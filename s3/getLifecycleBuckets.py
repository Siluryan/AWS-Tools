import boto3
import botocore
import csv

s3 = boto3.client('s3')

response = s3.list_buckets()
buckets = response['Buckets']

with open('lifecycle_policies.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    
    writer.writerow(['Bucket', 'ID', 'Status', 'Transitions'])
    
    for bucket in buckets:
        try:
            response = s3.get_bucket_lifecycle_configuration(Bucket=bucket['Name'])
            if 'Rules' in response:
                for rule in response['Rules']:
                    writer.writerow([bucket['Name'], rule.get('ID', 'N/A'), rule.get('Status', 'N/A'), rule.get('Transitions', '')])
            else:
                writer.writerow([bucket['Name'], 'N/A', 'N/A', 'N/A'])
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
                writer.writerow([bucket['Name'], 'N/A', 'No Configuration', 'N/A'])
            elif e.response['Error']['Code'] == 'AccessDenied':
                writer.writerow([bucket['Name'], 'N/A', 'Access Denied', 'N/A'])
            else:
                writer.writerow([bucket['Name'], 'Erro', 'Erro', 'Erro'])
        except Exception as e:
            writer.writerow([bucket['Name'], 'Erro', 'Erro', 'Erro'])