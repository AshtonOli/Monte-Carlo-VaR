import pandas as pd
from scipy import stats
from statsmodels.stats.diagnostic import het_arch, acorr_ljungbox
from statsmodels.tsa.stattools import adfuller

def _detect_jumps(returns):
    log_std = 2 * returns.log_returns.rolling(20).std()
    jumps = returns[(returns.log_returns > log_std) | (returns.log_returns < (returns.log_returns.mean() - log_std))]
    n_jumps = len(jumps)
    return n_jumps/len(returns)

def process_selection(returns : pd.DataFrame):
    results = {}

    # Test for normality
    jb_pvalue = stats.jarque_bera(returns.log_returns).pvalue
    sw_pvalue = stats.shapiro(returns.log_returns).pvalue
    results["Jarque-Bera"] = {
        "p-value" : jb_pvalue,
        'conclusion': 'Normal' if jb_pvalue > 0.05 else 'Non-normal'
    }
    results["Shapiro-Wilks"] = {
        "p-value" : sw_pvalue,
        'conclusion': 'Normal' if sw_pvalue > 0.05 else 'Non-normal'
    }

    # Test for volatility clustering
    arch_res = het_arch(returns.log_returns, nlags = 5)
    results["Hetson-Arch"] = {
        "p-value" : arch_res[1],
        'conclusion': 'Present' if arch_res[1] < 0.05 else 'Absent'
    }

    #Test for jumps
    jump_freq = _detect_jumps(returns)
    results["Jumps"] = {
        "frequency" : jump_freq,
        'conclusion': 'Significant' if jump_freq > 0.01 else 'Minimal'
    }

    # Test for mean reversion
    adf_res = adfuller(returns.log_returns)
    results["ADF"] = {
        "p-value" : adf_res[1],
        'conclusion': 'Mean-reverting' if adf_res[1] < 0.05 else 'Random walk'
    }

    # Test for autocorrelation
    lb_stat = acorr_ljungbox(returns.log_returns, lags = 10)
    results["Autocorrelation"] = {
        "p-value" : lb_stat["lb_pvalue"].iloc[-1],
        'conclusion': 'Present' if lb_stat["lb_pvalue"].iloc[-1] < 0.05 else 'Absent'
    }

    return results

def recommend_process(test_results: dict, stat_summary: dict):
    recomendations = []

    if (test_results["Jarque-Bera"]["conclusion"] == "Normal" and
        test_results["Hetson-Arch"]["conclusion"] == "Absent" and
        test_results["Jumps"]["conclusion"] == "Minimal"):
        recomendations.append({
            'process' : "GBM",
            "confidence" : 'high',
            'reason' : 'normal returns, constant volatility, no jumps'
        })
    
    if test_results["Hetson-Arch"]["conclusion"] == "Present":
        recomendations.append({
            "process" : "GARCH",
            "confidence" : "high",
            "reason" : "significant volatility clustering detected"
        })
    
    if test_results["Jumps"]["conclusion"] == "Significant":
        recomendations.append({
            "process" : "jump diffusion (merton)",
            "confidence" : "medium",
            "reason" : "significant jump frequency"
        })
    
    if test_results["ADF"]["conclusion"] == "Mean-reverting":
        recomendations.append({
            'process': 'Ornstein-Uhlenbeck',
            'confidence': 'medium',
            'reason': 'evidence of mean reversion in returns'
        })
    
    if (abs(stat_summary["skewness"]) > 0.5 or
        stat_summary["kurtosis"]):
        recomendations.append({
            "process" : "heston stochastic volatility",
            "confidence" : "medium",
            "reason" : "non-normal distrib with fat tails and skewness"
        })
    
    if not recomendations:
        recomendations.append({
            'process' : 'GBM',
            'confidence' : 'low',
            'reason' : "consider more stophisticated models"
        })

    return recomendations
    