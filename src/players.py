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
pd.options.mode.chained_assignment = None  # default='warn'

def get_udisc_name(name: str) -> str:
    '''
    input is name as it is in column
    function opens the players udisc profile (if they have one) and returns the name udsic gives them.
    if they don't have a profile, it returns the name that was passed in

    The purpose is to get the names udisc uses, so that we can join on name.
    They don't provide pdga number in the world rankings, so we must join on name.

    The issue was that names could differ from pdga to udisc.
    Ex. Richard Wysocki (pdga) & Ricky Wysocki (udisc)
    '''
    lname = ''.join(name.split()).lower()
    URL = f"https://udisclive.com/players/{lname}"
    service = Service('./chromedriver')
    driver = webdriver.Chrome(service=service)
    driver.get(URL)
    time.sleep(5)
    html = driver.page_source

    soup = BeautifulSoup(html, 'html.parser')
    try:
        udisc_name = soup.select('h1')[0].text # the name is the only h1 element
        return udisc_name
    except IndexError as e:
        print(f"{name}: {e}")
        return name

def generate_player_list(min_rating: int) -> pd.DataFrame:
    # generate empty df with structure of incoming pdga tables (to concat to)
    pdga = pd.DataFrame(columns = ['Name', 'PDGA #', 'Rating', 'Class', 'City', 'State/Prov', 'Country', 'Membership Status'])

    tic = datetime.now()
    print(f'start: {tic}')
    page_num = 0
    while True:
        # get page_num of pdga players (active, M, sorted by rating)
        URL = f"https://www.pdga.com/players?FirstName=&LastName=&PDGANum=&Status=Current&Gender=M&Class=P&MemberType=All&City=&StateProv=All&Country=All&Country_1=All&UpdateDate=&order=Rating_1&sort=desc&page={page_num}"
        page = requests.get(URL)
        try:
            dfs = pd.read_html(page.text, flavor='lxml')
        except ValueError as e:
            print(page_num)
            print(e)

        results = dfs[0]

        pdga = pd.concat([pdga, results], ignore_index=True)
        # check if last player's rating is below the minimum
        if pdga.iloc[-1]['Rating'] < min_rating:
            # remove players below the min
            pdga = pdga[pdga['Rating'] >= min_rating].reset_index(drop=True)
            break

        # load next page
        page_num += 1
    toc = datetime.now()
    print(f'end: {toc}')
    diff = toc - tic
    print(f'Time elapsed: {diff}')

    # formatting
    pdga = pdga.drop(columns = ['Class','City','State/Prov','Membership Status'])
    pdga['Name'] = pdga['Name'].apply(unidecode.unidecode)
    pdga.columns = pdga.columns.str.lower()
    pdga.rename(columns={"pdga #": 'pdga_no'}, inplace=True)
    pdga.rename(columns={"rating": 'cur_rating'}, inplace=True)

    # get udisc_name for later joins
    tic = datetime.now()
    print(f'start: {tic}')
    for i in tqdm(range(len(pdga))):
        udisc_name = get_udisc_name(pdga['name'][i])
        pdga.loc[i, 'udisc_name'] = udisc_name
    toc = datetime.now()
    print(f'end: {toc}')
    diff = toc - tic
    print(f'Time elapsed: {diff}')

    return pdga


# function to get pdga world rankings
def generate_pdga_rankings():
    # get pdga tour rankings as a pd dataframe
    URL = "https://www.pdga.com/united-states-tour-ranking-open"
    page = requests.get(URL)
    dfs = pd.read_html(page.text, flavor='lxml')
    players = dfs[0].iloc[::2]

    # formatting
    players.columns= players.columns.str.lower()
    players['pdga_rank'] = players['#'].str.split().str[0].astype(int)
    players['pdga_no'] = players['player'].str.split('#').str[-1].astype(int)
    players['name'] = players['player'].str.split('.').str[0].str[:-2]
    players['name'] = players['name'].apply(unidecode.unidecode)
    players['events_rating'] = players['rating'].str.split(" ").str[1]
    players['avg_elite_finish'] = players['elite'].str.split(" ").str[1]
    players['wins_count'] = players['wins'].str.split(" ").str[1].replace('·', 0).astype(int)
    players['podiums_count'] = players['podium'].str.split(" ").str[1].replace('·', 0).astype(int)
    players['topten_count'] = players['top 10'].str.split(" ").str[1].replace('·', 0).astype(int)

    colnames = ["pdga_no", "name", 'pdga_rank', "events_rating", "avg_elite_finish", "wins_count", "podiums_count", "topten_count"]
    players = players[colnames]
    return players

# udisc rankings
def generate_udisc_rankings():
    # get udisc world rankings as a pandas df
    URL = "https://udisclive.com/world-rankings/mpo"
    page = requests.get(URL)
    udisc_dfs = pd.read_html(page.text, flavor='lxml')
    udisc = udisc_dfs[0]

    # formatting
    udisc.columns = udisc.columns.str.lower()
    udisc.rename(columns={"dominance index": "udisc_index", "playerclick rows to compare players": "name"}, inplace=True)
    udisc['udisc_rank'] = udisc['#'].str.split(' ').str[0].str.extract('(\d+)', expand=False).astype(int)
    udisc['udisc_index'] = udisc['udisc_index'].str.split(' ').str[0].astype(float)
    udisc['name'] = udisc['name'].apply(unidecode.unidecode)

    colnames = ['name', 'udisc_index', 'udisc_rank']
    udisc = udisc[colnames]
    return udisc

# join
def merge_dfs(prev_year, pdga, udisc):
    pdga_merged = prev_year.merge(pdga, on=['pdga_no'], how='left')
    pdga_merged = pdga_merged.rename(columns={'name_x': 'name'})
    
    total = pdga_merged.merge(udisc, left_on="udisc_name", right_on='name', how='left')
    total = total.sort_values(by=['udisc_rank', 'pdga_rank', 'pdga_no'])

    cols = ["udisc_name","pdga_no","cur_rating","udisc_rank","udisc_index","pdga_rank","avg_elite_finish","podiums_count","topten_count"]
    final_df = total[cols]

    return final_df

if __name__ == "__main__":
    print("Enter year you want player finishes from: ")
    year = 2022
    min_rating = 990
    data_dir = './data/players'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    print(f"Gathering {year}'s data...")

    if not os.path.isfile(f"{data_dir}/pdga_{year}_{min_rating}.csv") or ('rerun' in sys.argv):
        print("generate_player_list...")
        current = generate_player_list(min_rating)

        print(f"generate_player_finishes: {year}...")
        # current = generate_player_finishes(current, year)
        current.to_csv(f"{data_dir}/pdga_{year}_{min_rating}.csv", index=False)

    print("generate_pdga_rankings...")
    pdga_rankings = generate_pdga_rankings()

    print("generate_udisc_rankings...")
    udisc = generate_udisc_rankings()

    print("merge_dfs...")
    current = pd.read_csv(f"{data_dir}/pdga_{year}_{min_rating}.csv")
    final = merge_dfs(current, pdga_rankings, udisc)
    
    print("sending to your data/ folder")
    final.to_csv(f"{data_dir}/players_{year}_{min_rating}.csv", index=False)
