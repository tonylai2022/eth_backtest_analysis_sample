from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger
import seaborn as sn
from math import sqrt
import statsmodels.api as sm 

from util import util_performance

class Backtester:
    _signal_price_df: pd.DataFrame
    _sample_size: int
    backtest_result_df: Optional[pd.DataFrame]
    opt_df: Optional[pd.DataFrame]
    
    def __init__(self, signal_price_df: pd.DataFrame):
        # input df must be of 2 columns, 1st is signal and 2nd is price data
        self._signal_price_df = signal_price_df
        self._signal_price_df['return'] = self._signal_price_df['price'].pct_change()
        self._signal_price_df = self._signal_price_df.dropna()
        self._sample_size = self._signal_price_df.shape[0]
        self.backtest_result_df = None
        self.opt_df = None
        
    def backtest_breakout_signal(self, upper_bound: float, lower_bound: float,
                                 unit_tc: float=0, is_long_exceeding_upper: bool=True, 
                                 cache_df: bool=False, annualized_factor: int=365) -> \
        Dict[str, Optional[float]]:
        # backtest
        df = self._signal_price_df
        df['benchmark'] = df['return'].cumsum()
        if is_long_exceeding_upper:
            df['position'] = np.where(df['signal'] > upper_bound, 1, np.where(df['signal'] < lower_bound, -1, 0))
        else:
            df['position'] = np.where(df['signal'] > upper_bound, -1, np.where(df['signal'] < lower_bound, 1, 0))
        df['transaction_cost'] = abs(df['position']-df['position'].shift(1)) * unit_tc
        df['pnl'] = df['position'].shift(1) * df['return'] - df['transaction_cost']
        df['cumulative_pnl'] = df['pnl'].cumsum()

        # cache
        if cache_df:
            self.backtest_result_df = df

        # performance evaluation
        sharpe_ratio: Optional[float] = util_performance.compute_sharpe_ratio(df['pnl'], annualized_factor)
        calmar_ratio: Optional[float] = util_performance.compute_calmar_ratio(df['pnl'], annualized_factor)
        annualized_return: float = util_performance.compute_annualized_return(df['pnl'], annualized_factor)
        maximum_drawdown: float = util_performance.compute_maximum_drawdown(df['pnl'])
        trading_number: float = abs(df['position']).sum()
        result_dict: Dict[str, Optional[float]] = {
            'sharpe_ratio': sharpe_ratio, 'calmar_ratio': calmar_ratio, 
            'annualized_return': annualized_return, 'maximum_drawdown': maximum_drawdown, 
            'trading_number': trading_number}
        return result_dict
    
    def create_optimization_df(self, backtest_logic_name: str, upper_param_range: List[float], 
                               lower_param_range: List[float], unit_tc: float, is_long_exceeding_upper: bool=True) -> \
        pd.DataFrame:
        # init
        result_list: List[Dict[str, Optional[float]]] = []
        upper_param_start: float = upper_param_range[0]
        upper_param_end: float = upper_param_range[1]
        lower_param_start: float = lower_param_range[0]
        lower_param_end: float = lower_param_range[1]
        upper_param_step: float = (upper_param_end - upper_param_start)/ 20
        lower_param_step: float = (lower_param_end - lower_param_start)/ 20
        
        for upper_param in np.arange(upper_param_start, upper_param_end, upper_param_step):
            for lower_param in np.arange(lower_param_start, lower_param_end, lower_param_step):
                if backtest_logic_name == 'breakout_signal':
                    result_dict: Dict[str, Optional[float]] = self.backtest_breakout_signal(
                        upper_param, lower_param, unit_tc, is_long_exceeding_upper)
                    result_dict['upper_param'] = upper_param
                    result_dict['lower_param'] = lower_param
                    result_list.append(result_dict)
        # optimise result
        result_df = pd.DataFrame(result_list)   
        self.opt_df = result_df 
        return result_df

    def extract_optimization_result_from_df(self, min_trading_ratio: float=0.3) -> pd.DataFrame:
        if self.opt_df is None:
            logger.warning('Optimization result df is None!')
            return
        min_trading_num: float = self._sample_size * min_trading_ratio
        opt_df_sorted = self.opt_df.sort_values('sharpe_ratio', ascending = False)   
        opt_df_sorted = opt_df_sorted[opt_df_sorted['trading_number'] >= min_trading_num]
        return opt_df_sorted
    
    def plot_param_heatmap(self) -> None:
        if self.opt_df is None:
            logger.warning('Optimization result df is None!')
            return
        param_heatmap_table = self.opt_df.pivot(index='upper_param', columns='lower_param', values='sharpe_ratio')
        sn.heatmap(param_heatmap_table, annot=True)
        
    def plot_equity_curve(self) -> None:
        if self.backtest_result_df is None:
            logger.warning('No backtest result df is cached!')
            return
        self.backtest_result_df[['cumulative_pnl', 'benchmark']].plot()
        
    def compute_benchmark_performance(self, annualized_factor: int=365) -> Dict[str, Optional[float]]:
        benchmark_r: pd.Series = self._signal_price_df['return']
        sharpe_ratio: Optional[float] = util_performance.compute_sharpe_ratio(benchmark_r, annualized_factor)
        calmar_ratio: Optional[float] = util_performance.compute_calmar_ratio(benchmark_r, annualized_factor)
        annualized_return: float = util_performance.compute_annualized_return(benchmark_r, annualized_factor)
        maximum_drawdown: float = util_performance.compute_maximum_drawdown(benchmark_r)
        result_dict: Dict[str, Optional[float]] = {
            'sharpe_ratio': sharpe_ratio, 'calmar_ratio': calmar_ratio, 
            'annualized_return': annualized_return, 'maximum_drawdown': maximum_drawdown}
        return result_dict
        
    def plot_regression_result(self, use_return: bool=True) -> None:
        """run regression: looking at alpha, beta, p-value, R-square and 
        correlation
        
        eg: TVS pct change on ETH return
        alpha = -0.0002
        beta = 0.9563
        
        y = mx + c
        y = beta*x + alpha 
        (Market Model/CAPM-CApital Asset Pricing Model; y=asset return, x=market benchmark return)
        beta: market risk
        alpha: additional return
        
        ETH return = 0.9563*TVS pct chg - 0.0002
        
        vs
        
        388 return = 0.5305*2800 return
        388 alpha = 0
        
        p-value is used to do statistical test
        for testing statistical significance
        """
        if use_return:
            self._run_regression(self._signal_price_df, 'signal', 'return')
            return
        self._run_regression(self._signal_price_df, 'signal', 'price')
        
    def _run_regression(self, data_df: pd.DataFrame, x_label: str, y_label: str) -> None:
        model = sm.OLS(data_df[y_label], sm.add_constant(data_df[x_label]))
        result = model.fit()
        print(result.summary())
        print('Correlation: ' + str(sqrt(result.rsquared)))
        sn.lmplot(x = x_label, y = y_label, data = data_df, fit_reg = True)
