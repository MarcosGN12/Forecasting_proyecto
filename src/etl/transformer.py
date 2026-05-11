"""
Transformer - Limpieza, transformación y agregación de datos.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transforma datos raw en datos procesados."""
    
    def __init__(self):
        self.processed_path = Path("data/processed")
        self.processed_path.mkdir(parents=True, exist_ok=True)
    
    def transform_invoices(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y transforma facturas."""
        logger.info("Transformando invoices...")
        
        df = df.copy()
        
        df['invoice_date'] = pd.to_datetime(df['invoice_date'])
        df['due_date'] = pd.to_datetime(df['due_date'])
        df['paid_date'] = pd.to_datetime(df['paid_date'], errors='coerce')
        
        df['status'] = df['status'].fillna('unknown')
        
        df['payment_method'] = df['payment_method'].fillna('transfer')
        
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
        df['vat'] = pd.to_numeric(df['vat'], errors='coerce').fillna(0)
        df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0)
        
        df = df.drop_duplicates(subset=['invoice_id'])
        
        df['days_to_pay'] = (df['paid_date'] - df['invoice_date']).dt.days
        
        df['is_overdue'] = (df['status'] == 'pending') & (df['due_date'] < pd.Timestamp.now())
        
        logger.info(f"  - invoices transformadas: {len(df):,} registros")
        
        return df
    
    def transform_bank_movements(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y transforma movimientos bancarios."""
        logger.info("Transformando bank_movements...")
        
        df = df.copy()
        
        df['date'] = pd.to_datetime(df['date'])
        df['value_date'] = pd.to_datetime(df['value_date'], errors='coerce')
        
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df['balance_after'] = pd.to_numeric(df['balance_after'], errors='coerce')
        
        df['description'] = df['description'].fillna('Sin descripcion')
        
        df = df.drop_duplicates(subset=['movement_id'])
        
        df = df.sort_values('date')
        
        df['is_inflow'] = df['amount'] > 0
        df['is_outflow'] = df['amount'] < 0
        
        df['cash_flow'] = df['amount']
        
        df['category'] = df['category'].fillna('other')
        
        logger.info(f"  - movimientos transformados: {len(df):,} registros")
        
        return df
    
    def transform_crm_deals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y transforma deals de CRM."""
        logger.info("Transformando crm_deals...")
        
        df = df.copy()
        
        df['created_date'] = pd.to_datetime(df['created_date'])
        df['expected_close'] = pd.to_datetime(df['expected_close'], errors='coerce')
        df['actual_close'] = pd.to_datetime(df['actual_close'], errors='coerce')
        df['closed_date'] = pd.to_datetime(df['closed_date'], errors='coerce')
        
        df['expected_amount'] = pd.to_numeric(df['expected_amount'], errors='coerce').fillna(0)
        df['probability'] = pd.to_numeric(df['probability'], errors='coerce').fillna(0)
        
        df['stage'] = df['stage'].fillna('unknown')
        
        df['is_won'] = df['stage'] == 'won'
        df['is_lost'] = df['stage'] == 'lost'
        
        df['weighted_value'] = df['expected_amount'] * df['probability']
        
        logger.info(f"  - deals transformados: {len(df):,} registros")
        
        return df
    
    def transform_employees(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia datos de empleados."""
        logger.info("Transformando employees...")
        
        df = df.copy()
        
        df['salary'] = pd.to_numeric(df['salary'], errors='coerce').fillna(0)
        df['ss_contribution'] = pd.to_numeric(df['ss_contribution'], errors='coerce').fillna(0)
        
        df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
        
        df['department'] = df['department'].fillna('unknown')
        df['contract_type'] = df['contract_type'].fillna('permanent')
        
        logger.info(f"  - empleados transformados: {len(df):,} registros")
        
        return df
    
    def transform_suppliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia datos de proveedores."""
        logger.info("Transformando suppliers...")
        
        df = df.copy()
        
        df['payment_cycle'] = pd.to_numeric(df['payment_cycle'], errors='coerce').fillna(30)
        df['typical_amount'] = pd.to_numeric(df['typical_amount'], errors='coerce').fillna(0)
        
        df['category'] = df['category'].fillna('unknown')
        
        logger.info(f"  - proveedores transformados: {len(df):,} registros")
        
        return df
    
    def transform_external_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia factores externos."""
        logger.info("Transformando external_factors...")
        
        df = df.copy()
        
        df['date'] = pd.to_datetime(df['date'])
        
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        df['indicator'] = df['indicator'].fillna('unknown')
        df['source'] = df['source'].fillna('unknown')
        
        logger.info(f"  - factores transformados: {len(df):,} registros")
        
        return df
    
    def create_cash_flow_daily(self, bank_df: pd.DataFrame) -> pd.DataFrame:
        """Crea serie temporal diaria de cash flow."""
        logger.info("Creando cash_flow_daily...")
        
        bank_df = bank_df.copy()
        bank_df['date'] = pd.to_datetime(bank_df['date'])
        
        daily_agg = bank_df.groupby('date').agg({
            'amount': 'sum',
            'balance_after': 'last',
            'movement_id': 'count'
        }).reset_index()
        
        daily_agg.columns = ['date', 'net_cash', 'cash_balance', 'transaction_count']
        
        daily_agg['cash_inflow'] = daily_agg['net_cash'].apply(
            lambda x: x if x > 0 else 0
        )
        daily_agg['cash_outflow'] = daily_agg['net_cash'].apply(
            lambda x: abs(x) if x < 0 else 0
        )
        
        date_range = pd.date_range(
            start=daily_agg['date'].min(),
            end=daily_agg['date'].max(),
            freq='D'
        )
        
        daily_agg = daily_agg.set_index('date')
        daily_agg = daily_agg.reindex(date_range)
        daily_agg.index.name = 'date'
        
        daily_agg['cash_balance'] = daily_agg['cash_balance'].interpolate(method='linear')
        daily_agg['net_cash'] = daily_agg['net_cash'].fillna(0)
        daily_agg['cash_inflow'] = daily_agg['cash_inflow'].fillna(0)
        daily_agg['cash_outflow'] = daily_agg['cash_outflow'].fillna(0)
        daily_agg['transaction_count'] = daily_agg['transaction_count'].fillna(0)
        
        daily_agg = daily_agg.reset_index()
        
        logger.info(f"  - cash_flow_daily: {len(daily_agg):,} dias")
        
        return daily_agg
    
    def transform_all(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Aplica todas las transformaciones."""
        logger.info("Iniciando transformacion completa...")
        
        transformed = {}
        
        if 'invoices' in datasets:
            transformed['invoices_clean'] = self.transform_invoices(datasets['invoices'])
        
        if 'bank_movements' in datasets:
            transformed['bank_clean'] = self.transform_bank_movements(datasets['bank_movements'])
            
            transformed['cash_flow_daily'] = self.create_cash_flow_daily(
                transformed['bank_clean']
            )
        
        if 'crm_deals' in datasets:
            transformed['crm_deals_clean'] = self.transform_crm_deals(datasets['crm_deals'])
        
        if 'employees' in datasets:
            transformed['employees_clean'] = self.transform_employees(datasets['employees'])
        
        if 'suppliers' in datasets:
            transformed['suppliers_clean'] = self.transform_suppliers(datasets['suppliers'])
        
        if 'external_factors' in datasets:
            transformed['external_factors_clean'] = self.transform_external_factors(
                datasets['external_factors']
            )
        
        logger.info(f"Transformacion completada: {len(transformed)} datasets")
        
        return transformed
    
    def save_processed(self, datasets: Dict[str, pd.DataFrame]):
        """Guarda datasets procesados a CSV."""
        logger.info("Guardando datasets procesados...")
        
        for name, df in datasets.items():
            filepath = self.processed_path / f"{name}.csv"
            df.to_csv(filepath, index=False, encoding='utf-8')
            logger.info(f"  - Guardado: {name}.csv ({len(df):,} registros)")


def transform_all_data(raw_path: str = "data/raw", 
                       processed_path: str = "data/processed") -> Dict[str, pd.DataFrame]:
    """Función convenience para transformar todos los datos."""
    from extractor import DataExtractor
    
    extractor = DataExtractor(raw_path)
    datasets = extractor.load_all()
    
    transformer = DataTransformer()
    transformed = transformer.transform_all(datasets)
    transformer.save_processed(transformed)
    
    return transformed


if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    
    logging.basicConfig(level=logging.INFO)
    transformed = transform_all_data()
    
    print("\n=== TRANSFORMACION COMPLETADA ===")
    for name, df in transformed.items():
        print(f"{name}: {len(df):,} registros")