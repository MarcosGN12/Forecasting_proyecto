"""
Gestor de base de datos SQLite.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List, Tuple
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


class DatabaseManager:
    """Gestor de base de datos SQLite."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', 'data/cashflow.db')
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
    
    def connect(self):
        """Conecta a la base de datos."""
        if self.conn is None:
            self.conn = sqlite3.connect(str(self.db_path))
            logger.info(f"Conectado a {self.db_path}")
        return self.conn
    
    def close(self):
        """Cierra la conexión."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Conexión cerrada")
    
    def execute(self, query: str, params: tuple = None) -> List[Tuple]:
        """Ejecuta una query."""
        conn = self.connect()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor.fetchall()
    
    def execute_many(self, query: str, data: List[tuple]):
        """Ejecuta una query con múltiples datos."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.executemany(query, data)
        conn.commit()
    
    def create_tables(self):
        """Crea las tablas del proyecto."""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Tabla de facturas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                invoice_id TEXT PRIMARY KEY,
                invoice_date TEXT,
                due_date TEXT,
                customer_id TEXT,
                customer_name TEXT,
                amount REAL,
                vat REAL,
                total REAL,
                status TEXT,
                paid_date TEXT,
                payment_method TEXT,
                category TEXT
            )
        """)
        
        # Tabla de movimientos bancarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bank_movements (
                movement_id TEXT PRIMARY KEY,
                date TEXT,
                value_date TEXT,
                description TEXT,
                amount REAL,
                balance_after REAL,
                category TEXT,
                reference TEXT,
                bank_account TEXT
            )
        """)
        
        # Tabla de deals CRM
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crm_deals (
                deal_id TEXT PRIMARY KEY,
                deal_name TEXT,
                customer_id TEXT,
                customer_name TEXT,
                stage TEXT,
                probability REAL,
                expected_amount REAL,
                expected_close TEXT,
                actual_close TEXT,
                created_date TEXT,
                closed_date TEXT
            )
        """)
        
        # Tabla de cash flow diario
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cash_flow_daily (
                date TEXT PRIMARY KEY,
                cash_balance REAL,
                cash_inflow REAL,
                cash_outflow REAL,
                net_cash REAL,
                transaction_count INTEGER
            )
        """)
        
        # Tabla de forecast
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forecast_results (
                ds TEXT PRIMARY KEY,
                yhat REAL,
                yhat_lower REAL,
                yhat_upper REAL,
                trend REAL,
                yearly REAL,
                weekly REAL
            )
        """)
        
        # Tabla de métricas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_metrics (
                metric_name TEXT PRIMARY KEY,
                metric_value REAL,
                created_at TEXT
            )
        """)
        
        # Tabla de alertas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_code TEXT,
                severity TEXT,
                message TEXT,
                triggered_at TEXT,
                resolved INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        logger.info("Tablas creadas correctamente")
    
    def load_csv(self, table_name: str, csv_path: str, if_exists: str = 'replace'):
        """Carga un CSV en una tabla."""
        df = pd.read_csv(csv_path)
        
        # Convertir fechas a string para SQLite
        date_cols = ['date', 'invoice_date', 'due_date', 'paid_date', 
                    'created_date', 'expected_close', 'actual_close', 'closed_date',
                    'value_date', 'ds']
        for col in date_cols:
            if col in df.columns:
                df[col] = df[col].astype(str)
        
        df.to_sql(table_name, self.connect(), if_exists=if_exists, index=False)
        logger.info(f"Tabla {table_name} actualizada con {len(df)} registros")
    
    def load_all_csv(self, data_dir: str = "data/raw"):
        """Carga todos los CSVs a la base de datos."""
        data_path = Path(data_dir)
        
        # Mapeo de archivos a tablas
        csv_mapping = {
            'invoices.csv': 'invoices',
            'bank_movements.csv': 'bank_movements',
            'crm_deals.csv': 'crm_deals',
        }
        
        for csv_file, table_name in csv_mapping.items():
            csv_path = data_path / csv_file
            if csv_path.exists():
                self.load_csv(table_name, str(csv_path))
        
        # Cargar datos procesados
        processed_path = Path("data/processed")
        if (processed_path / "cash_flow_daily.csv").exists():
            self.load_csv('cash_flow_daily', str(processed_path / "cash_flow_daily.csv"))
        
        # Cargar forecast
        models_path = Path("models")
        if (models_path / "forecast_results.csv").exists():
            self.load_csv('forecast_results', str(models_path / "forecast_results.csv"))
    
    def query_to_dataframe(self, query: str) -> pd.DataFrame:
        """Ejecuta una query y devuelve un DataFrame."""
        return pd.read_sql_query(query, self.connect())
    
    def get_current_balance(self) -> float:
        """Obtiene el balance actual."""
        query = "SELECT cash_balance FROM cash_flow_daily ORDER BY date DESC LIMIT 1"
        result = self.execute(query)
        return result[0][0] if result else 0
    
    def get_forecast_90d(self) -> float:
        """Obtiene la predicción a 90 días."""
        query = """
            SELECT yhat FROM forecast_results 
            ORDER BY ABS(julianday(ds) - julianday('now', '+90 days')) 
            LIMIT 1
        """
        result = self.execute(query)
        return result[0][0] if result else 0
    
    def save_alert(self, code: str, severity: str, message: str):
        """Guarda una alerta en la base de datos."""
        from datetime import datetime
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO alerts (alert_code, severity, message, triggered_at) VALUES (?, ?, ?, ?)",
            (code, severity, message, datetime.now().isoformat())
        )
        conn.commit()
        logger.info(f"Alerta guardada: {code}")


def init_database(db_path: str = None) -> DatabaseManager:
    """Inicializa la base de datos."""
    db = DatabaseManager(db_path)
    db.create_tables()
    return db


def load_csv_to_sqlite(csv_path: str, table_name: str, db_path: str = None):
    """Carga un CSV a SQLite."""
    db = DatabaseManager(db_path)
    db.load_csv(table_name, csv_path)


def get_connection(db_path: str = None) -> sqlite3.Connection:
    """Obtiene una conexión directa."""
    if db_path is None:
        db_path = os.getenv('DATABASE_PATH', 'data/cashflow.db')
    return sqlite3.connect(db_path)


def query(sql: str, db_path: str = None) -> pd.DataFrame:
    """Ejecuta una query y devuelve DataFrame."""
    db = DatabaseManager(db_path)
    return db.query_to_dataframe(sql)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Inicializando base de datos...")
    db = init_database()
    
    print("Cargando CSVs...")
    db.load_all_csv()
    
    print("\nEstadísticas:")
    print(f"  Balance actual: {db.get_current_balance():,.2f}€")
    print(f"  Forecast 90d: {db.get_forecast_90d():,.2f}€")
    
    db.close()
    print("\nBase de datos lista!")