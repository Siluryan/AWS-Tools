#!/bin/bash

# Solicita as informações de IAM da zona hospedada de origem
read -p "Digite o ID do role da IAM da zona hospedada de origem: " source_role_id
read -p "Digite o nome do role da IAM da zona hospedada de origem: " source_role_name
read -p "Digite o nome da sessão da IAM da zona hospedada de origem: " source_session_name

# Assume o role da IAM da zona hospedada de origem
echo "Assumindo o role da IAM da zona hospedada de origem..."
source_assume_role=$(aws sts assume-role --role-arn arn:aws:iam::$source_role_id:role/$source_role_name --role-session-name $source_session_name)
source_access_key=$(echo $source_assume_role | jq -r '.Credentials.AccessKeyId')
source_secret_key=$(echo $source_assume_role | jq -r '.Credentials.SecretAccessKey')
source_session_token=$(echo $source_assume_role | jq -r '.Credentials.SessionToken')

# Configura as credenciais da zona hospedada de origem
echo "Configurando as credenciais da zona hospedada de origem..."
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
export AWS_ACCESS_KEY_ID=$source_access_key
export AWS_SECRET_ACCESS_KEY=$source_secret_key
export AWS_SESSION_TOKEN=$source_session_token

# Solicita as informações da zona hospedada de origem
read -p "Digite o ID da zona hospedada de origem: " source_zone_id
read -p "Digite o nome do arquivo JSON de saída: " json_file

# Listar registros DNS da zona hospedada de origem
echo "Listando registros DNS da zona hospedada de origem..."
source_records=$(aws route53 list-resource-record-sets --hosted-zone-id $source_zone_id | jq '.ResourceRecordSets')

# Filtrar registros DNS da zona hospedada de origem
echo "Filtrando registros DNS da zona hospedada de origem..."
source_filtered_records=$(echo $source_records | jq 'map(select(.Type != "NS" and .Type != "SOA"))')

# Adicionar a ação "CREATE" para cada registro da zona hospedada de origem
echo "Adicionando a ação CREATE para cada registro da zona hospedada de origem..."
source_created_records=$(echo $source_filtered_records | jq 'map({Action: "CREATE", ResourceRecordSet: .})')

# Converter para o formato de mudanças da zona hospedada de origem
echo "Convertendo para o formato de mudanças da zona hospedada de origem..."
source_changes=$(echo $source_created_records | jq '{Changes: .}')

# Salvar mudanças no arquivo JSON
echo "Salvando mudanças no arquivo JSON..."
echo $source_changes | jq . > $json_file

echo "O arquivo $json_file da zona hospedada de origem foi gerado com sucesso."