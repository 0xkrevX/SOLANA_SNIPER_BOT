import time
import json
import logging
import asyncio
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import aiohttp  
import requests 

logger = logging.getLogger(__name__)

class SolanaMarketData:
    """Class for fetching and managing Solana market data"""
    
    def __init__(self, base_url: str = "https://api.coingecko.com/api/v3"):
        self.base_url = base_url
        self.cache = {}
        self.last_update = {}
        self.cache_expiry = 60  # seconds
        
    async def get_token_price(self, token_id: str = "solana", vs_currency: str = "usd") -> Dict:
        """
        Get current price of a token
        
        Args:
            token_id: Token ID (e.g., 'solana', 'bitcoin')
            vs_currency: Currency to compare against (e.g., 'usd', 'eur')
            
        Returns:
            Dict with price information
        """
        cache_key = f"{token_id}_{vs_currency}_price"
        
        # Check cache
        if cache_key in self.cache and (time.time() - self.last_update.get(cache_key, 0)) < self.cache_expiry:
            return self.cache[cache_key]
            
        url = f"{self.base_url}/simple/price"
        params = {
            "ids": token_id,
            "vs_currencies": vs_currency,
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if token_id in data:
                            result = {
                                "price": data[token_id].get(vs_currency, 0),
                                "market_cap": data[token_id].get(f"{vs_currency}_market_cap", 0),
                                "volume_24h": data[token_id].get(f"{vs_currency}_24h_vol", 0),
                                "change_24h": data[token_id].get(f"{vs_currency}_24h_change", 0),
                                "timestamp": datetime.now().isoformat(),
                            }
                            
                            # Update cache
                            self.cache[cache_key] = result
                            self.last_update[cache_key] = time.time()
                            
                            return result
                        else:
                            logger.error(f"Token {token_id} not found in response")
                            return {}
                    else:
                        logger.error(f"Error fetching price: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Error fetching price: {str(e)}")
            return {}
            
    async def get_historical_prices(self, token_id: str = "solana", vs_currency: str = "usd", 
                              days: int = 7) -> Dict:
        """
        Get historical price data for a token
        
        Args:
            token_id: Token ID (e.g., 'solana', 'bitcoin')
            vs_currency: Currency to compare against (e.g., 'usd', 'eur')
            days: Number of days of historical data
            
        Returns:
            Dict with historical price data
        """
        cache_key = f"{token_id}_{vs_currency}_{days}_history"
        
        # Check cache
        if cache_key in self.cache and (time.time() - self.last_update.get(cache_key, 0)) < self.cache_expiry:
            return self.cache[cache_key]
            
        url = f"{self.base_url}/coins/{token_id}/market_chart"
        params = {
            "vs_currency": vs_currency,
            "days": days,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        prices = []
                        timestamps = []
                        volumes = []
                        
                        for price_data in data.get("prices", []):
                            timestamps.append(price_data[0])
                            prices.append(price_data[1])
                            
                        for volume_data in data.get("total_volumes", []):
                            volumes.append(volume_data[1])
                            
                        result = {
                            "timestamps": timestamps,
                            "prices": prices,
                            "volumes": volumes,
                            "token_id": token_id,
                            "vs_currency": vs_currency,
                            "days": days,
                        }
                        
                        # Update cache
                        self.cache[cache_key] = result
                        self.last_update[cache_key] = time.time()
                        
                        return result
                    else:
                        logger.error(f"Error fetching historical prices: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Error fetching historical prices: {str(e)}")
            return {}
            
    async def get_token_info(self, token_id: str = "solana") -> Dict:
        """
        Get detailed information about a token
        
        Args:
            token_id: Token ID (e.g., 'solana', 'bitcoin')
            
        Returns:
            Dict with token information
        """
        cache_key = f"{token_id}_info"
        
        # Check cache
        if cache_key in self.cache and (time.time() - self.last_update.get(cache_key, 0)) < self.cache_expiry:
            return self.cache[cache_key]
            
        url = f"{self.base_url}/coins/{token_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        result = {
                            "id": data.get("id", ""),
                            "symbol": data.get("symbol", ""),
                            "name": data.get("name", ""),
                            "description": data.get("description", {}).get("en", ""),
                            "market_cap_rank": data.get("market_cap_rank", 0),
                            "current_price": data.get("market_data", {}).get("current_price", {}),
                            "market_cap": data.get("market_data", {}).get("market_cap", {}),
                            "total_volume": data.get("market_data", {}).get("total_volume", {}),
                            "high_24h": data.get("market_data", {}).get("high_24h", {}),
                            "low_24h": data.get("market_data", {}).get("low_24h", {}),
                            "price_change_percentage_24h": data.get("market_data", {}).get("price_change_percentage_24h", 0),
                            "price_change_percentage_7d": data.get("market_data", {}).get("price_change_percentage_7d", 0),
                            "price_change_percentage_30d": data.get("market_data", {}).get("price_change_percentage_30d", 0),
                            "timestamp": datetime.now().isoformat(),
                        }
                        
                        # Update cache
                        self.cache[cache_key] = result
                        self.last_update[cache_key] = time.time()
                        
                        return result
                    else:
                        logger.error(f"Error fetching token info: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Error fetching token info: {str(e)}")
            return {}
            
    def get_token_price_sync(self, token_id: str = "solana", vs_currency: str = "usd") -> Dict:
        """Synchronous version of get_token_price"""
        return asyncio.run(self.get_token_price(token_id, vs_currency))
        
    def get_historical_prices_sync(self, token_id: str = "solana", vs_currency: str = "usd", 
                             days: int = 7) -> Dict:
        """Synchronous version of get_historical_prices"""
        return asyncio.run(self.get_historical_prices(token_id, vs_currency, days))
        
    def get_token_info_sync(self, token_id: str = "solana") -> Dict:
        """Synchronous version of get_token_info"""
        return asyncio.run(self.get_token_info(token_id))
        
    def get_market_data_for_strategy(self, token_id: str = "solana", vs_currency: str = "usd",
                                   days: int = 30) -> Dict:
        """
        Get market data formatted for trading strategies
        
        Args:
            token_id: Token ID (e.g., 'solana', 'bitcoin')
            vs_currency: Currency to compare against (e.g., 'usd', 'eur')
            days: Number of days of historical data
            
        Returns:
            Dict with market data formatted for trading strategies
        """
        historical_data = self.get_historical_prices_sync(token_id, vs_currency, days)
        current_price = self.get_token_price_sync(token_id, vs_currency)
        
        prices = historical_data.get("prices", [])
        timestamps = historical_data.get("timestamps", [])
        volumes = historical_data.get("volumes", [])
        
        # Calculate highs and lows (simple implementation)
        highs = []
        lows = []
        
        window_size = min(5, len(prices))
        for i in range(len(prices)):
            start_idx = max(0, i - window_size)
            window = prices[start_idx:i+1]
            highs.append(max(window) if window else prices[i])
            lows.append(min(window) if window else prices[i])
            
        return {
            "prices": prices,
            "highs": highs,
            "lows": lows,
            "timestamps": timestamps,
            "volumes": volumes,
            "current_price": current_price.get("price", 0),
            "change_24h": current_price.get("change_24h", 0),
            "token_id": token_id,
            "vs_currency": vs_currency,
        } 
