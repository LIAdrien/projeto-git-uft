import sqlite3
from tkinter import INSERT

# 1. Conecta ao banco 
conexao = sqlite3.connect('tributos_piloto.db')
cursor = conexao.cursor()

# 2. Criação das tabelas
cursor.execute(CREATE TABLE IF NOT EXISTS contribuinte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cpf_cnpj_mascarado TEXT NOT NULL,
    score_recuperabilidade REAL
))

cursor.execute(CREATE TABLE IF NOT EXISTS divida_ativa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contribuinte_id INTEGER,
    valor_devido REAL NOT NULL,
    ano_referencia INTEGER,
    FOREIGN KEY (contribuinte_id) REFERENCES contribuinte(id)
))

# 3. População 
contribuintes_piloto = [

]
cursor.executemany(INSERT INTO contribuinte (cpf_cnpj_mascarado, score_recuperabilidade) VALUES (?, ?), contribuintes_piloto)

dividas_piloto = [
    (1, 1500.50, 2022),
    (1, 800.00, 2023),
    (2, 5000.00, 2021)
]
cursor.executemany(INSERT INTO divida_ativa (contribuinte_id, valor_devido, ano_referencia) VALUES (?, ?, ?), dividas_piloto)

# Salva as alterações e fecha
conexao.commit()
conexao.close()

print("Banco SQLite criado e populado com sucesso!")