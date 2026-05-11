"""
Predictor - Genera predicciones con modelo entrenado.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import json
import pickle

logger = logging.getLogger(__name__)


class CashFlowPredictor:
    """Genera predicciones de cash flow."""
    
    def __init__(self, models_path: str = "models"):
        self.models_path = Path(models_path)
        self.model = None
        self.forecast = None
    
    def load_model(self, filename: str = "prophet_cashflow_model.json") -> bool:
        """Carga modelo guardado."""
        filepath = self.models_path / filename
        
        if not filepath.exists():
            logger.error(f"Modelo no encontrado: {filepath}")
            return False
        
        try:
            with open(filepath, 'rb') as f:
                self.model = pickle.load(f)
            logger.info(f"Modelo cargado: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error cargando modelo: {e}")
            return False
    
    def predict(self, periods: int = 90, 
                include_history: bool = True) -> pd.DataFrame:
        """Genera predicciones."""
        if self.model is None:
            logger.error("Modelo no cargado")
            return None
        
        logger.info(f"Generando prediccion para {periods} dias...")
        
        future = self.model.make_future_dataframe(periods=periods)
        
        self.forecast = self.model.predict(future)
        
        logger.info(f"Prediccion completada: {len(self.forecast)} dias")
        
        return self.forecast
    
    def get_forecast_90d(self) -> pd.DataFrame:
        """Obtiene solo los proximos 90 dias."""
        if self.forecast is None:
            self.predict(90)
        
        last_date = self.forecast['ds'].max()
        cutoff = last_date - pd.Timedelta(days=89)
        
        future_forecast = self.forecast[self.forecast['ds'] >= cutoff].copy()
        
        return future_forecast
    
    def get_risk_indicators(self, forecast: pd.DataFrame = None) -> dict:
        """Calcula indicadores de riesgo."""
        if forecast is None:
            forecast = self.forecast
        
        if forecast is None or len(forecast) == 0:
            return {}
        
        min_balance = forecast['yhat'].min()
        avg_balance = forecast['yhat'].mean()
        
        last_30d = forecast.tail(30)
        trend_30d = last_30d['yhat'].iloc[-1] - last_30d['yhat'].iloc[0]
        
        risk_level = "BAJO"
        if min_balance < 25000:
            risk_level = "ALTO"
        elif min_balance < 50000:
            risk_level = "MEDIO"
        
        return {
            'min_forecast_balance': round(min_balance, 2),
            'avg_forecast_balance': round(avg_balance, 2),
            'trend_30d': round(trend_30d, 2),
            'risk_level': risk_level,
            'days_below_threshold': (forecast['yhat'] < 50000).sum()
        }
    
    def save_forecast(self, forecast: pd.DataFrame = None,
                      filename: str = "forecast_results.csv") -> Path:
        """Guarda prediccion a CSV."""
        if forecast is None:
            forecast = self.forecast
        
        if forecast is None:
            logger.warning("No hay forecast para guardar")
            return None
        
        filepath = self.models_path / filename
        
        forecast.to_csv(filepath, index=False)
        
        logger.info(f"Forecast guardado: {filepath}")
        
        return filepath
    
    def save_summary(self, forecast: pd.DataFrame = None,
                     filename: str = "forecast_summary.json") -> Path:
        """Guarda resumen de prediccion."""
        if forecast is None:
            forecast = self.forecast
        
        if forecast is None:
            logger.warning("No hay forecast para guardar")
            return None
        
        indicators = self.get_risk_indicators(forecast)
        
        summary = {
            'forecast_period': {
                'start': str(forecast['ds'].min()),
                'end': str(forecast['ds'].max()),
                'days': int(len(forecast))
            },
            'statistics': {
                'min_balance': float(round(forecast['yhat'].min(), 2)),
                'max_balance': float(round(forecast['yhat'].max(), 2)),
                'mean_balance': float(round(forecast['yhat'].mean(), 2)),
                'std_balance': float(round(forecast['yhat'].std(), 2))
            },
            'risk_indicators': {k: float(v) if isinstance(v, (np.integer, np.floating)) else v 
                              for k, v in indicators.items()}
        }
        
        filepath = self.models_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Resumen guardado: {filepath}")
        
        return filepath


def generate_forecast(models_path: str = "models", 
                     periods: int = 90) -> dict:
    """Funcion convenience para generar forecast."""
    predictor = CashFlowPredictor(models_path)
    
    if not predictor.load_model():
        logger.error("No se pudo cargar el modelo")
        return None
    
    forecast = predictor.predict(periods)
    
    predictor.save_forecast(forecast)
    predictor.save_summary(forecast)
    
    indicators = predictor.get_risk_indicators(forecast)
    
    return {
        'forecast': forecast,
        'indicators': indicators
    }


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    logging.basicConfig(level=logging.INFO)
    
    result = generate_forecast()
    
    if result:
        print("\nForecast generado!")
        print(f"Indicadores de riesgo: {result['indicators']}")