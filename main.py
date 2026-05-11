"""
Cash Flow Forecasting System - Main Pipeline
==============================================

Sistema de forecasting financiero con alertas Telegram.
Empresa simulada: Industrial Metálica Portillo S.L.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import os
import json

# Configurar path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / 'logs' / f'pipeline_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CashFlowPipeline:
    """Pipeline principal del sistema de forecasting."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.results = {}
        
        # Crear carpetas necesarias
        self._setup_directories()
    
    def _setup_directories(self):
        """Crea estructura de directorios."""
        dirs = ['data/raw', 'data/processed', 'data/synthetic', 
                'models', 'logs', 'powerbi']
        for d in dirs:
            (PROJECT_ROOT / d).mkdir(parents=True, exist_ok=True)
    
    def run(self):
        """Ejecuta el pipeline completo."""
        logger.info("=" * 60)
        logger.info("CASH FLOW FORECASTING PIPELINE")
        logger.info("=" * 60)
        
        try:
            # Fase 0: Generación de datos sintéticos
            self._phase_0_generation()
            
            # Fases 1-2: ETL
            self._phase_1_2_etl()
            
            # Fase 3: Forecasting
            self._phase_3_forecasting()
            
            # Fase 4: Métricas y KPIs
            self._phase_4_metrics()
            
            # Fase 5: Power BI
            self._phase_5_powerbi()
            
            # Fase 6: Alertas Telegram
            self._phase_6_alerts()
            
            # Fase 7: Base de datos
            self._phase_7_database()
            
            self._print_summary()
            
        except Exception as e:
            logger.error(f"Error en pipeline: {e}")
            raise
        finally:
            elapsed = datetime.now() - self.start_time
            logger.info(f"Tiempo total: {elapsed}")
    
    def _phase_0_generation(self):
        """Fase 0: Generación de datos sintéticos."""
        logger.info("\n[FASE 0] Generando datos sintéticos...")
        
        from src.generators.main_generator import DataGenerator
        
        generator = DataGenerator()
        generator.generate_all()
        
        self.results['phase_0'] = {'status': 'OK', 'records': 3107}
        logger.info("Fase 0 completada")
    
    def _phase_1_2_etl(self):
        """Fases 1-2: Pipeline ETL."""
        logger.info("\n[FASE 1-2] Ejecutando ETL...")
        
        from src.etl.extractor import DataExtractor
        from src.etl.transformer import DataTransformer
        from src.etl.validator import CoherenceValidator
        
        # Extracción
        extractor = DataExtractor("data/raw")
        datasets = extractor.load_all()
        
        # Transformación
        transformer = DataTransformer()
        transformed = transformer.transform_all(datasets)
        transformer.save_processed(transformed)
        
        # Validación
        validator = CoherenceValidator()
        results = validator.validate_all_rules(transformed)
        
        self.results['phase_1_2'] = {
            'status': 'OK',
            'validation': results.get('_summary', {}).get('overall_status', 'N/A')
        }
        logger.info(f"Fase 1-2: Validación {results.get('_summary', {}).get('overall_status', 'N/A')}")
    
    def _phase_3_forecasting(self):
        """Fase 3: Forecasting con Prophet."""
        logger.info("\n[FASE 3] Entrenando modelo Prophet...")
        
        from src.forecasting.data_prep import prepare_forecasting_data
        from src.forecasting.trainer import train_prophet_model
        from src.forecasting.predictor import generate_forecast
        
        # Preparar datos
        data = prepare_forecasting_data()
        
        # Entrenar modelo
        model = train_prophet_model(data['train'])
        
        # Generar predicción
        result = generate_forecast()
        
        self.results['phase_3'] = {
            'status': 'OK',
            'forecast_90d': result['indicators'].get('min_forecast_balance', 0)
        }
        logger.info("Fase 3 completada")
    
    def _phase_4_metrics(self):
        """Fase 4: Métricas y KPIs."""
        logger.info("\n[FASE 4] Calculando métricas...")
        
        from src.forecasting.evaluator import evaluate_model
        from src.forecasting.data_prep import prepare_forecasting_data
        from src.forecasting.predictor import CashFlowPredictor
        
        data = prepare_forecasting_data()
        
        predictor = CashFlowPredictor()
        predictor.load_model()
        predictor.predict()
        
        report = evaluate_model(test_df=data['test'], forecast_df=predictor.forecast)
        
        self.results['phase_4'] = {
            'status': 'OK',
            'mape': report.get('model_metrics', {}).get('mape', 0),
            'mae': report.get('model_metrics', {}).get('mae', 0),
            'rmse': report.get('model_metrics', {}).get('rmse', 0)
        }
        
        logger.info(f"MAPE: {self.results['phase_4']['mape']:.2f}%")
        logger.info(f"MAE: {self.results['phase_4']['mae']:,.2f}€")
        logger.info(f"RMSE: {self.results['phase_4']['rmse']:,.2f}€")
    
    def _phase_5_powerbi(self):
        """Fase 5: Exportar a Power BI."""
        logger.info("\n[FASE 5] Exportando a Power BI...")
        
        import pandas as pd
        
        # Cargar datos
        cash_flow = pd.read_csv('data/processed/cash_flow_daily.csv', parse_dates=['date'])
        forecast = pd.read_csv('models/forecast_results.csv', parse_dates=['ds'])
        
        # Preparar KPIs
        today = cash_flow['date'].max()
        current_balance = cash_flow[cash_flow['date'] == today]['cash_balance'].values[0]
        inflow_30d = cash_flow[cash_flow['date'] >= today - pd.Timedelta(days=30)]['cash_inflow'].sum()
        outflow_30d = cash_flow[cash_flow['date'] >= today - pd.Timedelta(days=30)]['cash_outflow'].sum()
        
        target_date = today + pd.Timedelta(days=90)
        closest_idx = (forecast['ds'] - target_date).abs().idxmin()
        forecast_90d = forecast.loc[closest_idx, 'yhat']
        
        kpis = pd.DataFrame([{
            'report_date': today.strftime('%Y-%m-%d'),
            'current_cash_balance': round(current_balance, 2),
            'cash_inflow_30d': round(inflow_30d, 2),
            'cash_outflow_30d': round(outflow_30d, 2),
            'forecast_90d': round(forecast_90d, 2),
            'liquidity_risk': 'ALTO' if forecast_90d < 25000 else 'MEDIO' if forecast_90d < 50000 else 'BAJO'
        }])
        
        # Guardar en powerbi/
        powerbi_path = PROJECT_ROOT / 'powerbi'
        cash_flow.to_csv(powerbi_path / 'cash_flow_daily.csv', index=False)
        forecast.to_csv(powerbi_path / 'forecast_results.csv', index=False)
        kpis.to_csv(powerbi_path / 'kpis.csv', index=False)
        
        self.results['phase_5'] = {'status': 'OK', 'files': 3}
        logger.info("Fase 5 completada - 3 archivos exportados")
    
    def _phase_6_alerts(self):
        """Fase 6: Verificar y enviar alertas."""
        logger.info("\n[FASE 6] Verificando alertas...")
        
        import pandas as pd
        from src.alerts.checker import check_alerts
        from src.alerts.notifier import send_alerts
        
        # Cargar datos
        cash_df = pd.read_csv('data/processed/cash_flow_daily.csv', parse_dates=['date'])
        
        # Cargar forecast
        forecast_df = pd.read_csv('models/forecast_results.csv')
        forecast_90d = forecast_df.iloc[-90:]['yhat'].iloc[-1]
        
        # Verificar alertas
        alerts = check_alerts(cash_df, forecast_90d)
        
        if alerts:
            send_alerts(alerts)
            self.results['phase_6'] = {'status': 'ALERTAS', 'count': len(alerts)}
        else:
            self.results['phase_6'] = {'status': 'OK', 'count': 0}
        
        logger.info(f"Alertas generadas: {len(alerts)}")
    
    def _phase_7_database(self):
        """Fase 7: Cargar a SQLite."""
        logger.info("\n[FASE 7] Actualizando base de datos...")
        
        from src.database.db_manager import DatabaseManager
        
        db = DatabaseManager()
        db.create_tables()
        db.load_all_csv()
        
        self.results['phase_7'] = {'status': 'OK'}
        logger.info("Base de datos actualizada")
    
    def _print_summary(self):
        """Imprime resumen del pipeline."""
        logger.info("\n" + "=" * 60)
        logger.info("RESUMEN DEL PIPELINE")
        logger.info("=" * 60)
        
        for phase, result in self.results.items():
            status = result.get('status', 'N/A')
            logger.info(f"{phase}: {status}")
        
        logger.info("=" * 60)
        logger.info("Pipeline completado exitosamente!")


def main():
    """Punto de entrada."""
    pipeline = CashFlowPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()