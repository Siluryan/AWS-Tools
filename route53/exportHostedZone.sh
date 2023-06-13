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

read -p "Digite o ID da zona hospedada de origem: " source_zone_id
read -p "Digite o nome do arquivo JSON de saída: " json_file

echo "Listando registros DNS da zona hospedada de origem..."
source_records=$(aws route53 list-resource-record-sets --hosted-zone-id $source_zone_id | jq '.ResourceRecordSets')

echo "Filtrando registros DNS da zona hospedada de origem..."
source_filtered_records=$(echo $source_records | jq 'map(select(.Type != "NS" and .Type != "SOA"))')

echo "Adicionando a ação CREATE para cada registro da zona hospedada de origem..."
source_created_records=$(echo $source_filtered_records | jq 'map({Action: "CREATE", ResourceRecordSet: .})')

echo "Convertendo para o formato de mudanças da zona hospedada de origem..."
source_changes=$(echo $source_created_records | jq '{Changes: .}')

echo "Salvando mudanças no arquivo JSON..."
echo $source_changes | jq . > $json_file

echo "O arquivo $json_file da zona hospedada de origem foi gerado com sucesso."