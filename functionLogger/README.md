# Logger de Funções

Obs.: os índices podem ser adaptados de acordo com as informações que precisam ser armazenadas no dynamoDB (o caso de uso foi um compactador de arquivos)

O logger de funções permite registrar atividades de funções em um arquivo de log e armazená-las em um diretório estruturado com base na data e hora. O código também é configurado para salvar logs agregados quando o script é encerrado.

## functionLogger.py

O código é composto por vários componentes que se combinam para criar um sistema de registro de logs. Aqui estão os principais pontos de funcionamento:

### Decorator `@function_logger`

O decorator `@function_logger` é usado para envolver funções que você deseja registrar. Quando uma função é decorada com `@function_logger`, ela fará o seguinte:

- Inicializa um logger específico para o módulo da função.
- Define o nível de log para INFO.
- Configura um manipulador de fluxo (stream handler) que direciona as mensagens de log para um buffer de string em memória.
- Define um formato para as mensagens de log.
- Chama a função decorada e captura seu valor de retorno.
- Recupera o conteúdo do log a partir do buffer de string.
- Agrega o conteúdo do log sob o nome da função no dicionário `log_contents`.
- Remove o manipulador de fluxo para interromper o registro no buffer de string.
- Retorna o valor de retorno da função decorada.

### Dicionário `log_contents`

O dicionário `log_contents` é usado para armazenar o conteúdo do log para cada função decorada. O conteúdo é agregado sob o nome da função no dicionário.

### Função `store_aggregated_logs`

A função `store_aggregated_logs` é registrada com `atexit` e é executada quando o script é encerrado. Ela faz o seguinte:

- Obtém a hora atual (UTC - 3 horas) para criar um timestamp.
- Agrega todo o conteúdo do log sob um formato específico, separando os logs de diferentes funções.
- Cria uma estrutura de diretórios com base na data atual (ano e mês) e cria um arquivo de log timestamped dentro desse diretório.
- Salva o conteúdo agregado no arquivo de log.

### `atexit.register(create_dictionary)`

Esta linha registra a função `create_dictionary` para ser executada quando o script é encerrado.

## createDictionary.py

Essa parte do código é usada para processar arquivos de log, extrair informações específicas deles e salvá-las em arquivos JSON. O código é organizado de forma a realizar as seguintes tarefas:

### Função Principal

O coração do projeto é a função `create_dictionary()` que é responsável por:

1. Criar um diretório chamado "output_json" se ele ainda não existir. Este é o diretório onde os arquivos JSON resultantes serão salvos.

2. Recursivamente buscar arquivos de log (com extensão ".log") no diretório atual e em seus subdiretórios.

3. Para cada arquivo de log encontrado, chamar a função `process_log_file()` para extrair informações específicas do arquivo e armazená-las em um dicionário.

4. Adicionar informações adicionais ao dicionário, incluindo a data e a hora da compactação do log.

5. Salvar o dicionário resultante como um arquivo JSON no diretório "output_json", com o mesmo nome de arquivo do log original, mas com a extensão ".json".

### Funções de Apoio

- `get_utc_minus_3()`: Obtém a data e a hora atuais em UTC, subtrai 3 horas e retorna esses valores.

- `clean_value(value)`: Limpa uma string removendo espaços em branco extras e retornando a primeira parte da string.

- `parse_info(file_content)`: Analisa o conteúdo de um arquivo de log em busca de informações específicas usando expressões regulares e palavras-chave predefinidas. Ele extrai informações como "Bucket de origem", "Bucket de destino", "Objeto Deletado" e outras, armazenando-as em um dicionário.

- `save_as_json(info_dict, output_path)`: Salva um dicionário como um arquivo JSON no caminho especificado.

### Observações

- O script processa todos os arquivos de log encontrados no diretório e em seus subdiretórios, portanto, certifique-se de que os arquivos de log sejam os desejados antes de executar o script.

- As informações específicas extraídas dos arquivos de log são definidas pelas palavras-chave predefinidas no código. Certifique-se de que essas palavras-chave correspondam ao formato dos seus arquivos de log.

- O script registra a data e a hora da compactação do log em cada arquivo JSON resultante.

- Certifique-se de que o diretório de saída "output_json" esteja vazio ou não exista antes de executar o script, pois os arquivos JSON resultantes serão substituídos ou adicionados a esse diretório.

---

## createRegistry.py

Esse código foi desenvolvido para processar arquivos JSON e inserir dados em uma tabela do AWS DynamoDB com base no conteúdo desses arquivos. Ele foi projetado para ser usado em um ambiente AWS e é útil para lidar com dados estruturados em formato JSON.

## Requisitos

Para executar este script, você precisará das seguintes dependências e configurações:

- Variáveis de ambiente para as credenciais AWS:
  - `FUNCTION_LOGGER_ACCESS_KEY`: Chave de acesso AWS
  - `FUNCTION_LOGGER_SECRET_KEY`: Chave secreta AWS
- Uma tabela do DynamoDB existente no AWS com o nome especificado no script.

### `processar_arquivo`

Esta função é responsável pelo processamento de um arquivo JSON específico. Ela realiza as seguintes etapas:

1. Abre o arquivo JSON especificado.
2. Tenta carregar o conteúdo do arquivo JSON.
3. Extrai informações específicas do arquivo JSON e as estrutura em um formato adequado para inserção no DynamoDB.
4. Lida com exceções, caso ocorram, e registra erros usando o módulo de `logging`.

### `percorrer_diretorio`

Esta função é usada para percorrer recursivamente um diretório em busca de arquivos JSON. Ela realiza o seguinte:

1. Aceita um diretório como entrada.
2. Utiliza a biblioteca `os` para percorrer recursivamente o diretório em busca de arquivos com extensão `.json`.
3. Para cada arquivo JSON encontrado, chama a função `processar_arquivo` para processá-lo e inserir seus dados na tabela do DynamoDB.

### `create_registry`

Esta é a função principal do script. Ela faz o seguinte:

1. Determina o diretório que contém os arquivos JSON a serem processados (geralmente três níveis acima do local atual do script).
2. Registra o diretório encontrado usando o módulo `logging`.
3. Chama a função `percorrer_diretorio` para processar e inserir dados de todos os arquivos JSON encontrados.

## Configurações necessárias

Siga estas etapas para poder realizar o registro dos logs no DynamoDB:

1. Instale as dependências Python mencionadas na seção de requisitos.
2. Configure as variáveis de ambiente `FUNCTION_LOGGER_ACCESS_KEY` e `FUNCTION_LOGGER_SECRET_KEY` com suas credenciais AWS.
3. Verifique se você tem uma tabela do DynamoDB com o nome especificado ou ajuste o nome da tabela no script, se necessário.

Certifique-se de que as credenciais fornecidas têm as permissões necessárias para acessar e inserir dados na tabela do DynamoDB.

---

## Exemplo de Uso

Aqui está um exemplo de como usar o decorator `@function_logger`:

```python
@function_logger()
def minha_funcao():
    # Seu código aqui
    pass
```
