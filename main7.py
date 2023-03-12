import tabula
import json

# Lendo o PDF.
df = tabula.read_pdf("carros.pdf", pages="1,2", lattice=True, multiple_tables=True)

# Removendo os caracteres '\r' dos nomes das colunas.
# Removendo as colunas 'fantasmas' (Unnamed).
for i in range(len(df)):
    for col in df[i].columns:
        df[i].rename(columns={col: col.replace('\r', ' ')}, inplace=True)
        if col.startswith('Unnamed'):
            del df[i][col]

# Identificando os índices dos DataFrames que contém as tabelas de interesse.
green_tables_indexes = []
blue_tables_indexes = []
for i in range(len(df)):
    for col in df[i].columns:
        if col == "CÓDIGO DE VENDAS":
            green_tables_indexes.append(i)
        # TODO: identificar a tabela azul de outro modo (não pelo nome da coluna, pois ele varia).
        elif col == "TRACKER - ANO/MODELO 2024":
            blue_tables_indexes.append(i)

# Montando os mapas de carros. A chave é o código de vendas e o valor é um
# dicionário com as informações do carro.
cars_map = {}
for i in range(len(green_tables_indexes)):
    table_index = green_tables_indexes[i]
    for j in range(len(df[table_index])):
        iloc = df[table_index].iloc[j]
        codigo_vendas = iloc[0]
        descricao_vendas = iloc[1]
        marca_modelo = iloc[2]
        descricao_cat = iloc[3]
        producao = iloc[4]
        cars_map[codigo_vendas] = {
            "descricao_vendas": descricao_vendas,
            "marca_modelo": int(marca_modelo),
            "descricao_cat": descricao_cat,
            "producao": producao
        }
# Salvando os dados do dicionário como um JSON em um arquivo
car_json = json.dumps(cars_map, indent=4)
file = open("sample.json", "w")
file.write(str(car_json))
file.close()