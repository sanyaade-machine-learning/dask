import pandas as pd
import numpy as np

from .core import tokenize, DataFrame

__all__ = ['make_timeseries']


def make_float(n, rstate):
    return rstate.rand(n) * 2 - 1

def make_int(n, rstate):
    return rstate.poisson(1000, size=n)


names = ['Alice', 'Bob', 'Charlie', 'Dan', 'Edith', 'Frank', 'George',
'Hannah', 'Ingrid', 'Jerry', 'Kevin', 'Laura', 'Michael', 'Norbert', 'Oliver',
'Patricia', 'Quinn', 'Ray', 'Sarah', 'Tim', 'Ursula', 'Victor', 'Wendy',
'Xavier', 'Yvonne', 'Zelda']


def make_string(n, rstate):
    return rstate.choice(names, size=n)


def make_categorical(n, rstate):
    return pd.Categorical.from_codes(rstate.randint(0, len(names), size=n),
                                     names)

make = {float: make_float,
        int: make_int,
        str: make_string,
        object: make_string,
        'category': make_categorical}


def make_timeseries_part(start, end, dtypes, freq, seed):
    index = pd.DatetimeIndex(start=start, end=end, freq=freq)
    state = np.random.RandomState(seed)
    columns = dict((k, make[dt](len(index), state)) for k, dt in dtypes.items())
    return pd.DataFrame(columns, index=index, columns=sorted(columns))


def make_timeseries(start, end, dtypes, freq, partition_freq, seed=None):
    """ Create timeseries dataframe with random data

    Parameters
    ----------
    start: datetime (or datetime-like string)
        Start of time series
    end: datetime (or datetime-like string)
        End of time series
    dtypes: dict
        Mapping of column names to types.
        Valid types include {float, int, str, 'category'}
    freq: string
        String like '2s' or '1H' or '12W' for the time series frequency
    partition_freq: string
        String like '1M' or '2Y' to divide the dataframe into partitions
    seed: int (optional)
        Randomstate seed

    >>> import dask.dataframe as dd
    >>> df = dd.demo.make_timeseries('2000', '2010',
    ...                              {'value': float, 'name': str, 'id': int},
    ...                              freq='2H', partition_freq='1D', seed=1)
    >>> df.head()
                           id    name     value
    2000-01-01 00:00:00   971   Edith -0.053963
    2000-01-01 02:00:00   937   Kevin -0.625998
    2000-01-01 04:00:00   965  Xavier -0.922559
    2000-01-01 06:00:00  1011   Sarah  0.866421
    2000-01-01 08:00:00  1005   Zelda -0.319609
    """
    divisions = list(pd.DatetimeIndex(start=start, end=end,
                                      freq=partition_freq))
    state = np.random.RandomState(seed)
    seeds = state.randint(0, 2**31, size=len(divisions))
    name = 'make-timeseries-' + tokenize(start, end, dtypes, freq, partition_freq)
    dsk = dict(((name, i), (make_timeseries_part, divisions[i], divisions[i + 1],
                                                 dtypes, freq, seeds[i]))
                for i in range(len(divisions) - 1))
    return DataFrame(dsk, name, sorted(dtypes), divisions)