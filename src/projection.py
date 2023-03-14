import pandas as pd
import numpy as np

def run(df:pd.DataFrame, points_col:str='points'):
    '''
    Input dataframe. must have column with points scored

    This function will group by person and then assign the average for projection.
    '''
    # get averages
    df_filt = df[df['place'] != ''].dropna(subset=['total','place','points']) # remove future tournaments
    # get avg for everyone
    avg_by_name = df_filt.groupby('name')[points_col].mean()
    df_filt['avg'] = df_filt['name'].map(avg_by_name)
    # calculate z-score for each points amt
    df_filt['z_score'] = df_filt.groupby('name',group_keys=False)[points_col].apply(lambda x: np.abs((x - x.mean()) / x.std()))
    # remove rows with z-score greater than 1.5 (threshold for outliers) or points higher than avg
    df_filt = df_filt[(df_filt['points'] > df_filt['avg']) | (df_filt['z_score'] <= 1.5)]
    
    # get avg of final filtered df
    avg = df_filt.groupby('name')[points_col].mean().reset_index()

    # add col
    all_names = pd.DataFrame({'name': df['name'].unique()})
    avg = pd.merge(all_names, avg, on='name', how='left').fillna(0).set_index('name')['points']

    # put avgs into df
    df['projection'] = df['name'].apply(lambda x: round(avg[x],2))
    df['projection'] = df['projection'].fillna(0)
    df = df.drop(columns=[points_col])

    return df