import os
import re
import json
import datetime
import atexit
from createRegistry import create_registry

def get_utc_minus_3():
    current_utc = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    return current_utc.date(), current_utc.time()
  
data, hora = get_utc_minus_3()

data_string = data.strftime("%Y-%m-%d")
hora_string = hora.strftime("%H:%M:%S")

def clean_value(value):
    cleaned_value = value.split()[0].strip() if value else ""
    return cleaned_value

def parse_info(file_content):
    info_dict = {}
    deleted_objects = []

    keywords = [
        "Bucket de origem:",
        "Bucket de destino:",
        "Nome do objeto compactado:",
        "Conta de origem:",
        "Conta de destino:",
        "Prefix:",
        "Sufix:",
    ]

    deleted_object_pattern = r"Objeto Deletado:\s*([^\n]+)"

    deleted_object_matches = re.findall(deleted_object_pattern, file_content, re.IGNORECASE | re.MULTILINE)

    deleted_objects.extend(map(str.strip, deleted_object_matches))

    for keyword in keywords:
        pattern = rf"{re.escape(keyword)}\s*([^\n]+)(?=\n|$)"
        match = re.search(pattern, file_content, re.IGNORECASE | re.DOTALL)
        if match:
            value = match.group(1).strip()
            cleaned_value = clean_value(value)
            if keyword == "Prefix:" or keyword == "Sufix:":
                cleaned_value = cleaned_value if re.match(r'^[a-zA-Z0-9_]+$', cleaned_value) else "null"
            if keyword not in info_dict:
                info_dict[keyword] = cleaned_value

    info_dict["Objetos Deletados"] = deleted_objects

    return info_dict


def save_as_json(info_dict, output_path):
    with open(output_path, "w") as json_file:
        json.dump(info_dict, json_file, indent=4)

def process_log_file(log_file):
    with open(log_file, "r") as input_file:
        file_content = input_file.read()
        info_dict = parse_info(file_content)

        info_dict["Data da Compactacao"] = data_string
        info_dict["Hora da Compactacao"] = hora_string
        
        return info_dict

def create_dictionary():
    output_dir = "output_json"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for root, dirs, files in os.walk(".", topdown=True):
        for file in files:
            if file.endswith(".log"):
                log_file_path = os.path.join(root, file)
                output_file_path = os.path.join(output_dir, f"{file}.json")

                info_dict = process_log_file(log_file_path)
                save_as_json(info_dict, output_file_path)   

   
atexit.register(create_registry)