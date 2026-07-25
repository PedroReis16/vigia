"""
Instância compartilhada da conexão com o banco de dados
"""

from peewee import SqliteDatabase

db: SqliteDatabase = SqliteDatabase(None)
