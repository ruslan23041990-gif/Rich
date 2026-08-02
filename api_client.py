"""
Bybit API Client Module
Handles all API interactions with Bybit exchange
"""

import logging
import time
from pybit.unified_trading import HTTP
import config

logger = logging.getLogger(__name__)

class BybitClient:
    """Bybit API Client for trading operations"""
    
    def __init__(self):
        """Initialize Bybit API client"""
        try:
            self.client = HTTP(
                testnet=config.BYBIT_TESTNET,
                api_key=config.BYBIT_API_KEY,
                api_secret=config.BYBIT_API_SECRET
            )
            logger.info("✅ Bybit API client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Bybit API: {e}")
            raise
    
    def get_account_balance(self):
        """Get current account balance"""
        try:
            response = self.client.get_wallet_balance(accountType="UNIFIED")
            balance = response['result']['list'][0]['totalEquity']
            logger.info(f"📊 Account balance: ${balance} USDT")
            return float(balance)
        except Exception as e:
            logger.error(f"❌ Error getting balance: {e}")
            return None
    
    def get_market_data(self, symbol, interval, limit=100):
        """Get historical OHLCV data for technical analysis"""
        try:
            response = self.client.get_kline(
                category="linear",
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            if response['retCode'] == 0:
                candles = response['result']['list']
                candles.reverse()
                logger.debug(f"📈 Fetched {len(candles)} candles for {symbol}")
                return candles
            else:
                logger.error(f"❌ API Error: {response['retMsg']}")
                return None
        except Exception as e:
            logger.error(f"❌ Error fetching market data: {e}")
            return None
    
    def get_current_price(self, symbol):
        """Get current market price"""
        try:
            response = self.client.get_tickers(
                category="linear",
                symbol=symbol
            )
            
            if response['retCode'] == 0:
                price = float(response['result']['list'][0]['lastPrice'])
                logger.debug(f"💰 {symbol} current price: ${price}")
                return price
            else:
                logger.error(f"❌ API Error: {response['retMsg']}")
                return None
        except Exception as e:
            logger.error(f"❌ Error getting current price: {e}")
            return None
    
    def open_long_position(self, symbol, size, leverage):
        """Open a long position (BUY)"""
        try:
            response = self.client.place_order(
                category="linear",
                symbol=symbol,
                side="Buy",
                orderType="Market",
                qty=str(size),
                leverage=str(leverage)
            )
            
            if response['retCode'] == 0:
                order_id = response['result']['orderId']
                logger.info(f"✅ Long position opened: {symbol} | Size: {size} | Order ID: {order_id}")
                return order_id
            else:
                logger.error(f"❌ Failed to open long: {response['retMsg']}")
                return None
        except Exception as e:
            logger.error(f"❌ Error opening long position: {e}")
            return None
    
    def open_short_position(self, symbol, size, leverage):
        """Open a short position (SELL)"""
        try:
            response = self.client.place_order(
                category="linear",
                symbol=symbol,
                side="Sell",
                orderType="Market",
                qty=str(size),
                leverage=str(leverage)
            )
            
            if response['retCode'] == 0:
                order_id = response['result']['orderId']
                logger.info(f"✅ Short position opened: {symbol} | Size: {size} | Order ID: {order_id}")
                return order_id
            else:
                logger.error(f"❌ Failed to open short: {response['retMsg']}")
                return None
        except Exception as e:
            logger.error(f"❌ Error opening short position: {e}")
            return None
    
    def close_position(self, symbol):
        """Close an open position"""
        try:
            position = self.get_position(symbol)
            if not position or float(position['size']) == 0:
                logger.warning(f"⚠️ No open position for {symbol}")
                return None
            
            size = float(position['size'])
            side = "Sell" if position['side'] == "Buy" else "Buy"
            
            response = self.client.place_order(
                category="linear",
                symbol=symbol,
                side=side,
                orderType="Market",
                qty=str(size)
            )
            
            if response['retCode'] == 0:
                order_id = response['result']['orderId']
                logger.info(f"✅ Position closed: {symbol} | Order ID: {order_id}")
                return order_id
            else:
                logger.error(f"❌ Failed to close position: {response['retMsg']}")
                return None
        except Exception as e:
            logger.error(f"❌ Error closing position: {e}")
            return None
    
    def get_position(self, symbol):
        """Get current position details"""
        try:
            response = self.client.get_positions(
                category="linear",
                symbol=symbol
            )
            
            if response['retCode'] == 0 and response['result']['list']:
                position = response['result']['list'][0]
                return position
            return None
        except Exception as e:
            logger.error(f"❌ Error getting position: {e}")
            return None
    
    def set_leverage(self, symbol, leverage):
        """Set leverage for trading pair"""
        try:
            response = self.client.set_leverage(
                category="linear",
                symbol=symbol,
                buyLeverage=str(leverage),
                sellLeverage=str(leverage)
            )
            
            if response['retCode'] == 0:
                logger.info(f"✅ Leverage set to {leverage}x for {symbol}")
                return True
            else:
                logger.error(f"❌ Failed to set leverage: {response['retMsg']}")
                return False
        except Exception as e:
            logger.error(f"❌ Error setting leverage: {e}")
            return False
    
    def get_all_positions(self):
        """Get all open positions"""
        try:
            response = self.client.get_positions(category="linear")
            
            if response['retCode'] == 0:
                positions = [p for p in response['result']['list'] if float(p['size']) > 0]
                logger.debug(f"📍 Found {len(positions)} open positions")
                return positions
            return []
        except Exception as e:
            logger.error(f"❌ Error getting positions: {e}")
            return []
    
    def place_stop_loss(self, symbol, side, price):
        """Place stop loss order"""
        try:
            position = self.get_position(symbol)
            if not position:
                logger.warning(f"⚠️ No position found for {symbol}")
                return None
            
            size = float(position['size'])
            opposite_side = "Sell" if side == "Buy" else "Buy"
            
            response = self.client.place_order(
                category="linear",
                symbol=symbol,
                side=opposite_side,
                orderType="Limit",
                qty=str(size),
                price=str(price),
                stopLoss=str(price),
                slTriggerBy="LastPrice",
                reduceOnly=True
            )
            
            if response['retCode'] == 0:
                logger.info(f"✅ Stop loss set at ${price} for {symbol}")
                return response['result']['orderId']
            else:
                logger.error(f"❌ Failed to set stop loss: {response['retMsg']}")
                return None
        except Exception as e:
            logger.error(f"❌ Error placing stop loss: {e}")
            return None

try:
    bybit_client = BybitClient()
except Exception as e:
    logger.error(f"❌ Failed to initialize Bybit client: {e}")
    bybit_client = None