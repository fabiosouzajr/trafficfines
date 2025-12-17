# db/database.py
import sqlite3
import os
from trafficfines.config import DATABASE_PATH
from trafficfines.utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    def __init__(self):
        """Initialize database connection"""
        self.conn = None
        self.cursor = None
        self.connect()
        
    def connect(self):
        """Connect to SQLite database"""
        try:
            self.conn = sqlite3.connect(DATABASE_PATH)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            self.cursor = self.conn.cursor()
            self.create_tables()
            logger.info(f"Successfully connected to database: {DATABASE_PATH}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}", exc_info=True)
            return False
    
    def create_tables(self):
        """Create necessary database tables if they don't exist"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS fines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fine_number TEXT UNIQUE,              -- IDENTIFICAÇÃO DO AUTO DE INFRAÇÃO
            notification_date DATE,               -- DATA DA NOTIFICAÇÃO DA AUTUAÇÃO
            defense_due_date DATE,                -- DATA LIMITE PARA INTERPOSIÇÃO DE DEFESA PRÉVIA
            driver_id_due_date DATE,              -- DATA LIMITE PARA IDENTIFICAÇÃO DO CONDUTOR INFRATOR
            license_plate TEXT,                   -- PLACA
            vehicle_model TEXT,                   -- MARCA/MODELO/VERSÃO
            violation_location TEXT,              -- LOCAL DA INFRAÇÃO
            violation_date DATE,                  -- DATA
            violation_time TEXT,                  -- HORA
            violation_code TEXT,                  -- CÓDIGO DA INFRAÇÃO
            amount REAL,                          -- VALOR DA MULTA
            description TEXT,                     -- DESCRIÇÃO DA INFRAÇÃO
            measured_speed TEXT,                  -- MEDIÇÃO REALIZADA
            considered_speed TEXT,                -- VALOR CONSIDERADO
            speed_limit TEXT,                     -- LIMITE REGULAMENTADO
            owner_name TEXT,                      -- NOME DO PROPRIETÁRIO
            owner_document TEXT,                  -- CPF/CNPJ
            pdf_path TEXT,
            payment_event_created BOOLEAN DEFAULT 0,
            driver_id_event_created BOOLEAN DEFAULT 0
        )
        ''')
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """Destructor to ensure database connection is closed"""
        self.close()