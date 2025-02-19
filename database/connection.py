import sqlite3
import os

class Database:
    def __init__(self, db_path='employee.db'):
        self.db_path = db_path
        
    def get_connection(self):
        return sqlite3.connect(self.db_path)

def get_database():
    return Database()
