"""
Pipeline completo de ejecución.
Orquestador de todas las fases del proyecto.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import logging
import yaml

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config():
    """Carga configuración general."""
    with open('config/generation_params.yaml', 'r') as f:
        return yaml.safe_load(f)


def run_phase_0():
    """Fase 0: Generación de datos sintéticos."""
    logger.info("=" * 50)
    logger.info("FASE 0: Generando datos sintéticos")
    logger.info("=" * 50)
    
    from src.generators.main_generator import DataGenerator
    
    generator = DataGenerator()
    generator.generate_all()
    
    logger.info("Fase 0 completada")


def run_phase_1_2():
    """Fases 1-2: ETL y transformación."""
    logger.info("=" * 50)
    logger.info("FASE 1-2: ETL y transformación")
    logger.info("=" * 50)
    
    from src.etl.extractor import DataExtractor
    from src.etl.transformer import DataTransformer
    from src.etl.validator import CoherenceValidator
    
    extractor = DataExtractor()
    datasets = extractor.load_all()
    
    transformer = DataTransformer()
    transformed = transformer.transform_all(datasets)
    transformer.save_processed(transformed)
    
    validator = CoherenceValidator()
    results = validator.validate_all_rules(transformed)
    print(validator.generate_validation_report(results))
    
    logger.info("Fase 1-2 completada")


def run_phase_3():
    """Fase 3: Forecasting con Prophet."""
    logger.info("=" * 50)
    logger.info("FASE 3: Forecasting")
    logger.info("=" * 50)
    
    from src.forecasting.data_prep import prepare_forecasting_data
    from src.forecasting.trainer import train_prophet_model
    from src.forecasting.predictor import generate_forecast
    from src.forecasting.evaluator import ModelEvaluator
    
    logger.info("Preparando datos...")
    data = prepare_forecasting_data()
    
    logger.info("Entrenando modelo...")
    model = train_prophet_model(data['train'])
    
    logger.info("Generando forecast...")
    result = generate_forecast()
    
    logger.info("Evaluando modelo...")
    from src.forecasting.predictor import CashFlowPredictor
    predictor = CashFlowPredictor()
    predictor.load_model()
    predictor.predict()
    
    evaluator = ModelEvaluator()
    report = evaluator.generate_report(data['test'], predictor.forecast)
    evaluator.save_metrics(report)
    
    logger.info(f"MAPE: {report.get('model_metrics', {}).get('mape', 'N/A')}%")
    
    logger.info("Fase 3 completada")


def run_phase_5():
    """Fase 5: Sistema de alertas."""
    logger.info("=" * 50)
    logger.info("FASE 5: Verificando alertas")
    logger.info("=" * 50)
    
    import pandas as pd
    from src.alerts.checker import check_alerts
    from src.alerts.notifier import send_alerts
    
    cash_df = pd.read_csv('data/processed/cash_flow_daily.csv', parse_dates=['date'])
    
    forecast_df = pd.read_csv('models/forecast_results.csv')
    forecast_90d = forecast_df.iloc[-90:]['yhat'].iloc[-1]
    
    alerts = check_alerts(cash_df, forecast_90d)
    
    if alerts:
        send_alerts(alerts)
    else:
        logger.info("Sin alertas activas")
    
    logger.info("Fase 5 completada")


def run_full_pipeline():
    """Ejecuta pipeline completo."""
    logger.info("INICIANDO PIPELINE COMPLETO")
    logger.info("=" * 60)
    
    run_phase_0()
    run_phase_1_2()
    run_phase_3()
    run_phase_5()
    
    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETADO")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_full_pipeline()