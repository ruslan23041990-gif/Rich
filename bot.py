"""
Bybit Trading Bot - Main Entry Point
Automated trading bot for short-term scalping on Bybit exchange
"""

import logging
import logging.handlers
import time
import sys
import os
from datetime import datetime

# Import custom modules
try:
    import config
    from api_client import bybit_client
    from indicators import TechnicalIndicators
    from risk_manager import RiskManager
    from notifications import Notifier
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure all required files are in the same directory")
    sys.exit(1)

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

class BybitTradingBot:
    """Main Trading Bot Class"""
    
    def __init__(self):
        """Initialize the trading bot"""
        try:
            config.validate_config()
            
            self.api_client = bybit_client
            if not self.api_client:
                raise Exception("Failed to initialize Bybit API client")
            
            # Get initial balance
            initial_balance = self.api_client.get_account_balance()
            if not initial_balance:
                raise Exception("Failed to get account balance")
            
            self.initial_balance = initial_balance
            self.risk_manager = RiskManager(initial_balance, config)
            self.notifier = Notifier(config)
            
            # Trading state
            self.is_running = False
            self.trades_opened = 0
            self.trades_closed = 0
            self.total_pnl = 0
            self.current_position = None
            
            logger.info("="*60)
            logger.info("🤖 BYBIT TRADING BOT INITIALIZED")
            logger.info("="*60)
            logger.info(f"Initial Balance: ${initial_balance:.2f}")
            logger.info(f"Trading Pair: {config.TRADING_PAIR}")
            logger.info(f"Leverage: {config.LEVERAGE}x")
            logger.info(f"Position Size: {config.POSITION_SIZE}")
            logger.info(f"Stop Loss: {config.STOP_LOSS_PERCENT}%")
            logger.info(f"Take Profit: {config.TAKE_PROFIT_PERCENT}%")
            logger.info("="*60)
            
            self.notifier.notify_bot_started(config.TRADING_PAIR, initial_balance)
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize bot: {e}")
            raise
    
    def analyze_market(self):
        """Analyze market using technical indicators"""
        try:
            # Fetch market data
            market_data = self.api_client.get_market_data(
                config.TRADING_PAIR,
                config.TIMEFRAME,
                config.HISTORY_LIMIT
            )
            
            if not market_data or len(market_data) < 30:
                logger.warning("❌ Insufficient market data for analysis")
                return None
            
            # Analyze using technical indicators
            signal = TechnicalIndicators.analyze_market(market_data, config)
            
            return signal
        except Exception as e:
            logger.error(f"❌ Error analyzing market: {e}")
            return None
    
    def check_take_profit_stop_loss(self):
        """Check if take profit or stop loss has been hit"""
        try:
            if not self.current_position:
                return
            
            current_price = self.api_client.get_current_price(config.TRADING_PAIR)
            if not current_price:
                return
            
            entry_price = float(self.current_position['entry_price'])
            side = self.current_position['side']
            
            # Check take profit
            take_profit = self.risk_manager.calculate_take_profit(entry_price, side)
            if (side == "Buy" and current_price >= take_profit) or \
               (side == "Sell" and current_price <= take_profit):
                logger.info(f"🎯 Take Profit hit at ${current_price:.2f}")
                self.close_trade(current_price, "TAKE_PROFIT")
                return
            
            # Check stop loss
            stop_loss = self.risk_manager.calculate_stop_loss(entry_price, side)
            if (side == "Buy" and current_price <= stop_loss) or \
               (side == "Sell" and current_price >= stop_loss):
                logger.warning(f"🛑 Stop Loss hit at ${current_price:.2f}")
                self.close_trade(current_price, "STOP_LOSS")
                self.notifier.notify_stop_loss_hit(config.TRADING_PAIR, 
                    abs(current_price - entry_price))
                return
        
        except Exception as e:
            logger.error(f"❌ Error checking TP/SL: {e}")
    
    def open_trade(self, signal):
        """Open a new trade based on signal"""
        try:
            # Check if we can open a position
            current_positions = self.api_client.get_all_positions()
            account_balance = self.api_client.get_account_balance()
            
            if not account_balance:
                logger.error("❌ Failed to get account balance")
                return False
            
            # Validate entry signal
            validation = self.risk_manager.validate_entry_signal(
                account_balance, current_positions
            )
            
            if not validation['can_trade']:
                return False
            
            # Get current price
            current_price = self.api_client.get_current_price(config.TRADING_PAIR)
            if not current_price:
                return False
            
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                account_balance, current_price
            )
            
            # Calculate stop loss and take profit
            if signal == "BUY":
                stop_loss = self.risk_manager.calculate_stop_loss(current_price, "Buy")
                take_profit = self.risk_manager.calculate_take_profit(current_price, "Buy")
                
                # Open long position
                order_id = self.api_client.open_long_position(
                    config.TRADING_PAIR,
                    position_size,
                    config.LEVERAGE
                )
                
                if order_id:
                    self.current_position = {
                        'side': 'Buy',
                        'entry_price': current_price,
                        'size': position_size,
                        'order_id': order_id,
                        'entry_time': datetime.now(),
                        'stop_loss': stop_loss,
                        'take_profit': take_profit
                    }
                    self.trades_opened += 1
                    logger.info(f"✅ LONG position opened at ${current_price:.2f}")
                    self.notifier.notify_trade_opened(
                        config.TRADING_PAIR, "BUY", current_price,
                        position_size, stop_loss, take_profit
                    )
                    return True
            
            elif signal == "SELL":
                stop_loss = self.risk_manager.calculate_stop_loss(current_price, "Sell")
                take_profit = self.risk_manager.calculate_take_profit(current_price, "Sell")
                
                # Open short position
                order_id = self.api_client.open_short_position(
                    config.TRADING_PAIR,
                    position_size,
                    config.LEVERAGE
                )
                
                if order_id:
                    self.current_position = {
                        'side': 'Sell',
                        'entry_price': current_price,
                        'size': position_size,
                        'order_id': order_id,
                        'entry_time': datetime.now(),
                        'stop_loss': stop_loss,
                        'take_profit': take_profit
                    }
                    self.trades_opened += 1
                    logger.info(f"✅ SHORT position opened at ${current_price:.2f}")
                    self.notifier.notify_trade_opened(
                        config.TRADING_PAIR, "SELL", current_price,
                        position_size, stop_loss, take_profit
                    )
                    return True
        
        except Exception as e:
            logger.error(f"❌ Error opening trade: {e}")
            self.notifier.notify_error(str(e))
        
        return False
    
    def close_trade(self, exit_price, reason="MANUAL"):
        """Close current trade"""
        try:
            if not self.current_position:
                logger.warning("⚠️ No open position to close")
                return False
            
            # Close position on exchange
            order_id = self.api_client.close_position(config.TRADING_PAIR)
            
            if order_id:
                entry_price = self.current_position['entry_price']
                side = self.current_position['side']
                size = self.current_position['size']
                
                # Calculate PnL
                pnl, pnl_percent = self.risk_manager.calculate_profit_loss(
                    entry_price, exit_price, side, size
                )
                
                self.total_pnl += pnl
                self.trades_closed += 1
                
                logger.info(f"✅ Position closed | Reason: {reason} | P/L: ${pnl:.2f} ({pnl_percent:.2f}%)")
                self.notifier.notify_trade_closed(
                    config.TRADING_PAIR, side, entry_price, exit_price, pnl, pnl_percent
                )
                
                self.current_position = None
                return True
        
        except Exception as e:
            logger.error(f"❌ Error closing trade: {e}")
            self.notifier.notify_error(str(e))
        
        return False
    
    def print_status(self):
        """Print current bot status"""
        try:
            account_balance = self.api_client.get_account_balance()
            if not account_balance:
                return
            
            profit_loss = account_balance - self.initial_balance + self.total_pnl
            profit_loss_percent = (profit_loss / self.initial_balance) * 100 if self.initial_balance > 0 else 0
            
            logger.info("="*60)
            logger.info("📊 BOT STATUS")
            logger.info("="*60)
            logger.info(f"Current Balance: ${account_balance:.2f}")
            logger.info(f"Initial Balance: ${self.initial_balance:.2f}")
            logger.info(f"Total P/L: ${profit_loss:.2f} ({profit_loss_percent:.2f}%)")
            logger.info(f"Trades Opened: {self.trades_opened}")
            logger.info(f"Trades Closed: {self.trades_closed}")
            logger.info(f"Open Position: {'Yes' if self.current_position else 'No'}")
            logger.info("="*60)
            
            risk_summary = self.risk_manager.get_summary(account_balance)
            logger.info(f"Daily Loss: ${risk_summary['daily_loss']:.2f}")
            logger.info(f"Max Daily Loss: ${risk_summary['max_daily_loss']:.2f}")
            logger.info("="*60)
        
        except Exception as e:
            logger.error(f"❌ Error printing status: {e}")
    
    def run(self):
        """Main bot loop"""
        self.is_running = True
        logger.info("🚀 Starting trading bot...")
        
        try:
            cycle_count = 0
            while self.is_running:
                cycle_count += 1
                
                try:
                    # Print status every 20 cycles
                    if cycle_count % 20 == 0:
                        self.print_status()
                    
                    # Check take profit and stop loss
                    if self.current_position:
                        self.check_take_profit_stop_loss()
                    else:
                        # Analyze market for new signal
                        signal = self.analyze_market()
                        
                        if signal in ["BUY", "SELL"]:
                            logger.info(f"📈 Signal: {signal}")
                            self.open_trade(signal)
                    
                    # Wait before next cycle (5 minute timeframe)
                    time.sleep(300)  # 5 minutes
                
                except KeyboardInterrupt:
                    logger.info("⌨️ Keyboard interrupt received")
                    break
                except Exception as e:
                    logger.error(f"❌ Error in trading cycle: {e}")
                    self.notifier.notify_error(str(e))
                    time.sleep(60)  # Wait before retry
        
        except Exception as e:
            logger.error(f"❌ Critical error: {e}")
            self.notifier.notify_error(f"Critical error: {e}")
        
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the bot gracefully"""
        logger.info("🛑 Shutting down bot...")
        self.is_running = False
        
        try:
            # Close any open positions
            if self.current_position:
                current_price = self.api_client.get_current_price(config.TRADING_PAIR)
                if current_price:
                    self.close_trade(current_price, "BOT_SHUTDOWN")
            
            # Print final status
            self.print_status()
            
            account_balance = self.api_client.get_account_balance()
            if account_balance:
                final_pnl = account_balance - self.initial_balance
                logger.info(f"📊 Final Balance: ${account_balance:.2f}")
                logger.info(f"📊 Final P/L: ${final_pnl:.2f}")
            
            self.notifier.notify_bot_stopped("Graceful shutdown")
            logger.info("✅ Bot shutdown complete")
        
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")

def main():
    """Main entry point"""
    try:
        bot = BybitTradingBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("\n⌨️ Bot interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
