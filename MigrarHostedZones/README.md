Antes de começar, certifique-se de pegar as seguintes informações:

Export Hosted Zone:

- ID da zona hospedada de origem
- ID do role da IAM da zona hospedada de origem
- Nome do role da IAM da zona hospedada de origem

Certifique-se também de criar pelo console da AWS a Hosted Zone na conta de *destino* com o **mesmo nome**
da Hosted Zone na conta de *origem*, e pegue as informações referentes a nova zona:

Import Hosted Zone:

- ID da zona hospedada de destino
- ID do role da IAM da zona hospedada de destino
- Nome do role da IAM da zona hospedada de destino

Verifique se você possui o utilitário **jq** instalado na sua máquina local, e dê permissão de execução para ambos os scripts com **chmod +x** caso esteja usando linux.

Execute o script `exportHostedZone.sh`, e depois execute o `importHostedZone.sh`
Nos dois scripts serão solicitados o nome do arquivo JSON que será criado e usado para configurar a nova hosted zone. Use o mesmo nome nos dois casos.

Para mais informações, consulte a [documentação oficial](https://docs.aws.amazon.com/pt_br/Route53/latest/DeveloperGuide/hosted-zones-migrating.html) da AWS sobre migração de zonas.