"""
Technical Indicators Module
Calculates RSI, MACD, Bollinger Bands, and EMA for trading signals
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """Technical analysis indicators for market analysis"""
    
    @staticmethod
    def rsi(data, period=14):
        """
        Calculate Relative Strength Index (RSI)
        RSI > 70: Overbought (potential sell signal)
        RSI < 30: Oversold (potential buy signal)
        """
        try:
            closes = pd.Series([float(candle[4]) for candle in data])
            
            delta = closes.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi.iloc[-1])
        except Exception as e:
            logger.error(f"❌ Error calculating RSI: {e}")
            return None
    
    @staticmethod
    def macd(data, fast=12, slow=26, signal=9):
        """
        Calculate MACD (Moving Average Convergence Divergence)
        """
        try:
            closes = pd.Series([float(candle[4]) for candle in data])
            
            ema_fast = closes.ewm(span=fast).mean()
            ema_slow = closes.ewm(span=slow).mean()
            
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            return {
                'macd': float(macd_line.iloc[-1]),
                'signal': float(signal_line.iloc[-1]),
                'histogram': float(histogram.iloc[-1])
            }
        except Exception as e:
            logger.error(f"❌ Error calculating MACD: {e}")
            return None
    
    @staticmethod
    def bollinger_bands(data, period=20, std_dev=2):
        """
        Calculate Bollinger Bands
        """
        try:
            closes = pd.Series([float(candle[4]) for candle in data])
            
            sma = closes.rolling(window=period).mean()
            std = closes.rolling(window=period).std()
            
            upper_band = sma + (std_dev * std)
            lower_band = sma - (std_dev * std)
            
            return {
                'upper': float(upper_band.iloc[-1]),
                'middle': float(sma.iloc[-1]),
                'lower': float(lower_band.iloc[-1]),
                'current_price': float(closes.iloc[-1])
            }
        except Exception as e:
            logger.error(f"❌ Error calculating Bollinger Bands: {e}")
            return None
    
    @staticmethod
    def ema(data, period=20):
        """Calculate Exponential Moving Average (EMA)"""
        try:
            closes = pd.Series([float(candle[4]) for candle in data])
            ema_value = closes.ewm(span=period).mean()
            
            return float(ema_value.iloc[-1])
        except Exception as e:
            logger.error(f"❌ Error calculating EMA: {e}")
            return None
    
    @staticmethod
    def sma(data, period=50):
        """Calculate Simple Moving Average (SMA)"""
        try:
            closes = pd.Series([float(candle[4]) for candle in data])
            sma_value = closes.rolling(window=period).mean()
            
            return float(sma_value.iloc[-1])
        except Exception as e:
            logger.error(f"❌ Error calculating SMA: {e}")
            return None
    
    @staticmethod
    def analyze_market(data, config):
        """
        Comprehensive market analysis using multiple indicators
        Returns: 'BUY', 'SELL', or 'HOLD'
        """
        try:
            rsi = TechnicalIndicators.rsi(data, config.RSI_PERIOD)
            macd = TechnicalIndicators.macd(data, config.MACD_FAST, config.MACD_SLOW, config.MACD_SIGNAL)
            bb = TechnicalIndicators.bollinger_bands(data, config.BB_PERIOD, config.BB_STD)
            ema = TechnicalIndicators.ema(data, 20)
            
            if not all([rsi, macd, bb, ema]):
                return 'HOLD'
            
            buy_signals = 0
            sell_signals = 0
            
            # RSI signals
            if rsi < config.RSI_OVERSOLD:
                buy_signals += 2
            elif rsi > config.RSI_OVERBOUGHT:
                sell_signals += 2
            
            # MACD signals
            if macd['histogram'] > 0 and macd['macd'] > macd['signal']:
                buy_signals += 2
            elif macd['histogram'] < 0 and macd['macd'] < macd['signal']:
                sell_signals += 2
            
            # Bollinger Bands signals
            current_price = bb['current_price']
            if current_price < bb['lower']:
                buy_signals += 1
            elif current_price > bb['upper']:
                sell_signals += 1
            
            # EMA signals
            if current_price > ema:
                buy_signals += 1
            else:
                sell_signals += 1
            
            logger.debug(f"📊 Analysis - Buy: {buy_signals}, Sell: {sell_signals}, RSI: {rsi:.2f}, MACD Hist: {macd['histogram']:.6f}")
            
            if buy_signals > sell_signals + 1:
                return 'BUY'
            elif sell_signals > buy_signals + 1:
                return 'SELL'
            else:
                return 'HOLD'
        
        except Exception as e:
            logger.error(f"❌ Error in market analysis: {e}")
            return 'HOLD'