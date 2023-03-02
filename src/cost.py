import pandas as pd
import numpy as np

# define exponential decay function
def exp_decay(x, a, b):
    return a * np.exp(-b * x)

def calc_cost(col:pd.Series, decay_rate:float=0.0125, max_cost:int=25) -> pd.Series:
    # normalize the data
    data_norm = col / np.max(col)

    # create output vector with exponential decay
    output = exp_decay(np.arange(len(data_norm)), 1, decay_rate) * np.max(data_norm)

    # scale output to max value of 25
    output_scaled = output / np.max(output) * max_cost

    return pd.Series(output_scaled)
