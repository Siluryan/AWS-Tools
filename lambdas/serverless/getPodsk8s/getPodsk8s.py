import boto3
import os
import subprocess
import urllib.request
import logging
from datetime import datetime

s3_bucket = "NOME-DO-BUCKET"
s3_folder = "NOME-DA-PASTA"

parameter_name = "/NOME-DO-PARAMETRO"

cluster_url = "https://api.k8s.CLUSTER.com.br"
kubectl_version_url = "https://dl.k8s.io/release/stable.txt"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def download_file(url, output_path):
    with urllib.request.urlopen(url) as response:
        with open(output_path, "wb") as file:
            file.write(response.read())

def lambda_handler(event, context):
    ssm_client = boto3.client("ssm")
    response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
    secret_value = response["Parameter"]["Value"]

    kubeconfig = "/tmp/kubeconfig"
    with open(kubeconfig, "w", encoding="utf-8") as file:
        file.write(secret_value)

    now = datetime.now()
    date_suffix = now.strftime('%d-%m-%Y')
    output_file = f"/tmp/output_{date_suffix}.csv"
    kubectl_path = f"/tmp/{s3_folder}/kubectl"

    with urllib.request.urlopen(kubectl_version_url) as response:
        kubectl_version = response.read().decode("utf-8").strip()

    kubectl_url = f"https://dl.k8s.io/release/{kubectl_version}/bin/linux/amd64/kubectl"

    os.makedirs(os.path.dirname(kubectl_path), exist_ok=True)
    download_file(kubectl_url, kubectl_path)
    os.chmod(kubectl_path, 0o755)

    kubectl_command = [
        kubectl_path,
        "--kubeconfig",
        kubeconfig,
        "get",
        "pods",
        "-A",
        "-o",
        "custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,READY:.status.containerStatuses[0].ready,STATUS:.status.phase,RESTARTS:.status.containerStatuses[0].restartCount,AGE:.metadata.creationTimestamp",
        "--no-headers=true"
    ]
    output = subprocess.check_output(kubectl_command, stderr=subprocess.STDOUT)

    logger.info("kubectl command output:")
    logger.info(output.decode())

    lines = output.decode().splitlines()
    output_csv = "\n".join([",".join(line.split()) for line in lines])

    header = "NAMESPACE,NAME,READY,STATUS,RESTARTS,AGE"
    output_csv = header + "\n" + output_csv

    with open(output_file, "w", encoding="utf-8") as file:
        file.write(output_csv)

    s3_key = f"{s3_folder}/pods-homolog-nhu_{date_suffix}.csv"
    s3 = boto3.client("s3")
    s3.upload_file(output_file, s3_bucket, s3_key)

    return {
        "statusCode": 200,
        "body": "Arquivo CSV salvo no S3 com sucesso!"
    }
