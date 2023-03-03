import os
import sys
import requests
import pandas as pd
import unidecode
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--window-size=835,3822")

import time
import re

def extract_int(string):
  if string == 'E': # even
    return int(0)
  if string == '(P)': # penalties added
    return int(1000)
  # find integer (with + or -) in string. if no digit, return None
  match = re.search(r'[+-]?\d+', string)
  if match:
    return int(match.group())
  else:
    return None


def count_scores(pars: int, scores: int) -> dict:
  results = {
    'aces': 0,
    'eagles+': 0,
    'birdies': 0,
    'pars': 0,
    'bogeys': 0,
    'doubles+': 0
  }
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


def get_udisc_html(udisc_id: str = 'usdgc2022', round: int = 1):
  URL = f"https://udisclive.com/live/{udisc_id}/{round}?t=scores&d=MPO"
  driver = webdriver.Chrome(options=chrome_options)
  driver.get(URL)
  time.sleep(5)
  html = driver.page_source
  soup = BeautifulSoup(html, 'html.parser')
  return soup

def get_registered_players(soup) -> pd.DataFrame:
  # <div style="display: inline-block; padding: 5px; text-align: left;">Paul McBeth</div>
  # <div style="display: inline-block; padding: 5px; text-align: left;">Paul McBeth</div>
  # <div style="display: inline-block; padding: 5px; text-align: left;">Billy Engel</div>
  # <div style="display: inline-flex; align-items: center; text-align: center; width: 260px; font-size: 20px; justify-content: flex-start; margin-bottom: 15px;"><a href="/players/paulmcbeth" style="display: flex; align-items: center;"><div style="width: 30px; height: 30px; color: rgb(255, 255, 255); display: inline-block; text-align: center; line-height: 40px; font-size: 24px; border-radius: 50%; left: 0px; user-select: none; background-image: url(&quot;https://dcaz3d51ftzmw.cloudfront.net/players/PaulMcBeth-Profile4.jpg&quot;); background-clip: border-box; background-size: contain; background-repeat: no-repeat; background-position: 50% 50%; flex-shrink: 0; margin-right: 5px;"></div><div style="display: inline-block; padding: 5px; text-align: left;">Paul McBeth</div></a></div>
  #             display: inline-flex; align-items: center; text-align: center; width: 260px; font-size: 20px; justify-content: flex-start; margin-bottom: 15px
  divs = soup.find_all(
    'div',
    attrs={
      'style': 'display: inline-flex; align-items: center; text-align: center; width: 260px; font-size: 20px; justify-content: flex-start; margin-bottom: 15px;'
    })
  # get registered players in events_result format
  names = [unidecode.unidecode(div.get_text()) for div in divs]

  # create df exactly as rest of script will expect, even though will be empty
  df = pd.DataFrame({
    'name': names,
    'place': None,
    'total': None,
    'round_score': None,
    'aces': None,
    'eagles+': None,
    'birdies':None,
    'pars':None,
    'bogeys':None,
    'doubles+':None
  })

  return df

def get_round_table(soup) -> pd.DataFrame:
  divs = soup.find_all(
    'div',
    attrs={
      'style':
      "border-top: 1px solid rgb(var(--color-divider)); font-size: 13px;"
    })
  divs2 = soup.find_all(
    'div',
    attrs={
      'style':
      "border-top: 1px solid rgb(var(--color-divider)); font-size: 10px;"
    })
  divs = divs + divs2

  # stop if tournamnet hasnt started
  if not divs:
    return None
  
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
    cells = [cell for cell in cells if not cell.find('div')
             ]  # remove cells that have more than one div
    cells = [cell for cell in cells
             if not cell.find('i')]  # remove cells that have an i element

    # get text based on place
    name = unidecode.unidecode(cells[1].get_text())
    place = extract_int(cells[0].get_text())
    total = extract_int(cells[2].get_text())
    round_score = extract_int(cells[4].get_text())
    hole_scores = [extract_int(cell.get_text()) for cell in cells[5:23]]

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

  return df


def get_round_pars(soup) -> list:
  divs = soup.find_all('div', attrs={'style': "font-weight: 500;"})
  round_pars = [extract_int(div.get_text()) for div in divs]
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


def run(event_id: str, save:bool=True):
  dfs = []
  print(f'getting {event_id}...')
  round = 1
  while True:
  # for round in range(1, n_rounds + 1):
    html = get_udisc_html(event_id, round)

    # will return None if tournament hasn't started
    round_results = get_round_table(html)

    # try to get round scores, custom exception will send to except, if tournamnet hasn't started
    if round_results is not None:
      print(f'getting round: {round}')
      round_pars = get_round_pars(html)
      try:
        tallies = round_results.apply(compute_scores, axis=1, pars=round_pars)
      except:
        print('either round hasnt happened yet or a playoff. stopping the loop')
        break
      tallies['round'] = round
      tallies['tournament'] = event_id

      # break while loop if new tallies are same as last round (finished)
      if round > 1:
        last_round = dfs[-1].drop(columns=['round'])
        if tallies.drop(columns='round').equals(last_round):
          print(f'nevermind.. round {round-1} was the final round')
          break
      
      print(tallies)
      dfs.append(tallies)
      round += 1
    
    else: 
      print('getting registered players')
      reg_players = get_registered_players(html)
      if len(reg_players) == 0:
        print('registration not open')
      
      reg_players['tournament']=event_id
      dfs.append(reg_players)
      break

  tournament_df = pd.concat(dfs)
  totals = tournament_df.groupby(['name', 'tournament']).agg({
    'aces': 'sum',
    'eagles+': 'sum',
    'birdies': 'sum',
    'pars': 'sum',
    'bogeys': 'sum',
    'doubles+': 'sum',
    'total': 'first',
    'place': 'first'
  })
  totals = totals.sort_values('place').reset_index()
  totals['lookup'] = totals['name'] + totals['tournament']
  totals['lookup'] = totals['lookup'].str.lower()
  cols = [
    'lookup', 'name', 'tournament', 'total', 'place', 'aces', 'eagles+', 'birdies',
    'pars', 'bogeys', 'doubles+'
  ]
  totals = totals[cols]

  if save:
    totals.to_csv(f'./data/{event_id}_results.csv', index=False)

  return totals


if __name__ == "__main__":
  print('start...')
  event = 'txstates2022'
  n_rounds = 3

  run(event, n_rounds, save=False)
