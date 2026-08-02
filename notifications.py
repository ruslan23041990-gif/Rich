"""
Notifications Module
Sends trading alerts via Telegram
"""

import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class Notifier:
    """Handles notifications for trading events"""
    
    def __init__(self, config):
        """Initialize notifier"""
        self.config = config
        self.enabled = config.SEND_NOTIFICATIONS and config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID
        
        if self.enabled:
            logger.info("✅ Telegram notifications enabled")
        else:
            logger.info("ℹ️ Telegram notifications disabled")
    
    def send_message(self, message):
        """Send message via Telegram"""
        if not self.enabled:
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.config.TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {
                'chat_id': self.config.TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                logger.debug("✅ Notification sent")
            else:
                logger.warning(f"⚠️ Failed to send notification: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error sending notification: {e}")
    
    def notify_trade_opened(self, symbol, side, entry_price, size, stop_loss, take_profit):
        """Notify when trade is opened"""
        message = f"""
🚀 <b>TRADE OPENED</b>
Symbol: <b>{symbol}</b>
Side: <b>{side}</b>
Entry Price: <b>${entry_price:.2f}</b>
Size: <b>{size:.4f}</b>
Stop Loss: <b>${stop_loss:.2f}</b>
Take Profit: <b>${take_profit:.2f}</b>
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        self.send_message(message)
    
    def notify_trade_closed(self, symbol, side, entry_price, exit_price, pnl, pnl_percent):
        """Notify when trade is closed"""
        emoji = "✅" if pnl >= 0 else "❌"
        message = f"""
{emoji} <b>TRADE CLOSED</b>
Symbol: <b>{symbol}</b>
Side: <b>{side}</b>
Entry Price: <b>${entry_price:.2f}</b>
Exit Price: <b>${exit_price:.2f}</b>
P/L: <b>${pnl:.2f} ({pnl_percent:.2f}%)</b>
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        self.send_message(message)
    
    def notify_stop_loss_hit(self, symbol, loss_amount):
        """Notify when stop loss is hit"""
        message = f"""
🛑 <b>STOP LOSS HIT</b>
Symbol: <b>{symbol}</b>
Loss: <b>${loss_amount:.2f}</b>
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        self.send_message(message)
    
    def notify_daily_limit_reached(self, daily_loss, max_daily_loss):
        """Notify when daily loss limit is reached"""
        message = f"""
⛔ <b>DAILY LOSS LIMIT REACHED</b>
Current Daily Loss: <b>${daily_loss:.2f}</b>
Max Daily Loss: <b>${max_daily_loss:.2f}</b>
Trading halted for today!
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        self.send_message(message)
    
    def notify_bot_started(self, symbol, balance):
        """Notify when bot starts"""
        message = f"""
🤖 <b>TRADING BOT STARTED</b>
Symbol: <b>{symbol}</b>
Account Balance: <b>${balance:.2f}</b>
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        self.send_message(message)
    
    def notify_bot_stopped(self, reason):
        """Notify when bot stops"""
        message = f"""
🛑 <b>TRADING BOT STOPPED</b>
Reason: <b>{reason}</b>
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        self.send_message(message)
    
    def notify_error(self, error_message):
        """Notify about errors"""
        message = f"""
⚠️ <b>BOT ERROR</b>
Error: <b>{error_message}</b>
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        self.send_message(message)
    
    def notify_daily_summary(self, trades_count, daily_pnl, daily_pnl_percent, balance):
        """Send daily trading summary"""
        emoji = "📈" if daily_pnl >= 0 else "📉"
        message = f"""
{emoji} <b>DAILY SUMMARY</b>
Total Trades: <b>{trades_count}</b>
Daily P/L: <b>${daily_pnl:.2f} ({daily_pnl_percent:.2f}%)</b>
Account Balance: <b>${balance:.2f}</b>
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        self.send_message(message)