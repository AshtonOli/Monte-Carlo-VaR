from binance import ThreadedWebsocketManager
from typing import Callable, Optional, Dict, List

class BinanceStreamer:
    def __init__(self, api_key: str, api_secret: str) -> None:
        self.twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
        self._symbols: List[str] = []
        self._klines: List[Dict] = []
        self._sockets: Dict[str, str] = {}
        self._is_running = False
    
    def start(self) -> None:
        """Start the WebSocket manager"""
        if not self._is_running:
            self.twm.start()
            self._is_running = True
            print("WebSocket manager started")
        else:
            print("WebSocket manager already running")
    
    def stop(self) -> None:
        """Stop the WebSocket manager and all streams"""
        if self._is_running:
            self.twm.stop()
            self._is_running = False
            self._sockets.clear()
            print("WebSocket manager stopped")
    
    def sockets(self) -> None:
        """Display active sockets"""
        print(f"{len(self._sockets)} sockets running.")
        for key in self._sockets.keys():
            print(f"  - {key}")
    
    def add_ticker_stream(self, symbol: str, callback: Callable) -> bool:
        """Add a ticker stream for a symbol"""
        stream_key = f"ticker_{symbol.upper()}"
        
        if stream_key in self._sockets:
            print(f"Ticker stream for {symbol} already exists")
            return False
            
        try:
            socket_id = self.twm.start_symbol_ticker_socket(
                callback=callback,
                symbol=symbol.upper()
            )
            self._sockets[stream_key] = socket_id
            if symbol.upper() not in self._symbols:
                self._symbols.append(symbol.upper())
            print(f"Added ticker stream for {symbol}")
            return True
        except Exception as e:
            print(f"Error adding ticker stream for {symbol}: {e}")
            return False
    
    def add_kline_stream(self, symbol: str, interval: str, callback: Callable) -> bool:
        """Add a kline stream for a symbol"""
        stream_key = f"kline_{symbol.upper()}_{interval}"
        
        if stream_key in self._sockets:
            print(f"Kline stream for {symbol} {interval} already exists")
            return False
            
        try:
            socket_id = self.twm.start_kline_socket(
                callback=callback,
                symbol=symbol.upper(),
                interval=interval
            )
            self._sockets[stream_key] = socket_id
            if symbol.upper() not in self._symbols:
                self._symbols.append(symbol.upper())
            print(f"Added kline stream for {symbol} {interval}")
            return True
        except Exception as e:
            print(f"Error adding kline stream for {symbol}: {e}")
            return False
    
    def stop_individual_stream(self, socket_type: str, symbol: str, interval: Optional[str] = None) -> bool:
        """Stop an individual stream"""
        symbol = symbol.upper()
        
        if socket_type.lower() == "kline":
            if interval is None:
                print("Please enter interval for kline stream!")
                return False
            stream_key = f"kline_{symbol}_{interval}"
        elif socket_type.lower() == "ticker":
            stream_key = f"ticker_{symbol}"
        else:
            print(f"Socket type '{socket_type}' not recognized")
            return False
        
        if stream_key not in self._sockets:
            print(f"Stream '{stream_key}' not found")
            return False
            
        try:
            self.twm.stop_socket(self._sockets[stream_key])
            del self._sockets[stream_key]
            print(f"Stopped stream: {stream_key}")
            return True
        except Exception as e:
            print(f"Error stopping stream {stream_key}: {e}")
            return False
    
    def get_active_symbols(self) -> List[str]:
        """Get list of active symbols"""
        return self._symbols.copy()
    
    def get_active_streams(self) -> List[str]:
        """Get list of active stream keys"""
        return list(self._sockets.keys())
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()