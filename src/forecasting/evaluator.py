"""
Evaluator - Calcula metricas de evaluacion del modelo.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import json


logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Evalua rendimiento del modelo de forecasting."""
    
    def __init__(self, models_path: str = "models"):
        self.models_path = Path(models_path)
    
    def calculate_mae(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calcula Mean Absolute Error."""
        return np.mean(np.abs(y_true - y_pred))
    
    def calculate_rmse(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calcula Root Mean Square Error."""
        return np.sqrt(np.mean((y_true - y_pred) ** 2))
    
    def calculate_mape(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calcula Mean Absolute Percentage Error."""
        mask = y_true != 0
        if mask.sum() == 0:
            return 0.0
        return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    
    def calculate_smape(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calcula Symmetric MAPE."""
        denominator = (np.abs(y_true) + np.abs(y_pred)) / 2
        mask = denominator != 0
        if mask.sum() == 0:
            return 0.0
        return np.mean(np.abs(y_true[mask] - y_pred[mask]) / denominator[mask]) * 100
    
    def evaluate_predictions(self, test_df: pd.DataFrame, 
                            forecast_df: pd.DataFrame) -> dict:
        """Evalua predicciones vs datos reales."""
        merged = test_df[['ds', 'y']].merge(
            forecast_df[['ds', 'yhat', 'yhat_lower', 'yhat_upper']],
            on='ds',
            how='inner'
        )
        
        if len(merged) == 0:
            logger.warning("No hay datos para evaluar")
            return {}
        
        y_true = merged['y'].values
        y_pred = merged['yhat'].values
        
        mae = self.calculate_mae(y_true, y_pred)
        rmse = self.calculate_rmse(y_true, y_pred)
        mape = self.calculate_mape(y_true, y_pred)
        smape = self.calculate_smape(y_true, y_pred)
        
        coverage = ((merged['y'] >= merged['yhat_lower']) & 
                   (merged['y'] <= merged['yhat_upper'])).mean() * 100
        
        results = {
            'mae': round(mae, 2),
            'rmse': round(rmse, 2),
            'mape': round(mape, 2),
            'smape': round(smape, 2),
            'coverage_95': round(coverage, 2),
            'n_evaluations': len(merged)
        }
        
        logger.info(f"MAE: {mae:.2f}, RMSE: {rmse:.2f}, MAPE: {mape:.2f}%")
        
        return results
    
    def compare_with_benchmark(self, test_df: pd.DataFrame) -> dict:
        """Compara con forecast naive (ultimo valor)."""
        y_true = test_df['y'].values[1:]
        y_naive = test_df['y'].values[:-1]
        
        mae_naive = self.calculate_mae(y_true, y_naive)
        rmse_naive = self.calculate_rmse(y_true, y_naive)
        mape_naive = self.calculate_mape(y_true, y_naive)
        
        return {
            'naive_mae': round(mae_naive, 2),
            'naive_rmse': round(rmse_naive, 2),
            'naive_mape': round(mape_naive, 2)
        }
    
    def generate_report(self, test_df: pd.DataFrame, 
                        forecast_df: pd.DataFrame) -> dict:
        """Genera reporte completo de evaluacion."""
        metrics = self.evaluate_predictions(test_df, forecast_df)
        
        if not metrics:
            return {}
        
        benchmark = self.compare_with_benchmark(test_df)
        
        improvement = {}
        if 'mae' in metrics:
            improvement['mae_improvement'] = round(
                (benchmark['naive_mae'] - metrics['mae']) / benchmark['naive_mae'] * 100, 2
            )
        if 'mape' in metrics:
            improvement['mape_improvement'] = round(
                (benchmark['naive_mape'] - metrics['mape']) / benchmark['naive_mape'] * 100, 2
            )
        
        report = {
            'model_metrics': metrics,
            'benchmark_metrics': benchmark,
            'improvement_vs_benchmark': improvement
        }
        
        return report
    
    def save_metrics(self, metrics: dict, 
                     filename: str = "model_metrics.json") -> Path:
        """Guarda metricas a JSON."""
        filepath = self.models_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Metricas guardadas: {filepath}")
        
        return filepath


def evaluate_model(models_path: str = "models", 
                  test_df: pd.DataFrame = None,
                  forecast_df: pd.DataFrame = None) -> dict:
    """Funcion convenience para evaluar modelo."""
    from src.forecasting.data_prep import prepare_forecasting_data
    
    evaluator = ModelEvaluator(models_path)
    
    if test_df is None or forecast_df is None:
        data = prepare_forecasting_data()
        test_df = data['test']
        
        from src.forecasting.predictor import CashFlowPredictor
        predictor = CashFlowPredictor(models_path)
        predictor.load_model()
        predictor.predict()
        forecast_df = predictor.forecast
    
    report = evaluator.generate_report(test_df, forecast_df)
    
    evaluator.save_metrics(report)
    
    return report


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    logging.basicConfig(level=logging.INFO)
    
    report = evaluate_model()
    
    if report:
        print("\n=== REPORTE DE EVALUACION ===")
        print(f"\nMetricas del modelo:")
        for k, v in report.get('model_metrics', {}).items():
            print(f"  {k}: {v}")
        
        print(f"\nBenchmark (Naive):")
        for k, v in report.get('benchmark_metrics', {}).items():
            print(f"  {k}: {v}")
        
        print(f"\nMejora vs Benchmark:")
        for k, v in report.get('improvement_vs_benchmark', {}).items():
            print(f"  {k}: {v}%")