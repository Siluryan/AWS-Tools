#!/bin/bash

read -p "Digite o ID do role da IAM da zona hospedada de destino: " destination_role_id
read -p "Digite o nome do role da IAM da zona hospedada de destino: " destination_role_name
read -p "Digite o nome da sessão da IAM da zona hospedada de destino: " destination_session_name

echo "Assumindo o role da IAM da zona hospedada de destino..."
destination_assume_role=$(aws sts assume-role --role-arn arn:aws:iam::$destination_role_id:role/$destination_role_name --role-session-name $destination_session_name)

if [ $? -eq 0 ]; then
    destination_access_key=$(echo $destination_assume_role | jq -r '.Credentials.AccessKeyId')
    destination_secret_key=$(echo $destination_assume_role | jq -r '.Credentials.SecretAccessKey')
    destination_session_token=$(echo $destination_assume_role | jq -r '.Credentials.SessionToken')

    echo "Configurando as credenciais da zona hospedada de destino..."
    aws configure set aws_access_key_id "$destination_access_key"
    aws configure set aws_secret_access_key "$destination_secret_key"
    aws configure set aws_session_token "$destination_session_token"

    echo "Você assumiu a role com sucesso!"
else
    echo "Falha ao assumir a role. Verifique se as credenciais e o ARN da role estão corretos."
fi

read -p "Digite o ID da zona hospedada de destino: " hosted_zone_id
read -p "Digite o nome do arquivo JSON com as mudanças: " json_file

echo "Realizando mudança de conjunto de registros na zona hospedada..."
aws route53 change-resource-record-sets --hosted-zone-id $hosted_zone_id --change-batch file://$json_file

echo "A mudança de conjunto de registros na zona hospedada foi concluída com sucesso."