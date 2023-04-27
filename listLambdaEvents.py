import os
import re
import json
import datetime
from datetime import datetime

region = 'us-east-1'

names = 'functionNames.txt'
details = 'detailFunctions.json'

tmp = 'tmp_log'
list_default = []

os.system(f'aws lambda list-functions --region {region} | grep "FunctionName" > {names}')
os.system(f'aws lambda list-functions --region {region} > {details}')

with open(names,'r') as f:
    f_Names = f.read()

f_Names = re.sub(r'[,:\"\ ]', '', f_Names)
f_Names = re.sub('FunctionName', '', f_Names)

with open(names, 'w') as f:
    f.write(f_Names)

with open(names, 'r') as f:    
    for line in f:
        line = re.sub('\n',"", line)        
        list_default.append(line)

for line in list_default:          
    os.system(f'aws logs describe-log-streams --log-group-name /aws/lambda/{line} \
              --region {region} \
              --max-items 1 \
              --order-by LastEventTime \
              --descending | grep -E "arn|lastEventTimestamp" >> {tmp} \
              && echo \n >> {tmp}')   

with open(details,'r') as f:
    detail_json = f.read()

detail_dict = json.loads(detail_json)

with open(tmp,'r') as f:   
    list_default = [] 
    for line in f:
        line = re.sub(r'[","\n,\ ]',"", line).strip()        
        list_default.append(line)     
          
for log in list_default:
    for info in range(len(detail_dict["Functions"])):    
        i = list_default.index(log) 
        name = detail_dict["Functions"][info]["FunctionName"]                
        if re.fullmatch(name, log[62:62+len(name)]):                      
            tm_tmp = int(list_default[i-1][-13:])
            dt_obj = datetime.fromtimestamp(tm_tmp/1000).strftime('%d-%m-%y')
            detail_dict["Functions"][info].update({'LastEventTimestamp':tm_tmp})        
            detail_dict["Functions"][info].update({'LastEventDatetime':dt_obj})                             
 
detail_content = json.dumps(detail_dict, indent=2)

with open(details,'w') as f:
     f.write(detail_content)

os.remove(tmp)