import os
import sys
import requests
import pandas as pd
import unidecode
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
from datetime import datetime
from tqdm import tqdm


import re
def extract_int(string):
    if string == 'E':
        return int(0)
    if string == '(P)':
        return int(1000)
    # find integer (with + or -) in string. if no digit, return None
    match = re.search(r'[+-]?\d+', string)
    if match:
        return int(match.group())
    else:
        return None
    
def count_scores(pars:int, scores:int) -> dict:
    results={'aces':0,'eagles+':0,'birdies':0,'pars':0,'bogeys':0,'doubles+':0}
    for i in range(len(pars)):
        if scores[i] == 1:
            results['aces'] += 1
        elif scores[i] <= pars[i] - 2:
            results['eagles+'] += 1
        elif scores[i] == pars[i] - 1:
            results['birdies'] += 1
        elif scores[i] == pars[i]:
            results['pars'] += 1
        elif scores[i] == pars[i] + 1:
            results['bogeys'] += 1
        elif scores[i] >= pars[i] + 2:
            results['doubles+'] += 1
    return results
    
def get_udisc_html(udisc_id: str = 'usdgc2022', round:int=1):
    URL = f"https://udisclive.com/live/{udisc_id}/{round}?t=scores&d=MPO"
    service = Service('./chromedriver')
    driver = webdriver.Chrome(service=service)
    driver.get(URL)
    time.sleep(5)
    html = driver.page_source

    soup = BeautifulSoup(html, 'html.parser')

    return soup

def get_round_table(soup) -> pd.DataFrame:
    divs = soup.find_all('div', attrs={'style': "border-top: 1px solid rgb(var(--color-divider)); font-size: 13px;"})
    divs2 = soup.find_all('div', attrs={'style': "border-top: 1px solid rgb(var(--color-divider)); font-size: 10px;"})
    divs = divs + divs2
    
    # generate table
    ## initiate lists for data
    names = []
    places = []
    totals = []
    round_scores = []
    hole_scores_all = []

    # loop through each div (a row) and get cells we need.
    for i in range(len(divs)):
        cells = divs[i].find_all('div')
        cells = [cell for cell in cells if not cell.find('div')] # remove cells that have more than one div
        cells = [cell for cell in cells if not cell.find('i')] # remove cells that have an i element

        # get text based on place
        name           = unidecode.unidecode(cells[1].get_text())
        place          = extract_int(cells[0].get_text())
        total          = extract_int(cells[2].get_text())
        round_score    = extract_int(cells[4].get_text())
        hole_scores    = [extract_int(cell.get_text()) for cell in cells[5:23]]
        
        if place == None:
            continue

        # add to lists
        names.append(name)
        places.append(place)
        totals.append(total)
        round_scores.append(round_score)
        hole_scores_all.append(hole_scores)

    # create pandas.DataFrame
    df = pd.DataFrame({
        'name': names,
        'place': places,
        'total': totals,
        'round_score': round_scores,
        'hole_scores': hole_scores_all
    })
    # print(df)
    # print(df.dtypes)

    return df

def get_round_pars(soup) -> list:
    divs = soup.find_all('div', attrs={'style': "font-weight: 500;"})
    round_pars=[extract_int(div.get_text()) for div in divs]
    # print(round_pars)
    return round_pars

def compute_scores(row, pars):
    scores = row['hole_scores']
    results = count_scores(pars, scores)
    row['aces'] = results['aces']
    row['eagles+'] = results['eagles+']
    row['birdies'] = results['birdies']
    row['pars'] = results['pars']
    row['bogeys'] = results['bogeys']
    row['doubles+'] = results['doubles+']
    return row.drop('hole_scores')

def main(event_id:str, n_rounds:int, round:int):
    dfs = []
    for round in range(1, n_rounds+1):
        print(f'getting round: {round}')
        html = get_udisc_html(event, round)
        round_results = get_round_table(html)
        round_pars = get_round_pars(html)
        tallies = round_results.apply(compute_scores, axis=1, pars=round_pars)
        tallies['round'] = round
        tallies['tournament'] = event_id
        # print(tallies)
        dfs.append(tallies)
    tournament_df = pd.concat(dfs)

    totals = tournament_df.groupby(['name', 'tournament']).agg({'aces': 'sum', 
                                                'eagles+': 'sum', 
                                                'birdies': 'sum', 
                                                'pars': 'sum', 
                                                'bogeys': 'sum', 
                                                'doubles+': 'sum',
                                                'total': 'first',
                                                'place': 'first'})
    totals = totals.sort_values('place').reset_index()
    cols = ['name', 'tournament', 'total', 'place', 'aces', 'eagles+', 'birdies', 'pars', 'bogeys', 'doubles+']
    totals = totals[cols]


    print(totals)
    totals.to_csv(f'./data/tournaments/2023/{event_id}_results.csv', index=False)

if __name__ == "__main__":
    print('start...')
    event = 'lvc2022'
    n_rounds = 4

    main(event, n_rounds, round)

