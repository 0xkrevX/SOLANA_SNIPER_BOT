from typing import Dict, List, Optional, Union
import logging
from datetime import datetime

from .trading_strategies import TradingStrategy, MovingAverageCrossover, RSIStrategy, VolatilityBreakout

logger = logging.getLogger(__name__)

class StrategyManager:
    """Manager for handling multiple trading strategies"""
    
    def __init__(self):
        self.strategies: Dict[str, TradingStrategy] = {}
        self.active_strategies: List[str] = []
        self.market_data: Dict = {}
        self.last_update = None
        
    def add_strategy(self, strategy: TradingStrategy) -> None:
        """Add a trading strategy to the manager"""
        if strategy.name in self.strategies:
            logger.warning(f"Strategy {strategy.name} already exists, overwriting")
        
        self.strategies[strategy.name] = strategy
        logger.info(f"Added strategy: {strategy.name}")
        
    def remove_strategy(self, strategy_name: str) -> bool:
        """Remove a strategy from the manager"""
        if strategy_name in self.strategies:
            if strategy_name in self.active_strategies:
                self.active_strategies.remove(strategy_name)
            
            del self.strategies[strategy_name]
            logger.info(f"Removed strategy: {strategy_name}")
            return True
        
        logger.warning(f"Strategy {strategy_name} not found")
        return False
        
    def activate_strategy(self, strategy_name: str) -> bool:
        """Activate a strategy"""
        if strategy_name not in self.strategies:
            logger.error(f"Strategy {strategy_name} not found")
            return False
            
        if strategy_name not in self.active_strategies:
            self.active_strategies.append(strategy_name)
            self.strategies[strategy_name].activate()
            logger.info(f"Activated strategy: {strategy_name}")
        
        return True
        
    def deactivate_strategy(self, strategy_name: str) -> bool:
        """Deactivate a strategy"""
        if strategy_name not in self.strategies:
            logger.error(f"Strategy {strategy_name} not found")
            return False
            
        if strategy_name in self.active_strategies:
            self.active_strategies.remove(strategy_name)
            self.strategies[strategy_name].deactivate()
            logger.info(f"Deactivated strategy: {strategy_name}")
        
        return True
        
    def update_market_data(self, market_data: Dict) -> None:
        """Update market data for all strategies"""
        self.market_data = market_data
        self.last_update = datetime.now()
        
    def run_strategies(self) -> Dict[str, Dict]:
        """Run all active strategies and return their signals"""
        if not self.market_data:
            logger.warning("No market data available")
            return {}
            
        results = {}
        for strategy_name in self.active_strategies:
            strategy = self.strategies[strategy_name]
            try:
                signal = strategy.analyze(self.market_data)
                results[strategy_name] = signal
                logger.debug(f"Strategy {strategy_name} signal: {signal['signal']}")
            except Exception as e:
                logger.error(f"Error running strategy {strategy_name}: {str(e)}")
                
        return results
        
    def get_consensus_signal(self) -> Dict:
        """Get a consensus signal from all active strategies"""
        signals = self.run_strategies()
        
        if not signals:
            return {"signal": "HOLD", "reason": "No active strategies"}
            
        # Count signals
        buy_count = sum(1 for s in signals.values() if s.get('signal') == "BUY")
        sell_count = sum(1 for s in signals.values() if s.get('signal') == "SELL")
        hold_count = sum(1 for s in signals.values() if s.get('signal') == "HOLD")
        
        # Get majority signal
        if buy_count > sell_count and buy_count > hold_count:
            signal = "BUY"
            reason = f"Majority consensus: {buy_count}/{len(signals)} strategies recommend BUY"
        elif sell_count > buy_count and sell_count > hold_count:
            signal = "SELL"
            reason = f"Majority consensus: {sell_count}/{len(signals)} strategies recommend SELL"
        else:
            signal = "HOLD"
            reason = f"No clear consensus or majority HOLD: {hold_count}/{len(signals)} strategies"
            
        return {
            "signal": signal,
            "reason": reason,
            "buy_count": buy_count,
            "sell_count": sell_count,
            "hold_count": hold_count,
            "timestamp": datetime.now().isoformat(),
            "details": signals
        }
        
    def create_default_strategies(self) -> None:
        """Create and add default trading strategies"""
        # Moving Average Crossover with different windows
        self.add_strategy(MovingAverageCrossover(short_window=10, long_window=30))
        self.add_strategy(MovingAverageCrossover(short_window=20, long_window=50, 
                                                config={"name": "MA Crossover Medium"}))
        
        # RSI Strategy
        self.add_strategy(RSIStrategy())
        self.add_strategy(RSIStrategy(period=7, oversold=25, overbought=75,
                                     config={"name": "RSI Aggressive"}))
        
        # Volatility Breakout
        self.add_strategy(VolatilityBreakout())
        
        logger.info("Created default strategies") 