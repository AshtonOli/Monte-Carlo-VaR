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
    
    def jdp(self, nPeriods: int, nSims: int) -> pd.DataFrame:
        interval = (self.returns.closetime.iloc[1] - self.returns.closetime.iloc[0]).seconds
        dt = interval / (360*24*252)
        mu = self.returns.log_returns.mean()/dt
        var = self.returns.log_returns.var()/dt

        jump_indices = np.abs(self.returns.log_returns) > 2.5 * self.returns.log_returns.std()
        if np.sum(jump_indices) > 0:
            jump_mean = self.returns.log_returns[jump_indices].mean()
            jump_std = self.returns.log_returns[jump_indices].std()
            lambda_jumps = len(self.returns.log_returns[jump_indices]) /( len(self.returns.log_returns) * dt)
        
            if len(self.returns.log_returns[~jump_indices]) > 0:
                sigma = np.std(self.returns.log_returns[~jump_indices]) / np.sqrt(dt)
            else:
                sigma = np.sqrt(var * 0.8)
        
            mu = mu - lambda_jumps * (np.exp(jump_mean + jump_std**2 / 2) - 1)
        else:
            sigma = np.sqrt(var)
            lambda_jumps = 0
            jump_mean = 0
            jump_std = 1
        
        time_index = [t for t in dt_date_range(self.returns.closetime.iloc[-1].to_pydatetime(), interval, nPeriods+1)]

        dW = np.random.normal(0, np.sqrt(dt), size=(nPeriods, nSims))
        jump_component = np.zeros((nPeriods, nSims))
        if lambda_jumps > 0:
            jump_prob = lambda_jumps * dt
            if jump_prob <= 0.1:
                jump_occurs = np.random.random((nPeriods, nSims)) < jump_prob
                jump_magnitude = np.random.normal(jump_mean, jump_std, size=(nPeriods, nSims))
                jump_component = jump_occurs * jump_magnitude
            else:
                n_jumps = np.random.poisson(jump_prob, size=(nPeriods, nSims))
                max_jumps = int(np.max(n_jumps) if np.any(n_jumps > 0) else 0)
                if max_jumps > 0:
                    jump_magnitudes = np.random.normal(jump_mean, jump_std, size=(max_jumps, nSims,max_jumps))
                    jump_indices = np.arange(max_jumps)[None, None, :]
                    jump_mask = jump_indices < n_jumps[:, :, None]
                    jump_component = np.sum(jump_mask * jump_magnitudes[None, :, :], axis=2)
        log_returns = (mu - (sigma**2) / 2) * dt + sigma * dW + jump_component
        prices = np.zeros((nPeriods + 1, nSims))
        prices[0, :] = self.returns.close.iloc[-1]

        cumulative_log_returns = np.exp(np.cumsum(log_returns, axis=0))
        prices[1:,:] = prices[0, :] * cumulative_log_returns
        df = pd.DataFrame(prices, index=time_index, columns=[f'sim_{i+1}' for i in range(nSims)])
        return df
