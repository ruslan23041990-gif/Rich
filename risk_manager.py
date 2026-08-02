"""
Risk Management Module
Handles stop-loss, take-profit, position sizing, and daily loss limits
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RiskManager:
    """Manages trading risks and position sizing"""
    
    def __init__(self, initial_balance, config):
        """Initialize risk manager"""
        self.initial_balance = initial_balance
        self.config = config
        self.daily_loss = 0
        self.day_start = datetime.now()
        self.positions = []
    
    def calculate_position_size(self, account_balance, current_price):
        """Calculate optimal position size based on account balance"""
        try:
            max_risk_amount = account_balance * 0.01  # 1% risk per trade
            price_movement = current_price * (self.config.STOP_LOSS_PERCENT / 100)
            position_size = max_risk_amount / price_movement
            
            if position_size > self.config.POSITION_SIZE:
                position_size = self.config.POSITION_SIZE
            
            logger.info(f"📊 Calculated position size: {position_size:.4f}")
            return position_size
        except Exception as e:
            logger.error(f"❌ Error calculating position size: {e}")
            return self.config.POSITION_SIZE
    
    def calculate_stop_loss(self, entry_price, side):
        """Calculate stop-loss price"""
        if side == "Buy":
            stop_loss = entry_price * (1 - self.config.STOP_LOSS_PERCENT / 100)
        else:
            stop_loss = entry_price * (1 + self.config.STOP_LOSS_PERCENT / 100)
        
        logger.info(f"🛑 Stop loss calculated: ${stop_loss:.2f} ({self.config.STOP_LOSS_PERCENT}%)")
        return stop_loss
    
    def calculate_take_profit(self, entry_price, side):
        """Calculate take-profit price"""
        if side == "Buy":
            take_profit = entry_price * (1 + self.config.TAKE_PROFIT_PERCENT / 100)
        else:
            take_profit = entry_price * (1 - self.config.TAKE_PROFIT_PERCENT / 100)
        
        logger.info(f"🎯 Take profit calculated: ${take_profit:.2f} ({self.config.TAKE_PROFIT_PERCENT}%)")
        return take_profit
    
    def can_open_position(self, account_balance, open_positions_count):
        """Check if new position can be opened"""
        if open_positions_count >= self.config.MAX_POSITIONS:
            logger.warning(f"⚠️ Max positions limit reached ({self.config.MAX_POSITIONS})")
            return False
        
        if self.daily_loss >= self.config.MAX_DAILY_LOSS:
            logger.warning(f"⚠️ Daily loss limit reached: ${self.daily_loss:.2f}")
            return False
        
        if datetime.now() - self.day_start > timedelta(days=1):
            self.daily_loss = 0
            self.day_start = datetime.now()
            logger.info("📅 New trading day started")
        
        return True
    
    def update_daily_loss(self, loss_amount):
        """Update cumulative daily loss"""
        self.daily_loss += loss_amount
        logger.info(f"💔 Daily loss updated: ${self.daily_loss:.2f}")
    
    def calculate_profit_loss(self, entry_price, exit_price, side, quantity):
        """Calculate profit or loss for a position"""
        if side == "Buy":
            pnl = (exit_price - entry_price) * quantity
        else:
            pnl = (entry_price - exit_price) * quantity
        
        pnl_percent = (pnl / (entry_price * quantity)) * 100
        
        if pnl >= 0:
            logger.info(f"✅ Profit: ${pnl:.2f} ({pnl_percent:.2f}%)")
        else:
            logger.warning(f"❌ Loss: ${pnl:.2f} ({pnl_percent:.2f}%)")
            self.update_daily_loss(abs(pnl))
        
        return pnl, pnl_percent
    
    def validate_entry_signal(self, account_balance, current_positions):
        """Comprehensive validation before entering a trade"""
        validation_results = {'can_trade': True, 'reasons': []}
        
        if len(current_positions) >= self.config.MAX_POSITIONS:
            validation_results['can_trade'] = False
            validation_results['reasons'].append(f"Max positions ({self.config.MAX_POSITIONS}) reached")
        
        if self.daily_loss >= self.config.MAX_DAILY_LOSS:
            validation_results['can_trade'] = False
            validation_results['reasons'].append(f"Daily loss limit (${self.config.MAX_DAILY_LOSS}) exceeded")
        
        min_balance = self.config.POSITION_SIZE * 10
        if account_balance < min_balance:
            validation_results['can_trade'] = False
            validation_results['reasons'].append(f"Insufficient balance. Min required: ${min_balance}")
        
        if validation_results['reasons']:
            logger.warning(f"⚠️ Trade validation failed: {', '.join(validation_results['reasons'])}")
        
        return validation_results
    
    def get_summary(self, account_balance):
        """Get risk management summary"""
        summary = {
            'account_balance': account_balance,
            'daily_loss': self.daily_loss,
            'max_daily_loss': self.config.MAX_DAILY_LOSS,
            'daily_loss_percent': (self.daily_loss / account_balance * 100) if account_balance > 0 else 0,
            'stop_loss_percent': self.config.STOP_LOSS_PERCENT,
            'take_profit_percent': self.config.TAKE_PROFIT_PERCENT,
            'max_positions': self.config.MAX_POSITIONS,
            'position_size': self.config.POSITION_SIZE,
            'leverage': self.config.LEVERAGE
        }
        
        logger.info(f"📋 Risk Summary - Balance: ${summary['account_balance']:.2f}, Daily Loss: ${summary['daily_loss']:.2f}, Remaining: ${summary['max_daily_loss'] - summary['daily_loss']:.2f}")
        
        return summary