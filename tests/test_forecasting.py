"""
Tests para módulo de forecasting.
"""

import pytest
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDataPrep:
    """Tests para preparación de datos."""
    
    def test_prepare_prophet_df(self):
        """Test preparación dataframe Prophet."""
        from src.forecasting.data_prep import DataPreparator
        
        if not Path('data/processed/cash_flow_daily.csv').exists():
            pytest.skip("Datos procesados no disponibles")
        
        preparator = DataPreparator()
        cash_flow = preparator.load_cash_flow()
        
        prophet_df = preparator.prepare_prophet_df(cash_flow)
        
        assert 'ds' in prophet_df.columns
        assert 'y' in prophet_df.columns
        assert len(prophet_df) > 0
    
    def test_train_test_split(self):
        """Test división train/test."""
        from src.forecasting.data_prep import DataPreparator
        
        if not Path('data/processed/cash_flow_daily.csv').exists():
            pytest.skip("Datos procesados no disponibles")
        
        preparator = DataPreparator()
        data = preparator.prepare_all()
        
        assert 'train' in data
        assert 'test' in data
        assert len(data['train']) > len(data['test'])


class TestTrainer:
    """Tests para trainer de Prophet."""
    
    def test_model_training(self):
        """Test entrenamiento del modelo."""
        from src.forecasting.data_prep import prepare_forecasting_data
        
        if not Path('data/processed/cash_flow_daily.csv').exists():
            pytest.skip("Datos procesados no disponibles")
        
        data = prepare_forecasting_data()
        
        from src.forecasting.trainer import ProphetTrainer
        
        trainer = ProphetTrainer()
        model = trainer.train(data['train'])
        
        assert model is not None


class TestPredictor:
    """Tests para predictor."""
    
    def test_prediction_generation(self):
        """Test generación de predicciones."""
        from src.forecasting.predictor import CashFlowPredictor
        
        if not Path('models/prophet_cashflow_model.json').exists():
            pytest.skip("Modelo no disponible")
        
        predictor = CashFlowPredictor()
        loaded = predictor.load_model()
        
        assert loaded == True
        
        forecast = predictor.predict(periods=30)
        
        assert forecast is not None
        assert len(forecast) > 0
    
    def test_risk_indicators(self):
        """Test cálculo de indicadores de riesgo."""
        from src.forecasting.predictor import CashFlowPredictor
        
        if not Path('models/prophet_cashflow_model.json').exists():
            pytest.skip("Modelo no disponible")
        
        predictor = CashFlowPredictor()
        predictor.load_model()
        predictor.predict(90)
        
        indicators = predictor.get_risk_indicators()
        
        assert 'min_forecast_balance' in indicators
        assert 'risk_level' in indicators


class TestEvaluator:
    """Tests para evaluador."""
    
    def test_metrics_calculation(self):
        """Test cálculo de métricas."""
        from src.forecasting.evaluator import ModelEvaluator
        import numpy as np
        
        evaluator = ModelEvaluator()
        
        y_true = np.array([100, 110, 120, 130])
        y_pred = np.array([105, 108, 125, 128])
        
        mae = evaluator.calculate_mae(y_true, y_pred)
        rmse = evaluator.calculate_rmse(y_true, y_pred)
        
        assert mae > 0
        assert rmse > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])