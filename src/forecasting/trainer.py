"""
Trainer - Entrena modelo Prophet.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)

try:
    from prophet import Prophet
except ImportError:
    logger.warning("Prophet no instalado, instalando...")
    import subprocess
    subprocess.run(['pip', 'install', 'prophet', '-q'])
    from prophet import Prophet


class ProphetTrainer:
    """Entrena modelo Prophet para forecasting."""
    
    def __init__(self, models_path: str = "models"):
        self.models_path = Path(models_path)
        self.models_path.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.config = {
            'growth': 'linear',
            'seasonality_mode': 'multiplicative',
            'yearly_seasonality': True,
            'weekly_seasonality': True,
            'daily_seasonality': False,
            'changepoint_prior_scale': 0.05,
            'seasonality_prior_scale': 10.0,
            'holidays_prior_scale': 10.0
        }
    
    def create_model(self) -> Prophet:
        """Crea modelo Prophet con configuracion."""
        model = Prophet(
            growth=self.config['growth'],
            seasonality_mode=self.config['seasonality_mode'],
            yearly_seasonality=self.config['yearly_seasonality'],
            weekly_seasonality=self.config['weekly_seasonality'],
            daily_seasonality=self.config['daily_seasonality'],
            changepoint_prior_scale=self.config['changepoint_prior_scale'],
            seasonality_prior_scale=self.config['seasonality_prior_scale'],
            holidays_prior_scale=self.config['holidays_prior_scale']
        )
        
        model.add_country_holidays(country_name='ES')
        
        return model
    
    def add_regressors(self, model: Prophet, df: pd.DataFrame):
        """Añade regresores al modelo."""
        pass
    
    def train(self, train_df: pd.DataFrame, add_regressors: bool = True) -> Prophet:
        """Entrena el modelo."""
        logger.info("Entrenando modelo Prophet...")
        
        model = self.create_model()
        
        if add_regressors:
            self.add_regressors(model, train_df)
        
        df_for_prophet = train_df[['ds', 'y']].copy()
        
        model.fit(df_for_prophet)
        
        self.model = model
        
        logger.info("Modelo entrenado correctamente")
        
        return model
    
    def save_model(self, filename: str = "prophet_cashflow_model.json"):
        """Guarda el modelo."""
        if self.model is None:
            logger.warning("No hay modelo para guardar")
            return None
        
        filepath = self.models_path / filename
        
        import pickle
        with open(filepath, 'wb') as f:
            pickle.dump(self.model, f)
        
        logger.info(f"Modelo guardado: {filepath}")
        
        return filepath
    
    def save_config(self, filename: str = "model_config.json"):
        """Guarda configuracion del modelo."""
        filepath = self.models_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        logger.info(f"Configuracion guardada: {filepath}")
        
        return filepath
    
    def load_model(self, filename: str = "prophet_cashflow_model.json"):
        """Carga un modelo guardado."""
        filepath = self.models_path / filename
        
        if not filepath.exists():
            logger.error(f"Modelo no encontrado: {filepath}")
            return None
        
        import pickle
        with open(filepath, 'rb') as f:
            self.model = pickle.load(f)
        
        logger.info(f"Modelo cargado: {filepath}")
        
        return self.model


def train_prophet_model(train_df: pd.DataFrame, 
                        models_path: str = "models") -> Prophet:
    """Funcion convenience para entrenar modelo."""
    trainer = ProphetTrainer(models_path)
    model = trainer.train(train_df)
    trainer.save_model()
    trainer.save_config()
    
    return model


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    from data_prep import prepare_forecasting_data
    
    logging.basicConfig(level=logging.INFO)
    
    data = prepare_forecasting_data()
    
    model = train_prophet_model(data['train'])
    
    print("\nModelo entrenado y guardado!")