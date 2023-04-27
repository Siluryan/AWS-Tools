import boto3

s3_client = boto3.client('s3')

buckets = s3_client.list_buckets()

for bucket in buckets['Buckets']:   
    bucket_name = bucket['Name']
    bucket_url = "https://s3.{0}.amazonaws.com/{1}".format\
        (s3_client.get_bucket_location(Bucket=bucket_name)['LocationConstraint'], bucket_name)
   
    bucket_size = 0
    bucket_object_count = 0
    
    next_token = ''    
    
    while True:        
        objects = s3_client.list_objects_v2(Bucket=bucket_name, ContinuationToken=next_token)
        
        for obj in objects['Contents']:            
            bucket_size += obj['Size'] / 1024 / 1024            
            bucket_object_count += 1
               
        if 'NextContinuationToken' in objects:
            next_token = objects['NextContinuationToken']
        else:
            break
    
with open('bucket_info.txt', 'w') as f:
    for bucket_info in buckets:
        f.write("{0}\n".format(bucket_info))