"""
Configuration module for Bybit Trading Bot
Loads all settings from .env file
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bybit API Configuration
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')
BYBIT_TESTNET = os.getenv('BYBIT_TESTNET', 'False').lower() == 'true'

# Trading Configuration
TRADING_PAIR = os.getenv('TRADING_PAIR', 'BTCUSDT')
LEVERAGE = int(os.getenv('LEVERAGE', '5'))
POSITION_SIZE = float(os.getenv('POSITION_SIZE', '100'))
MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', '3'))

# Risk Management
STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '2'))
TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', '4'))
MAX_DAILY_LOSS = float(os.getenv('MAX_DAILY_LOSS', '500'))

# Indicators Settings
RSI_PERIOD = int(os.getenv('RSI_PERIOD', '14'))
RSI_OVERBOUGHT = int(os.getenv('RSI_OVERBOUGHT', '70'))
RSI_OVERSOLD = int(os.getenv('RSI_OVERSOLD', '30'))

MACD_FAST = int(os.getenv('MACD_FAST', '12'))
MACD_SLOW = int(os.getenv('MACD_SLOW', '26'))
MACD_SIGNAL = int(os.getenv('MACD_SIGNAL', '9'))

BB_PERIOD = int(os.getenv('BB_PERIOD', '20'))
BB_STD = float(os.getenv('BB_STD', '2'))

# Telegram Notifications
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
SEND_NOTIFICATIONS = os.getenv('SEND_NOTIFICATIONS', 'False').lower() == 'true'

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'logs/trading_bot.log')

# Timeframes
TIMEFRAME = '5m'  # 5 minute candles for short-term trading
HISTORY_LIMIT = 100  # Number of candles to analyze

# API Settings
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3
RETRY_DELAY = 2

def validate_config():
    """Validate that all required config values are set"""
    if not BYBIT_API_KEY or not BYBIT_API_SECRET:
        raise ValueError("Bybit API credentials not configured in .env file")
    
    if POSITION_SIZE <= 0:
        raise ValueError("POSITION_SIZE must be greater than 0")
    
    if LEVERAGE < 1 or LEVERAGE > 100:
        raise ValueError("LEVERAGE must be between 1 and 100")
    
    print("✅ Configuration validated successfully!")

if __name__ == "__main__":
    validate_config()