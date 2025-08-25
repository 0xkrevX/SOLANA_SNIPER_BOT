from typing import Dict, List, Optional, Union
import time
import numpy as np
from datetime import datetime, timedelta
   
class TradingStrategy:
    """Base class for all trading strategies"""  
    
    def __init__(self, name: str, config: Dict = None):
        self.name = name
        self.config = config or {}
        self.active = False
        self.last_signal = None
        
    def analyze(self, market_data: Dict) -> Dict:
        """Analyze market data and return trading signals"""
        raise NotImplementedError("Subclasses must implement analyze method")
    
    def get_signal(self) -> Dict:
        """Get the latest trading signal"""
        return self.last_signal
        
    def activate(self):
        """Activate the strategy"""
        self.active = True
        
    def deactivate(self):
        """Deactivate the strategy"""
        self.active = False


class MovingAverageCrossover(TradingStrategy):
    """Moving Average Crossover strategy for Solana trading"""
    
    def __init__(self, short_window: int = 20, long_window: int = 50, config: Dict = None):
        super().__init__("MA Crossover", config)
        self.short_window = short_window
        self.long_window = long_window
        
    def analyze(self, market_data: Dict) -> Dict:
        """
        Analyze price data using moving average crossover strategy
        
        Args:
            market_data: Dict containing price history
            
        Returns:
            Dict with trading signal (BUY, SELL, HOLD)
        """
        prices = market_data.get('prices', [])
        if len(prices) < self.long_window:
            self.last_signal = {"signal": "HOLD", "reason": "Insufficient data"}
            return self.last_signal
            
        # Calculate moving averages
        short_ma = np.mean(prices[-self.short_window:])
        long_ma = np.mean(prices[-self.long_window:])
        
        # Previous values
        prev_short_ma = np.mean(prices[-self.short_window-1:-1])
        prev_long_ma = np.mean(prices[-self.long_window-1:-1])
        
        # Generate signals
        if short_ma > long_ma and prev_short_ma <= prev_long_ma:
            signal = "BUY"
            reason = f"Short MA ({short_ma:.2f}) crossed above Long MA ({long_ma:.2f})"
        elif short_ma < long_ma and prev_short_ma >= prev_long_ma:
            signal = "SELL"
            reason = f"Short MA ({short_ma:.2f}) crossed below Long MA ({long_ma:.2f})"
        else:
            signal = "HOLD"
            reason = f"No crossover detected"
            
        self.last_signal = {
            "signal": signal,
            "reason": reason,
            "short_ma": short_ma,
            "long_ma": long_ma,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.last_signal


class RSIStrategy(TradingStrategy):
    """RSI (Relative Strength Index) based trading strategy"""
    
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70, config: Dict = None):
        super().__init__("RSI Strategy", config)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        
    def calculate_rsi(self, prices: List[float]) -> float:
        """Calculate RSI value from price data"""
        if len(prices) <= self.period:
            return 50  # Default value if not enough data
            
        # Calculate price changes
        deltas = np.diff(prices)
        
        # Calculate gains and losses
        gains = np.clip(deltas, 0, None)
        losses = -np.clip(deltas, None, 0)
        
        # Calculate average gains and losses
        avg_gain = np.mean(gains[-self.period:])
        avg_loss = np.mean(losses[-self.period:])
        
        if avg_loss == 0:
            return 100
            
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    def analyze(self, market_data: Dict) -> Dict:
        """
        Analyze price data using RSI strategy
        
        Args:
            market_data: Dict containing price history
            
        Returns:
            Dict with trading signal (BUY, SELL, HOLD)
        """
        prices = market_data.get('prices', [])
        if len(prices) <= self.period:
            self.last_signal = {"signal": "HOLD", "reason": "Insufficient data"}
            return self.last_signal
            
        # Calculate current and previous RSI
        current_rsi = self.calculate_rsi(prices)
        prev_rsi = self.calculate_rsi(prices[:-1])
        
        # Generate signals
        if current_rsi < self.oversold and prev_rsi >= self.oversold:
            signal = "BUY"
            reason = f"RSI ({current_rsi:.2f}) entered oversold territory"
        elif current_rsi > self.overbought and prev_rsi <= self.overbought:
            signal = "SELL"
            reason = f"RSI ({current_rsi:.2f}) entered overbought territory"
        else:
            signal = "HOLD"
            reason = f"RSI ({current_rsi:.2f}) not at extreme levels"
            
        self.last_signal = {
            "signal": signal,
            "reason": reason,
            "rsi": current_rsi,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.last_signal


class VolatilityBreakout(TradingStrategy):
    """Volatility Breakout trading strategy for Solana"""
    
    def __init__(self, lookback_period: int = 20, volatility_factor: float = 1.5, config: Dict = None):
        super().__init__("Volatility Breakout", config)
        self.lookback_period = lookback_period
        self.volatility_factor = volatility_factor
        
    def analyze(self, market_data: Dict) -> Dict:
        """
        Analyze price data using volatility breakout strategy
        
        Args:
            market_data: Dict containing price history with high and low values
            
        Returns:
            Dict with trading signal (BUY, SELL, HOLD)
        """
        highs = market_data.get('highs', [])
        lows = market_data.get('lows', [])
        closes = market_data.get('prices', [])
        
        if len(closes) < self.lookback_period:
            self.last_signal = {"signal": "HOLD", "reason": "Insufficient data"}
            return self.last_signal
            
        # Calculate average true range (ATR) as volatility measure
        ranges = []
        for i in range(1, min(self.lookback_period, len(highs))):
            true_range = max(
                highs[-(i+1)] - lows[-(i+1)],
                abs(highs[-(i+1)] - closes[-(i+2)]),
                abs(lows[-(i+1)] - closes[-(i+2)])
            )
            ranges.append(true_range)
            
        atr = np.mean(ranges) if ranges else 0
        
        # Calculate breakout levels
        current_price = closes[-1]
        previous_close = closes[-2]
        upper_band = previous_close + (atr * self.volatility_factor)
        lower_band = previous_close - (atr * self.volatility_factor)
        
        # Generate signals
        if current_price > upper_band:
            signal = "BUY"
            reason = f"Price ({current_price:.2f}) broke above upper band ({upper_band:.2f})"
        elif current_price < lower_band:
            signal = "SELL"
            reason = f"Price ({current_price:.2f}) broke below lower band ({lower_band:.2f})"
        else:
            signal = "HOLD"
            reason = f"Price ({current_price:.2f}) within volatility bands"
            
        self.last_signal = {
            "signal": signal,
            "reason": reason,
            "atr": atr,
            "upper_band": upper_band,
            "lower_band": lower_band,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.last_signal 
