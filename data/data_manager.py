from src.get_data import HistoricalData
import datetime as dt
import pandas as pd
from src.processes import Processes
import asyncio
from typing import Tuple
from src.util import parse_json

class DataManager:
    _instance = None
    _data_cache = {}
    _last_loaded = {}

    def __new__(cls, api_key: str, api_secret: str):
        if cls._instance is None:
            cls.__api_key = api_key
            cls.__api_secret = api_secret
            cls._instance = super(DataManager, cls).__new__(cls)
        return cls._instance

    def grab_ohlc_data(self, force_reload=False) -> pd.DataFrame:
        cache_key = "ohlc_data"

        if (
            not force_reload
            and cache_key in self._data_cache
            and cache_key in self._last_loaded
            and (dt.datetime.now() - self._last_loaded[cache_key]).seconds < 3600
        ):
            return self._data_cache[cache_key]
        else:
            self.load_ohlc_data()
            self._last_loaded[cache_key] = dt.datetime.now()
            return self._data_cache[cache_key]

    def load_ohlc_data(self) -> pd.DataFrame:
        cache_key = "ohlc_data"
        binance = HistoricalData(self.__api_key, self.__api_secret)
        df = binance.getKline("SOLUSDC", "12h").dropna()
        self._data_cache[cache_key] = df
        self._last_loaded[cache_key] = dt.datetime.now()
        return df

    def grab_price_path(
        self,
        force_reload=False,
        nPeriods: int = 10,
        nSims: int = 10,
        seed: int = 1234
    ) -> Tuple[Processes, pd.DataFrame]:
        cache_key = "price_path_data"
        if (
            not force_reload
            and cache_key in self._data_cache
            and cache_key in self._last_loaded
            and (dt.datetime.now() - self._last_loaded[cache_key]).seconds < 3600
        ):
            return self._data_cache["price_paths_object"], self._data_cache["price_paths_summary"]
        else:
            asyncio.run(self.load_price_paths(nPeriods, nSims,seed))
            return self._data_cache["price_paths_object"], self._data_cache["price_paths_summary"]

    async def load_price_paths(self,nPeriods: int, nSims: int, seed: int|None = None):
        proc = Processes(self.grab_ohlc_data(), seed)
        output = await proc.compare_processes(nPeriods, nSims)
        self._data_cache["price_paths_object"] = proc
        self._data_cache["price_paths_summary"] = output
        self._last_loaded["price_path_data"] = dt.datetime.now()


config = parse_json("config.json")
datamanager = DataManager(api_key=config["binance"]["API_KEY"], api_secret=config["binance"]["API_SECRET"])