import pandas as pd
import numpy as np
from typing import Optional, Tuple
from src.util import dt_date_range
import asyncio
from src.util import dollar_format

class Processes:
    complete_gbm = None
    complete_jdp = None
    complete_ou = None
    def __init__(self, returns: pd.DataFrame, seed: Optional[int] = None) -> None:
        self.returns = returns
        if seed is not None:
            np.random.seed(seed)
        self.interval = (
            self.returns.closetime.iloc[1] - self.returns.closetime.iloc[0]
        ).seconds
        self.dt = self.interval / (
            3600 * 24 * 252
        )  # Convert seconds to days assuming 252 trading days in a year

    def _gbm(self, nPeriods: int, nSims: int) -> pd.DataFrame:
        mu = self.returns.log_returns.mean()
        sigma = self.returns.log_returns.std()

        dW = np.random.normal(0, np.sqrt(self.dt), size=(nPeriods, nSims))
        log_returns = (mu - (sigma**2) / 2) * self.dt + sigma * dW
        time_index = [
            t
            for t in dt_date_range(
                self.returns.closetime.iloc[-1].to_pydatetime(), self.interval, nPeriods
            )
        ]
        if nSims == 1:
            columns = ["log_returns"]
        else:
            columns = [f"sim_{i + 1}" for i in range(nSims)]

        df = pd.DataFrame(log_returns, index=time_index, columns=columns)
        return df

    def gbm_log_returns(self, nPeriods: int, nSims: int) -> pd.DataFrame:
        return self._gbm(nPeriods, nSims)

    def gbm_price_path(self, nPeriods: int, nSims: int) -> pd.DataFrame:
        log_returns = self._gbm(nPeriods, nSims)
        price_paths = self.returns.close.iloc[-1] * np.exp(log_returns.cumsum())
        initial_row = pd.DataFrame(
            [self.returns.close.iloc[-1]] * len(price_paths.columns),
            index=price_paths.columns,
        ).T
        initial_row.index = [self.returns.closetime.iloc[-1]]
        return pd.concat([initial_row, price_paths])

    def jdp(self, nPeriods: int, nSims: int) -> pd.DataFrame:
        mu = self.returns.log_returns.mean() / self.dt
        var = self.returns.log_returns.var() / self.dt

        jump_indices = (
            np.abs(self.returns.log_returns) > 2.5 * self.returns.log_returns.std()
        )
        if np.sum(jump_indices) > 0:
            jump_mean = self.returns.log_returns[jump_indices].mean()
            jump_std = self.returns.log_returns[jump_indices].std()
            lambda_jumps = len(self.returns.log_returns[jump_indices]) / (
                len(self.returns.log_returns) * self.dt
            )

            if len(self.returns.log_returns[~jump_indices]) > 0:
                sigma = np.std(self.returns.log_returns[~jump_indices]) / np.sqrt(
                    self.dt
                )
            else:
                sigma = np.sqrt(var * 0.8)

            mu = mu - lambda_jumps * (np.exp(jump_mean + jump_std**2 / 2) - 1)
        else:
            sigma = np.sqrt(var)
            lambda_jumps = 0
            jump_mean = 0
            jump_std = 1

        time_index = [
            t
            for t in dt_date_range(
                self.returns.closetime.iloc[-1].to_pydatetime(),
                self.interval,
                nPeriods + 1,
            )
        ]

        dW = np.random.normal(0, np.sqrt(self.dt), size=(nPeriods, nSims))
        jump_component = np.zeros((nPeriods, nSims))
        if lambda_jumps > 0:
            jump_prob = lambda_jumps * self.dt
            if jump_prob <= 0.1:
                jump_occurs = np.random.random((nPeriods, nSims)) < jump_prob
                jump_magnitude = np.random.normal(
                    jump_mean, jump_std, size=(nPeriods, nSims)
                )
                jump_component = jump_occurs * jump_magnitude
            else:
                n_jumps = np.random.poisson(jump_prob, size=(nPeriods, nSims))
                max_jumps = int(np.max(n_jumps) if np.any(n_jumps > 0) else 0)
                if max_jumps > 0:
                    jump_magnitudes = np.random.normal(
                        jump_mean, jump_std, size=(max_jumps, nSims, max_jumps)
                    )
                    jump_indices = np.arange(max_jumps)[None, None, :]
                    jump_mask = jump_indices < n_jumps[:, :, None]
                    jump_component = np.sum(
                        jump_mask * jump_magnitudes[None, :, :], axis=2
                    )
        log_returns = (mu - (sigma**2) / 2) * self.dt + sigma * dW + jump_component
        prices = np.zeros((nPeriods + 1, nSims))
        prices[0, :] = self.returns.close.iloc[-1]

        cumulative_log_returns = np.exp(np.cumsum(log_returns, axis=0))
        prices[1:, :] = prices[0, :] * cumulative_log_returns
        df = pd.DataFrame(
            prices, index=time_index, columns=[f"sim_{i + 1}" for i in range(nSims)]
        )
        return df
    #############################
    # Broken need to fix
    def _ou_fit(self) -> Tuple[float, float, float]:
        log_returns = self.returns.log_returns.to_numpy()

        x = log_returns[:-1]
        y = log_returns[1:]
        n = len(x)

        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.dot(x, y)
        sum_x2 = np.dot(x, x)

        denominator = n * sum_x2 - sum_x**2
        if abs(denominator) < 1e-10:
            theta = 0.001
            mu = np.mean(log_returns)
            sigma = np.std(log_returns) / np.sqrt(self.dt)
        else:
            b = (n * sum_xy - sum_x * sum_y) / denominator
            a = (sum_y - b * sum_x) / n

            if b >= 1 or b<= 0:
                theta = 0.001 / self.dt
                
            else:
                theta = -np.log(max(b, 1e-10)) / self.dt
                # theta = min(theta, .001 / self.dt)

            if theta > 0:
                mu = a / (1 - b)
            else:
                mu = np.mean(log_returns)

            residuals = y - (a + b * x)
            if theta > 1e-10:
                theoretical_var = (1 - np.exp(-2 * theta * self.dt)) / (2 * theta)
            else:
                theoretical_var = self.dt
            residual_var = np.var(residuals)
            if theoretical_var > 0:
                sigma = np.sqrt(residual_var / theoretical_var)
            else:
                sigma = np.std(residuals) / np.sqrt(self.dt)
        
        print(f"Fitted OU parameters: mu={mu}, sigma={sigma}, theta={theta}")

        return (mu, sigma, theta)

    def ou(self, nPeriods: int, nSims: int) -> pd.DataFrame:
        mu, sigma, theta = self._ou_fit()
        timesteps = np.arange(1, nPeriods + 1)

        exp_neg_theta_dt = np.exp(-theta * self.dt)
        
        if theta < 1e-10:
            # Brownian motion case
            std_increment = sigma * np.sqrt(self.dt)
            random_increments = np.random.normal(0, 1, size=(nPeriods, nSims))
            cumulative_increments = np.cumsum(random_increments, axis=0)
            
            # Generate future log return levels
            time_steps_col = timesteps[:, np.newaxis]
            log_returns = (
                self.returns.log_returns.iloc[-1]
                + mu * time_steps_col * self.dt
                + std_increment * cumulative_increments
            )
        else:
            # Full OU process
            std_next = np.sqrt(
                (sigma**2) * (1 - np.exp(-2 * theta * self.dt)) / (2 * theta)
            )
            random_shocks = np.random.normal(0, 1, size=(nPeriods, nSims))
            
            # Create coefficient matrix for noise contributions
            i_matrix, j_matrix = np.meshgrid(
                timesteps, np.arange(nPeriods), indexing="ij"
            )
            coefficient_matrix = np.where(
                j_matrix <= i_matrix - 1,
                exp_neg_theta_dt ** (i_matrix - j_matrix - 1),
                0.0,
            )
            noise_contributions = coefficient_matrix @ random_shocks

            # Calculate deterministic component
            time_steps_col = timesteps[:, np.newaxis]
            deterministic_part = mu + (
                self.returns.log_returns.iloc[-1] - mu
            ) * (exp_neg_theta_dt ** time_steps_col)

            # Combine deterministic and stochastic parts
            log_returns = deterministic_part + std_next * noise_contributions
        
        # Create complete log return series including initial value
        all_log_returns = np.vstack([
            np.full((1, nSims), self.returns.log_returns.iloc[-1]),
            log_returns
        ])
        
        # Calculate log return increments (period-to-period changes)
        log_return_increments = np.diff(all_log_returns, axis=0)
        
        # For the first period, use the simulated log return as the increment
        # (this represents the change from the last historical return to first simulated return)
        first_period_increments = log_returns[0, :] - self.returns.log_returns.iloc[-1]
        
        # Combine all increments
        all_increments = np.vstack([
            first_period_increments.reshape(1, -1),
            log_return_increments[1:, :]  # Skip the first diff since we handled it above
        ])
        
        # Convert to price multipliers and calculate cumulative product
        price_multipliers = np.exp(all_increments)
        
        # Calculate price paths starting from last historical price
        initial_prices = np.full((1, nSims), self.returns.close.iloc[-1])
        price_changes = initial_prices * np.cumprod(price_multipliers, axis=0)
        
        # Combine initial price with simulated prices
        price_paths = np.vstack([
            initial_prices,
            price_changes
        ])
        
        # Create DataFrame with proper date index
        df = pd.DataFrame(
            price_paths, 
            index=[
                t for t in dt_date_range(
                    self.returns.closetime.iloc[-1].to_pydatetime(),
                    self.interval,
                    nPeriods + 1
                )
            ],
            columns=[f"sim_{i + 1}" for i in range(nSims)]
        )
        return df
    #############################

    async def compare_processes(self, nPeriods: int, nSims: int) -> pd.DataFrame:


        async def run_gbm():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.gbm_price_path, nPeriods, nSims)
        async def run_jdp():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None,self.jdp, nPeriods, nSims)
        async def run_ou():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.ou, nPeriods, nSims)
        
        gbm_res, jdp_res, ou_res = await asyncio.gather(run_gbm(), run_jdp(), run_ou())

        self.complete_gbm = gbm_res
        self.complete_jdp = jdp_res
        self.complete_ou = ou_res

        gbm_final = gbm_res.iloc[-1]
        jdp_final = jdp_res.iloc[-1]
        ou_res = ou_res.iloc[-1]

        v_dollar_format = np.vectorize(dollar_format)
        data = [
            ["Max", "Min", "Mean", "Std", "Variance"],

        ]

        df = pd.DataFrame(
            columns = ["GBM", "JDP", "OU"],
            index = np.array(["Max", "Min", "Mean", "Std", "Variance"]),
            data = v_dollar_format(np.array([
                [max(gbm_final), min(gbm_final), np.mean(gbm_final), np.std(gbm_final), np.var(gbm_final)],
                [max(jdp_final), min(jdp_final), np.mean(jdp_final), np.std(jdp_final), np.var(jdp_final)],
                [max(ou_res), min(ou_res), np.mean(ou_res), np.std(ou_res), np.var(ou_res)],
            ]).T)
        ).reset_index(drop = False).rename(columns={"index" : "Stats"})
        
        return df

    def str_select(self, process_selected : str) -> pd.DataFrame:
        if process_selected.upper() == "GBM":
            if self.complete_gbm is not None:
                return self.complete_gbm
        elif process_selected.upper() == "JDP":
            if self.complete_jdp is not None:
                return self.complete_jdp
        elif process_selected.upper() == "OU":
            if self.complete_ou is not None:
                return self.complete_ou
        else:
            return pd.DataFrame()