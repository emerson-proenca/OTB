from sqlite_utils import Database

db = Database("dados.db")
meu_dicionario = {"id": 1, "nome": "exemplo"}

# Isso cria a tabela e insere os dados automaticamente
db["minha_tabela"].insert(meu_dicionario, pk="id")
