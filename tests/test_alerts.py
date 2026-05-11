"""
Tests para sistema de alertas.
"""

import pytest
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAlertChecker:
    """Tests para checker de alertas."""
    
    @pytest.fixture
    def checker(self):
        """Crea checker."""
        from src.alerts.checker import AlertChecker
        return AlertChecker()
    
    def test_balance_threshold_alert(self, checker):
        """Test alerta de balance bajo."""
        result = checker.check_balance_threshold(30000)
        
        assert result['triggered'] == True
        assert result['severity'] == 'CRITICAL'
    
    def test_balance_ok(self, checker):
        """Test balance OK."""
        result = checker.check_balance_threshold(100000)
        
        assert result['triggered'] == False
    
    def test_projection_floor_alert(self, checker):
        """Test alerta de proyección bajo."""
        result = checker.check_projection_floor(20000)
        
        assert result['triggered'] == True
        assert result['severity'] == 'CRITICAL'
    
    def test_projection_ok(self, checker):
        """Test proyección OK."""
        result = checker.check_projection_floor(100000)
        
        assert result['triggered'] == False


class TestAlertNotifier:
    """Tests para notificador."""
    
    @pytest.fixture
    def notifier(self):
        """Crea notificador."""
        from src.alerts.notifier import AlertNotifier
        return AlertNotifier()
    
    def test_format_message_empty(self, notifier):
        """Test formato sin alertas."""
        message = notifier.format_message([])
        
        assert "No hay alertas" in message
    
    def test_format_message_with_alerts(self, notifier):
        """Test formato con alertas."""
        alerts = [
            {'code': 'A1', 'severity': 'CRITICAL', 'message': 'Test alert'}
        ]
        
        message = notifier.format_message(alerts)
        
        assert 'CRITICAL' in message
        assert 'A1' in message
    
    def test_notify_disabled(self, notifier):
        """Test notificaciones deshabilitadas."""
        # No debe fallar aunque Telegram esté deshabilitado
        result = notifier.notify([])
        
        assert result == True


class TestIntegration:
    """Tests de integración."""
    
    def test_full_alert_flow(self):
        """Test flujo completo de alertas."""
        if not Path('data/processed/cash_flow_daily.csv').exists():
            pytest.skip("Datos no disponibles")
        
        from src.alerts.checker import check_alerts
        
        cash_df = pd.read_csv('data/processed/cash_flow_daily.csv', parse_dates=['date'])
        
        alerts = check_alerts(cash_df, forecast_90d=30000)
        
        # No debe fallar
        assert isinstance(alerts, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])