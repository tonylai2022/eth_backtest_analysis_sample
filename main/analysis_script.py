from facade.test_crypto_data_service import CryptoDataService
from facade.backtester import Backtester

import matplotlib.pyplot as plt

# get data
crypto_data_service = CryptoDataService()
metric_price_df = crypto_data_service.create_gn_metric_price_df(
    '/addresses/active_count', 'ETH')

# data cleaning/data transformation
metric_price_df = metric_price_df.dropna()
metric_price_df['signal'] = metric_price_df['metric']
signal_price_df = metric_price_df[['signal', 'price']].dropna()

# regression
backtester = Backtester(signal_price_df)
backtester.plot_regression_result()

# test util performance
from util import util_performance
signal_price_df['return'] = signal_price_df['price'].pct_change()
return_series = signal_price_df['return'].loc['2021-07-01':]
print(util_performance.compute_sharpe_ratio(return_series, 365))
print(util_performance.compute_annualized_return(return_series, 365))
print(util_performance.compute_maximum_drawdown(return_series))
print(util_performance.compute_calmar_ratio(return_series, 365))



# run backtest
from facade.test_crypto_data_service import CryptoDataService
from facade.backtester import Backtester

# strat types
# 1. pure arb
# 2. factor strat

# scientific method: observsation, hypothesis, experiment, theory, prediction

# get data
metric_str = '/addresses/active_count'
crypto_data_service = CryptoDataService()
metric_price_df = crypto_data_service.create_gn_metric_price_df(
    metric_str, 'ETH', date_since = '2021-01-01T00:00:00Z')

# data cleaning/data transformation
metric_price_df = metric_price_df.dropna()
metric_price_df['signal'] = metric_price_df['metric'].pct_change()
signal_price_df = metric_price_df[['signal', 'price']].dropna()

# backtest
backtest_logic_name = 'breakout_signal'
upper_param_range = [0.5, 0.9]
lower_param_range = [0.2, 0.5]
unit_tc = 0.0003 # platform fee + bid ask spread + slippage

backtester = Backtester(signal_price_df)
# opt_result_dict = backtester.backtest_breakout_signal(
#     0.19, -0.01, unit_tc, is_long_exceeding_upper = False, cache_df = True)


opt_df = backtester.create_optimization_df(backtest_logic_name, upper_param_range, lower_param_range, unit_tc, False)
result_df = backtester.extract_optimization_result_from_df()
opt_result_dict = backtester.backtest_breakout_signal(
    0.88, 0.485, unit_tc, is_long_exceeding_upper = False, cache_df = True)
backtester.plot_equity_curve()

"""
Strategy performance evaluation:
1. strat metrics
2. equity curve
3. comparison with benchmark
4. data mining/curve fitting/overfitting/over optimization risk?
"""

# data mining risk checking
backtester = Backtester(signal_price_df)
opt_df = backtester.create_optimization_df(backtest_logic_name, upper_param_range, lower_param_range, unit_tc, False)
backtester.plot_param_heatmap()




