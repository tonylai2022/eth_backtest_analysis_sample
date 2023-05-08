from typing import Dict, Optional

import json
import requests
import pandas as pd
import ccxt
from loguru import logger

from util import util_clean_data
from facade.test_crypto_price_data_service import CryptoPriceDataService

# init
GN_API_KEY: str = ''
GN_API_BASE_PATH: str = 'https://api.glassnode.com/v1/metrics'


class CryptoDataService:
    # const
    TIMEFRAME_DICT: Dict[str, str] = {'1d': '24h'}
    # init    
    _quote_ccy_code: str
    _binance = ccxt.binance()
    
    def __init__(self, quote_ccy_code: str='USDT'):
        self._quote_ccy_code = quote_ccy_code
    
    def create_gn_metric_price_df(self, gn_metric_str: str, 
                                  asset_str: str='BTC', 
                                  p_data_exchange_name: str = 'binance',
                                  timeframe: str='1d', date_since: str = '2021-01-01T00:00:00Z') -> \
        Optional[pd.DataFrame]:
        # return time series df with price data time horizon
        gn_metric_df: pd.DataFrame = self.fetch_glassnode_metric(gn_metric_str, asset_str, timeframe)
        price_data_symbol: str = asset_str + '/' + self._quote_ccy_code
        ohlcv_df: Optional[pd.DataFrame] = CryptoPriceDataService.fetch_ohlcv_times_series_df(
            price_data_symbol, p_data_exchange_name, timeframe, date_since)
        if ohlcv_df is None:
            logger.warning('No price data available! asset_str={}, date_since={}', asset_str, date_since)
            return
        price_df = ohlcv_df[[price_data_symbol + '_' + p_data_exchange_name + '_close']]
        metric_price_df: pd.DataFrame = util_clean_data.left_join_df_on_ind(price_df, gn_metric_df)
        metric_price_df.columns = ['price', 'metric']
        metric_price_df = metric_price_df[['metric', 'price']]
        return metric_price_df
            
    @classmethod
    def fetch_glassnode_metric(cls, metric_str: str, asset_str: str='BTC', timeframe: str='1d') -> pd.DataFrame:
        """Fetch Glassnode metric time series df (all time)
        
        Args:
            metric_str (str): api path str starting with "/"
            asset_str (str):
            timeframe (str):
                
        Returns:
            pd.DataFrame
        """
        if timeframe == '1d':
            timeframe = cls.TIMEFRAME_DICT.get(timeframe)
        # make API request
        req_str: str = GN_API_BASE_PATH + metric_str
        res = requests.get(req_str, params={'a': asset_str, 'api_key': GN_API_KEY, 'i': timeframe})
        # convert to pandas dataframe
        data_df = pd.read_json(res.text)
        data_df['t'] = data_df['t'].apply(
            lambda x: pd.to_datetime(cls._binance.iso8601(x * 1000)))
        data_df = data_df.set_index('t')
        data_df.index.name = 'timestamp'
        data_df.columns = [metric_str.split('/')[-1]]
        return data_df