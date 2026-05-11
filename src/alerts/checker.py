"""
Checker - Evalua condiciones de alerta.
"""

import pandas as pd
import numpy as np
from typing import List, Dict
import yaml
import logging

logger = logging.getLogger(__name__)


class AlertChecker:
    """Evalua condiciones de alertas."""
    
    def __init__(self, config_path: str = "config/alerts.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.thresholds = self.config['alerts']['thresholds']
    
    def check_balance_threshold(self, current_balance: float) -> Dict:
        """A1: Cash balance < umbral."""
        if current_balance < self.thresholds['min_balance']:
            return {
                'code': 'A1',
                'severity': 'CRITICAL',
                'message': f"CASH BAJO: {current_balance:,.0f}€ (min: {self.thresholds['min_balance']:,.0f}€)",
                'triggered': True
            }
        return {'code': 'A1', 'triggered': False}
    
    def check_variation_7d(self, cash_data: pd.DataFrame) -> Dict:
        """A2: Caida > 15% en 7 dias."""
        if len(cash_data) < 7:
            return {'code': 'A2', 'triggered': False}
        
        current = cash_data.iloc[-1]['cash_balance']
        old = cash_data.iloc[-7]['cash_balance']
        
        if old == 0:
            return {'code': 'A2', 'triggered': False}
        
        variation = (current - old) / old
        
        if variation < self.thresholds['min_variation_7d']:
            return {
                'code': 'A2',
                'severity': 'HIGH',
                'message': f"CAIDA SEMANAL: {variation*100:.1f}% ({old:,.0f} -> {current:,.0f}€)",
                'triggered': True
            }
        return {'code': 'A2', 'triggered': False}
    
    def check_projection_floor(self, forecast_90d: float) -> Dict:
        """A4: Proyeccion a 90 dias < floor."""
        if forecast_90d < self.thresholds['projection_floor']:
            return {
                'code': 'A4',
                'severity': 'CRITICAL',
                'message': f"PROYECCION NEGATIVA: {forecast_90d:,.0f}€ a 90 dias (floor: {self.thresholds['projection_floor']:,.0f}€)",
                'triggered': True
            }
        return {'code': 'A4', 'triggered': False}
    
    def check_deviation_forecast(self, actual: float, forecast: float) -> Dict:
        """A3: Desviacion forecast > 10%."""
        if forecast == 0:
            return {'code': 'A3', 'triggered': False}
        
        deviation = abs(actual - forecast) / abs(forecast)
        
        if deviation > self.thresholds['max_deviation_forecast']:
            return {
                'code': 'A3',
                'severity': 'MEDIUM',
                'message': f"DESVIACION: {deviation*100:.1f}% (actual: {actual:,.0f}, forecast: {forecast:,.0f})",
                'triggered': True
            }
        return {'code': 'A3', 'triggered': False}
    
    def check_all(self, cash_data: pd.DataFrame, 
                  forecast_90d: float = None) -> List[Dict]:
        """Evalua todas las condiciones."""
        alerts = []
        
        current_balance = cash_data.iloc[-1]['cash_balance']
        
        alert = self.check_balance_threshold(current_balance)
        if alert['triggered']:
            alerts.append(alert)
        
        alert = self.check_variation_7d(cash_data)
        if alert['triggered']:
            alerts.append(alert)
        
        if forecast_90d is not None:
            alert = self.check_projection_floor(forecast_90d)
            if alert['triggered']:
                alerts.append(alert)
        
        if len(alerts) > 0:
            logger.warning(f"Alertas generadas: {len(alerts)}")
        else:
            logger.info("Sin alertas")
        
        return alerts


def check_alerts(cash_data: pd.DataFrame, 
                 forecast_90d: float = None) -> List[Dict]:
    """Funcion convenience."""
    checker = AlertChecker()
    return checker.check_all(cash_data, forecast_90d)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    logging.basicConfig(level=logging.INFO)
    
    cash_df = pd.read_csv('data/processed/cash_flow_daily.csv', parse_dates=['date'])
    alerts = check_alerts(cash_df, 30000)
    
    print(f"\nAlertas: {len(alerts)}")
    for a in alerts:
        print(f"  {a['code']}: {a.get('message', 'OK')}")