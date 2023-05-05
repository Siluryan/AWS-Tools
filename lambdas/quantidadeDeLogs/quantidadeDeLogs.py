import boto3
import csv
from datetime import datetime, timedelta

region_name = 'sa-east-1'
start_time = datetime.strptime('02-05-2023 00:00:00', '%d-%m-%Y %H:%M:%S') # datetime.strptime('02-05-2023 00:00:00', '%d-%m-%Y %H:%M:%S')
end_time = datetime.strptime('03-05-2023 23:59:59', '%d-%m-%Y %H:%M:%S') # datetime.strptime('03-05-2023 23:59:59', '%d-%m-%Y %H:%M:%S')

client = boto3.client('logs', region_name=region_name)

lambda_executions = {}

paginator = client.get_paginator('describe_log_groups')
for response in paginator.paginate(logGroupNamePrefix='/aws/lambda/'):
    for function in response['logGroups']:
        for day in range((end_time - start_time).days + 1):
            current_day_start = start_time + timedelta(days=day)
            current_day_end = current_day_start + timedelta(days=1) - timedelta(seconds=1)

            response = client.filter_log_events(
                logGroupName=function['logGroupName'],
                startTime=int(current_day_start.timestamp() * 1000),
                endTime=int(current_day_end.timestamp() * 1000),
                filterPattern='REPORT'
            )

            lambda_executions.setdefault(function['logGroupName'], 0)
            lambda_executions[function['logGroupName']] += len(response['events'])

with open(f'lambda-executions_{region_name}.csv', mode='w', newline='') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(['Lambda', 'Execuções'])
    for function, executions in lambda_executions.items():
        writer.writerow([function, executions])