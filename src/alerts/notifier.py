"""
Notifier - Formatea y envia notificaciones.
"""

import logging
from datetime import datetime
from typing import List, Dict
import yaml

logger = logging.getLogger(__name__)


class AlertNotifier:
    """Formatea y envia alertas."""
    
    def __init__(self, config_path: str = "config/alerts.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.telegram_config = self.config.get('telegram', {})
    
    def format_message(self, alerts: List[Dict]) -> str:
        """Formatea mensaje de alertas."""
        if not alerts:
            return "No hay alertas activas. Sistema OK."
        
        lines = []
        lines.append("=" * 50)
        lines.append("ALERTA DE TESORERIA - Industrial Metálica Portillo")
        lines.append("=" * 50)
        lines.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        critical = [a for a in alerts if a.get('severity') == 'CRITICAL']
        high = [a for a in alerts if a.get('severity') == 'HIGH']
        medium = [a for a in alerts if a.get('severity') == 'MEDIUM']
        
        if critical:
            lines.append("CRITICAL:")
            for a in critical:
                lines.append(f"  [{a['code']}] {a['message']}")
            lines.append("")
        
        if high:
            lines.append("HIGH:")
            for a in high:
                lines.append(f"  [{a['code']}] {a['message']}")
            lines.append("")
        
        if medium:
            lines.append("MEDIUM:")
            for a in medium:
                lines.append(f"  [{a['code']}] {a['message']}")
            lines.append("")
        
        lines.append("=" * 50)
        
        return "\n".join(lines)
    
    async def send_telegram_async(self, message: str) -> bool:
        """Envía notificación por Telegram de forma asíncrona."""
        if not self.telegram_config.get('enabled', False):
            logger.info("Telegram deshabilitado, mostrando mensaje:")
            print(message)
            return True
        
        try:
            from telegram import Bot
            from telegram.error import TelegramError
            
            token = self.telegram_config.get('bot_token')
            chat_id = self.telegram_config.get('admin_chat_id')
            
            if not token or token == "YOUR_BOT_TOKEN_HERE":
                logger.warning("Token de Telegram no configurado")
                return False
            
            bot = Bot(token=token)
            await bot.send_message(chat_id=chat_id, text=message)
            
            logger.info("Notificacion enviada por Telegram")
            return True
            
        except ImportError:
            logger.warning("python-telegram-bot no instalado")
            print(message)
            return True
        except Exception as e:
            logger.error(f"Error enviando Telegram: {e}")
            return False
    
    def send_telegram(self, message: str) -> bool:
        """Envía notificación por Telegram (sync wrapper)."""
        try:
            import asyncio
            return asyncio.run(self.send_telegram_async(message))
        except Exception as e:
            logger.error(f"Error en send_telegram: {e}")
            return False
            return False
    
    def notify(self, alerts: List[Dict]) -> bool:
        """Procesa y envia notificaciones."""
        message = self.format_message(alerts)
        
        return self.send_telegram(message)


def send_alerts(alerts: List[Dict]) -> bool:
    """Funcion convenience."""
    notifier = AlertNotifier()
    return notifier.notify(alerts)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    test_alerts = [
        {'code': 'A1', 'severity': 'CRITICAL', 'message': 'CASH BAJO: 45,000€ (min: 50,000€)'},
        {'code': 'A4', 'severity': 'CRITICAL', 'message': 'PROYECCION NEGATIVA: 20,000€ a 90 dias'}
    ]
    
    send_alerts(test_alerts)