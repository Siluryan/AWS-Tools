import re
import json
import boto3
import logging
import datetime as dt
from datetime import datetime
from botocore.exceptions import ClientError

date = f'{dt.date.today().day}-{dt.date.today().month}-{dt.date.today().year}'

file_name = f'_{date}.json'
file_path = f'/tmp/{file_name}'

bucket_name = ''
object_url = 'Bucket_url/{file_name}'

topic_arn = ''
subject=f'- {date}'
message=f': {object_url}'

def generate_report():
    try:    
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('') 
        response = table.scan()
        data = response['Items']

        for obj in data:
            obj[''] = re.sub(r'[^a-zA-Z0-9]', '', obj[''])   

        json_list = [
            obj for obj in data \
                if obj['name'] != 'prod' and 'awsEBSSize' in obj['']
                    if 'inactivation' not in obj[''] and 'destroyAt' not in obj['']  
                
        ]
        
        for obj in data:
            obj['createdDate'] = datetime.fromtimestamp(int(obj['createdDate'])/1000).strftime('%d-%m-%y')
            obj['modifiedDate'] = datetime.fromtimestamp(int(obj['modifiedDate'])/1000).strftime('%d-%m-%y')

        data = json.dumps(json_list, indent=2, default=str)    

        with open(file_path, 'w') as f:
            f.write(data)
    
    except ClientError as e:        
        logging.error(e)
        return False

    return True 

def send_report_to_s3(file_path, file_name, bucket_name):
    s3_client = boto3.client('s3')
    try:
        with open(file_path, 'rb') as file:
            s3_client.put_object(
            Bucket=bucket_name,
            Key=f'Bucket_Name/{file_name}',
            Body=file
        )
    except ClientError as e:        
        logging.error(e)
        return False 

    return True

def send_notification(topic_arn, subject, message):
    sns = boto3.client('sns')
    try:        
        sns.publish(TopicArn=topic_arn,
                    Subject=subject,
                    Message=message)
    except ClientError as e:
        logging.error(e)
        return False
    
    return True

def handler(event, context):
    generate_report()
    send_report_to_s3(file_path, file_name, bucket_name)
    send_notification(topic_arn, subject, message)