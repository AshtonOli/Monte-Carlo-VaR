import pandas as pd
import numpy as np

from src.util import dt_date_range
class Processes:
    def __init__(self, returns: pd.DataFrame) -> None:
        self.returns = returns
    
    
    def _gbm(self,nPeriods: int, nSims: int) -> pd.DataFrame:
        mu = self.returns.log_returns.mean()
        sigma = self.returns.log_returns.std()
        interval = (self.returns.closetime.iloc[1] - self.returns.closetime.iloc[0]).seconds
        dt = interval / (360*24*252)

        dW = np.random.normal(0,np.sqrt(dt), size = (nPeriods, nSims))
        log_returns = (mu - (sigma**2)/2) * dt + sigma * dW
        time_index = [t for t in dt_date_range(self.returns.closetime.iloc[-1].to_pydatetime(), interval,nPeriods)]
        if nSims == 1:
            columns = ['log_returns']
        else:
            columns = [f'sim_{i+1}' for i in range(nSims)]
        
        df = pd.DataFrame(log_returns, index=time_index, columns=columns)
        return df

    def gbm_log_returns(self,nPeriods: int, nSims: int) -> pd.DataFrame:
        return self._gbm(nPeriods,nSims)
    
    def gbm_price_path(self,nPeriods: int, nSims: int) -> pd.DataFrame:
        log_returns = self._gbm(nPeriods,nSims)
        price_paths = self.returns.close.iloc[-1] * np.exp(log_returns.cumsum())
        initial_row = pd.DataFrame(
            [self.returns.close.iloc[-1]] * len(price_paths.columns),
            index = price_paths.columns,
        ).T
        initial_row.index = [self.returns.closetime.iloc[-1]]
        return pd.concat([initial_row,price_paths])
    
    

