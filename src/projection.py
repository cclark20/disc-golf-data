import pandas as pd

def run(df:pd.DataFrame, points_col:str='points'):
    '''
    Input dataframe. must have column with points scored

    This function will group by person and then assign the average for projection.
    '''

    # get averages

    avg = df.groupby('name')[points_col].mean()

    # put avgs into df
    df['projection'] = df['name'].apply(lambda x: round(avg[x],2))
    df['projection'] = df['projection'].fillna(0)
    df = df.drop(columns=[points_col])

    return df