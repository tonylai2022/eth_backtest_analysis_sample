from typing import Optional
from math import sqrt

import pandas as pd
from loguru import logger



def compute_sharpe_ratio(return_series: pd.Series, annualized_factor: int=252) -> Optional[float]:
    mean_return: float = return_series.mean()
    return_std: float = return_series.std()
    if return_std == 0:
        logger.warning('Return std is 0!')
        return
    sharpe: float = mean_return / return_std * sqrt(annualized_factor)
    return sharpe


def compute_maximum_drawdown(return_series: pd.Series) -> float:
    cumul_return_series: pd.Series = return_series.cumsum()
    mdd: float = -(cumul_return_series-cumul_return_series.expanding().max()).min()
    return mdd


def compute_annualized_return(return_series: pd.Series, annualized_factor: int=252) -> float:
    num_day: int = return_series.size
    num_year: float = num_day / annualized_factor
    cumul_return_series: pd.Series = return_series.cumsum()
    cumul_return: float = cumul_return_series.iloc[-1]
    annualized_return: float = cumul_return / num_year
    return annualized_return


def compute_calmar_ratio(return_series: pd.Series, annualized_factor: int=252) -> Optional[float]:
    annualized_return: float = compute_annualized_return(return_series, annualized_factor)
    mdd: float = compute_maximum_drawdown(return_series)
    if mdd == 0:
        logger.warning('MDD is 0!')
        return
    calmar_ratio: float = annualized_return / mdd
    return calmar_ratio