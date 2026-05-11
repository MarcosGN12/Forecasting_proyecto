"""
Data Prep - Prepara datos para Prophet.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DataPreparator:
    """Prepara serie temporal para Prophet."""
    
    def __init__(self, processed_path: str = "data/processed"):
        self.processed_path = Path(processed_path)
        self.models_path = Path("models")
        self.models_path.mkdir(parents=True, exist_ok=True)
    
    def load_cash_flow(self) -> pd.DataFrame:
        """Carga datos de cash flow diario."""
        filepath = self.processed_path / "cash_flow_daily.csv"
        
        df = pd.read_csv(filepath, parse_dates=['date'])
        df = df.set_index('date')
        
        logger.info(f"Cargados {len(df)} dias de cash flow")
        
        return df
    
    def prepare_prophet_df(self, df: pd.DataFrame, target_col: str = 'cash_balance') -> pd.DataFrame:
        """Prepara DataFrame en formato Prophet."""
        prophet_df = pd.DataFrame()
        prophet_df['ds'] = df.index
        prophet_df['y'] = df[target_col].values
        
        prophet_df = prophet_df.dropna()
        
        logger.info(f"DataFrame Prophet preparado: {len(prophet_df)} registros")
        
        return prophet_df
    
    def add_features(self, df: pd.DataFrame, cash_flow_df: pd.DataFrame) -> pd.DataFrame:
        """Añade features adicionales."""
        df = df.copy()
        
        df['day_of_week'] = df['ds'].dt.dayofweek
        df['month'] = df['ds'].dt.month
        df['quarter'] = df['ds'].dt.quarter
        df['day_of_month'] = df['ds'].dt.day
        df['week_of_year'] = df['ds'].dt.isocalendar().week.astype(int)
        df['is_month_end'] = df['ds'].dt.is_month_end.astype(int)
        df['is_month_start'] = df['ds'].dt.is_month_start.astype(int)
        
        if 'cash_inflow' in cash_flow_df.columns:
            df['cash_inflow'] = cash_flow_df['cash_inflow'].values
            df['cash_outflow'] = cash_flow_df['cash_outflow'].values
            df['net_cash'] = cash_flow_df['net_cash'].values
        
        return df
    
    def load_external_factors(self) -> pd.DataFrame:
        """Carga factores externos."""
        filepath = self.processed_path / "external_factors_clean.csv"
        
        if not filepath.exists():
            logger.warning("Factores externos no encontrados")
            return None
        
        df = pd.read_csv(filepath, parse_dates=['date'])
        
        interest_rates = df[df['indicator'] == 'interest_rate'][['date', 'value']]
        interest_rates = interest_rates.rename(columns={'value': 'interest_rate'})
        
        inflation = df[df['indicator'] == 'inflation'][['date', 'value']]
        inflation = inflation.rename(columns={'value': 'inflation'})
        
        sector_growth = df[df['indicator'] == 'sector_growth'][['date', 'value']]
        sector_growth = sector_growth.rename(columns={'value': 'sector_growth'})
        
        return interest_rates, inflation, sector_growth
    
    def merge_external_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fusiona factores externos."""
        interest, inflation, sector = self.load_external_factors()
        
        if interest is None:
            return df
        
        interest = interest.rename(columns={'date': 'ds'})
        inflation = inflation.rename(columns={'date': 'ds'})
        sector = sector.rename(columns={'date': 'ds'})
        
        df = df.merge(interest, on='ds', how='left')
        df = df.merge(inflation, on='ds', how='left')
        df = df.merge(sector, on='ds', how='left')
        
        if 'interest_rate' in df.columns:
            df['interest_rate'] = df['interest_rate'].interpolate(method='linear')
        if 'inflation' in df.columns:
            df['inflation'] = df['inflation'].interpolate(method='linear')
        if 'sector_growth' in df.columns:
            df['sector_growth'] = df['sector_growth'].interpolate(method='linear')
        
        logger.info("Factores externos mergeados")
        
        return df
    
    def split_train_test(self, df: pd.DataFrame, test_size: float = 0.2) -> tuple:
        """Divide train/test manteniendo orden temporal."""
        split_idx = int(len(df) * (1 - test_size))
        
        train = df.iloc[:split_idx].copy()
        test = df.iloc[split_idx:].copy()
        
        logger.info(f"Train: {len(train)} dias, Test: {len(test)} dias")
        
        return train, test
    
    def prepare_all(self, target_col: str = 'cash_balance') -> dict:
        """Prepara todos los datos para entrenamiento."""
        logger.info("Preparando datos para Prophet...")
        
        cash_flow = self.load_cash_flow()
        
        prophet_df = self.prepare_prophet_df(cash_flow, target_col)
        
        prophet_df = self.add_features(prophet_df, cash_flow)
        
        prophet_df = self.merge_external_factors(prophet_df)
        
        train, test = self.split_train_test(prophet_df)
        
        return {
            'full': prophet_df,
            'train': train,
            'test': test,
            'cash_flow': cash_flow
        }


def prepare_forecasting_data(processed_path: str = "data/processed") -> dict:
    """Funcion convenience."""
    preparator = DataPreparator(processed_path)
    return preparator.prepare_all()


if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    
    logging.basicConfig(level=logging.INFO)
    data = prepare_forecasting_data()
    
    print(f"\nDatos preparados:")
    print(f"  Full: {len(data['full'])} registros")
    print(f"  Train: {len(data['train'])} registros")
    print(f"  Test: {len(data['test'])} registros")
    print(f"\nColumnas: {data['full'].columns.tolist()}")