"""
Telegram Bot - Bot de alertas para Cash Flow.
"""

import logging
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class CashFlowBot:
    """Bot de Telegram para alertas de cash flow."""
    
    def __init__(self, config_path: str = "config/alerts.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.telegram_config = self.config.get('telegram', {})
        self.alerts_enabled = self.config.get('alerts', {}).get('enabled', True)
    
    def setup_commands(self):
        """Configura comandos del bot."""
        commands = [
            ('start', 'Iniciar bot'),
            ('status', 'Ver estado actual de tesoreria'),
            ('forecast', 'Ver prediccion a 90 dias'),
            ('alerts', 'Ver alertas activas'),
            ('help', 'Mostrar ayuda')
        ]
        return commands
    
    def get_status_message(self, cash_data) -> str:
        """Obtiene mensaje de estado."""
        current = cash_data.iloc[-1]
        
        msg = "=== ESTADO ACTUAL DE TESORERIA ===\n\n"
        msg += f"Saldo actual: {current['cash_balance']:,.2f}€\n"
        msg += f"Ingresos 30d: {current.get('cash_inflow', 0):,.2f}€\n"
        msg += f"Gastos 30d: {current.get('cash_outflow', 0):,.2f}€\n"
        
        return msg
    
    def run(self):
        """Ejecuta el bot (placeholder para desarrollo)."""
        if not self.telegram_config.get('enabled', False):
            logger.info("Bot deshabilitado. Para habilitar, configura config/alerts.yaml")
            return
        
        logger.info("Iniciando bot de Telegram...")
        logger.info("Comandos disponibles: /start, /status, /forecast, /alerts, /help")


def main():
    """Punto de entrada."""
    logging.basicConfig(level=logging.INFO)
    
    bot = CashFlowBot()
    bot.run()


if __name__ == "__main__":
    main()