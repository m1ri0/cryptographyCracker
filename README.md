# Cryptography Cracker

Vamos usar:
1. Python
    - Poetry
    - SQLAlchemy
    - Celery (RabbitMQ)
    - FastAPI
2. Docker
3. PostgresSQL

Rodar o código:
`sudo docker compose up --build`
use este comando na pasta principal do projeto

Então abra no seu navegador `localhost:8000` e a interface da API estará disponível

Wordlists:
- Por padrao o projeto usa `./wordlists/Pwdb_top-10000000.txt` dentro do container.
- Para usar varias wordlists em ordem, configure `WORDLIST_PATHS` com caminhos separados por virgula.
- Tambem e possivel apontar para um diretorio; os arquivos dele serao usados em ordem alfabetica.

Exemplo:
`WORDLIST_PATHS=./wordlists/top.txt,./wordlists/br.txt sudo docker compose up --build`

No PowerShell:
`$env:WORDLIST_PATHS="./wordlists/top.txt,./wordlists/br.txt"; docker compose up --build`

Cracker sequencial para comparacao:
`python sequencial/sequencial.py --hash <md5> --wordlists src/wordlists`
ou
`python sequencial/sequencial.py --password batata --wordlists src/wordlists`
