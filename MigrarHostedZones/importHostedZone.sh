# Solicita as informações de IAM da zona hospedada de destino
read -p "Digite o ID do role da IAM da zona hospedada de destino: " destination_role_id
read -p "Digite o nome do role da IAM da zona hospedada de destino: " destination_role_name
read -p "Digite o nome da sessão da IAM da zona hospedada de destino: " destination_session_name

# Assume o role da IAM da zona hospedada de destino
echo "Assumindo o role da IAM da zona hospedada de destino..."
destination_assume_role=$(aws sts assume-role --role-arn arn:aws:iam::$destination_role_id:role/$destination_role_name --role-session-name $destination_session_name)
destination_access_key=$(echo $destination_assume_role | jq -r '.Credentials.AccessKeyId')
destination_secret_key=$(echo $destination_assume_role | jq -r '.Credentials.SecretAccessKey')
destination_session_token=$(echo $destination_assume_role | jq -r '.Credentials.SessionToken')

# Configura as credenciais da zona hospedada de destino
echo "Configurando as credenciais da zona hospedada de destino..."
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
export AWS_ACCESS_KEY_ID=$destination_access_key
export AWS_SECRET_ACCESS_KEY=$destination_secret_key
export AWS_SESSION_TOKEN=$destination_session_token

# Solicita as informações da zona hospedada de destino
read -p "Digite o ID da zona hospedada de destino: " hosted_zone_id
read -p "Digite o nome do arquivo JSON com as mudanças: " json_file

# Realiza a mudança de conjunto de registros na zona hospedada
echo "Realizando mudança de conjunto de registros na zona hospedada..."
aws route53 change-resource-record-sets --hosted-zone-id $hosted_zone_id --change-batch file://$json_file

echo "A mudança de conjunto de registros na zona hospedada foi concluída com sucesso."