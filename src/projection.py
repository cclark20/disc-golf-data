import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from tqdm import tqdm

def project(df, name_col, points_col, date_col):
    og = df
    # remove future events
    df = df[df['place'] != ''].dropna(subset=['total','place','points']) # remove future tournaments

    # type the date col
    df[date_col] = pd.to_datetime(df[date_col])
    
    averages = {}
    for player in tqdm(df[name_col].unique()):
        player_df = df[df[name_col] == player]

        # get most recent events
        player_df_filt = player_df[player_df[date_col] > datetime.now() - timedelta(days=365)]
        # if less than 5 events in last year, use all available events
        if len(player_df_filt) <= 5:
            player_df_filt = player_df
        elif len(player_df_filt) == 0:
            averages[player] = 0
            continue
        
        # remove low outliers in last year
        mean = player_df_filt[points_col].mean()
        sd = player_df_filt[points_col].std() if len(player_df_filt[points_col]) > 1 else 0
        lower_cutoff = mean - 2.5*sd
        player_df_filt = player_df_filt[player_df_filt[points_col] >= lower_cutoff]

        
        player_df_filt = player_df_filt.sort_values(date_col, ascending=False)
        
        # weight 2023 events (current form)
        double_events = int(len(player_df_filt[player_df_filt[date_col].dt.year == 2023]))
        points = list(player_df_filt[points_col])
        points = (points[:double_events] * 5) + points
        avg = sum(points) / len(points)

        # assign to player
        averages[player] = avg

    # fill in those with no projections
    for player in og[name_col].unique():
        if player not in averages:
            averages[player] = 0

    # add column with projections
    og['projection'] = og.apply(lambda row: averages[row[name_col]], axis=1)
    
    return og




        
        

def run(df:pd.DataFrame, points_col:str='points'):
    '''
    Input dataframe. must have column with points scored

    This function will group by person and then assign the average for projection.
    '''
    # get averages
    df_filt = df[df['place'] != ''].dropna(subset=['total','place','points']) # remove future tournaments
    # remove 2021 from projection
    mask = df_filt.tournament.str.contains('2021')
    df_filt = df_filt[~mask]
    # get avg for everyone
    avg_by_name = df_filt.groupby('name')[points_col].mean()
    df_filt['avg'] = df_filt['name'].map(avg_by_name)
    # calculate z-score for each points amt
    df_filt['z_score'] = df_filt.groupby('name',group_keys=False)[points_col].apply(lambda x: np.abs((x - x.mean()) / x.std()))
    # remove rows with z-score greater than 1.5 (threshold for outliers) or points higher than avg
    df_filt = df_filt[(df_filt['points'] > df_filt['avg']) | (df_filt['z_score'] <= 2.5)]
    
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