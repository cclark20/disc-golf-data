import os
import sys
import requests
import pandas as pd
import unidecode
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time

from tqdm import tqdm
pd.options.mode.chained_assignment = None  # default='warn'

def generate_player_finishes(players_df, year: int = 2021):
    players_stats = players_df

    for i in tqdm(range(len(players_stats))):
        try:
            URL = f"https://www.pdga.com/player/{players_stats['pdga #'][i]}/stats/{year}"
            page = requests.get(URL)
            for f in range(10):
                try:
                    dfs = pd.read_html(page.text, flavor='lxml')
                    break
                except:
                    # print(players_stats['pdga #'][i])
                    # print('it failed, retrying')
                    continue
        except:
            print(players_stats['pdga #'][i])
            raise Exception('read_html')
        for t in range(len(dfs)):
            if 'Tournament' in dfs[t].columns:
                player = dfs[t]
                break

        try:
            # only DGPT, Majors, and no silver series
            # player = player.drop(columns = ["Points", "Prize", "Dates"])
            player = player[(player["Tier"] == "ES") |
                            (player["Tier"] == "M") |
                            (player["Tier"] == "XM")]
            player = player[(player["Tournament"].str.contains("Silver Series") == False) &
                            (player["Tournament"].str.contains("Silver") == False) &
                            (player["Tournament"].str.contains("All Star") == False) &
                            (player["Tournament"].str.contains("Match Play") == False) &
                            (player["Tournament"].str.contains("Aussie Open") == False) &
                            (player["Tournament"].str.contains("Pro Tour Championship") == False)].reset_index(drop=True)

            for m in range(len(player["Tournament"])):
                if player["Tournament"][m] in players_stats:
                    players_stats.at[i, player["Tournament"][m]] = player["Place"][m]
                else:
                    # players_stats[player["Tournament"][m]] = None
                    players_stats.at[i, player["Tournament"][m]] = player["Place"][m]
        except:
            print(players_stats['pdga #'][i])
            print(dfs)
            print(player)
            raise Exception('could not parse their tournament data')
    import pdb; pdb.set_trace()
    # remove non US tournaments
    players_2 = players_stats.dropna(axis=1, thresh=5).reset_index(drop=True)

    # number of tournaments
    num_tournaments = len(players_2.columns[4:])

    # add descriptive stats
    players_2['best_finish'] = players_2.iloc[:, 4:(4+num_tournaments)].min(axis=1)
    players_2['worst_finish'] = players_2.iloc[:, 4:(4+num_tournaments)].max(axis=1)
    players_2['sd'] = players_2.iloc[:, 4:(4+num_tournaments)].std(axis=1).round(2)
    players_2['amt_played'] = players_2.iloc[:, 4:(4+num_tournaments)].count(axis=1)

    players_2.rename(columns={"pdga #": 'pdga_no'}, inplace=True)
    colnames = ["pdga_no", "name", "rating", "country", "best_finish", "worst_finish", "sd", "amt_played"]
    players_2 = players_2[colnames]
    players_2.columns= players_2.columns.str.lower()
    return players_2