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
from datetime import datetime
from tqdm import tqdm
pd.options.mode.chained_assignment = None  # default='warn'

from src import cost

def get_udisc_stats(name: str) -> str:
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
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(URL)
    time.sleep(5)
    html = driver.page_source

    soup = BeautifulSoup(html, 'html.parser')
    try:
        udisc_name = soup.select('h1')[0].text # the name is the only h1 element
        return udisc_name
    except IndexError as e:
        print(f"\n{name}: {e}")
        return name

def generate_player_list(min_rating: int) -> pd.DataFrame:
    # generate empty df with structure of incoming pdga tables (to concat to)
    pdga = pd.DataFrame(columns = ['Name', 'PDGA #', 'Rating', 'Class', 'City', 'State/Prov', 'Country', 'Membership Status'])

    tic = datetime.now()
    print(f'\ngetting all players above {min_rating}')
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
    pdga.columns = pdga.columns.str.lower()
    pdga.rename(columns={"pdga #": 'pdga_no'}, inplace=True)
    pdga.rename(columns={"rating": 'cur_rating'}, inplace=True)

    # manual changes
    pdga['udisc_name'] = pdga['name'].replace(
        {
        'Richard Wysocki': 'Ricky Wysocki',
        'Nathan Sexton': 'Nate Sexton',
        'Benjamin Callaway': 'Ben Callaway',
        'Jason Hebenheimer': 'Jake Hebenheimer',
        'Kevin Kiefer III': 'Kevin Kiefer',
        'Benjamin Stemen': 'Ben Stemen',
        'Steven Rico': 'Steve Rico',
        # 'Bartosz Kowalewski': 'Bart Kowalewski',
        'G.T. Hancock': 'GT Hancock',
        'Matt Thompson': 'Matthew Thompson',
        'Daniel Brooks-Wells': 'Dan Brooks-Wells',
        'John Willis II': 'John Willis',
        'DW Hass': 'D.W. Hass',
        ' Ⓗ': ''
        },
        regex=True
    )

    pdga['name'] = pdga['name'].apply(unidecode.unidecode)
    pdga['udisc_name'] = pdga['udisc_name'].apply(unidecode.unidecode)

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
    players['cur_pdga_rank'] = players['#'].str.split().str[0].astype(int)
    players['pdga_no'] = players['player'].str.split('#').str[-1].astype(int)
    players['name'] = players['player'].str.split('.').str[0].str[:-2]
    players['name'] = players['name'].apply(unidecode.unidecode)
    players['events_rating'] = players['rating'].str.split(" ").str[1]
    players['avg_elite_finish'] = players['elite'].str.split(" ").str[1]
    players['wins_count'] = players['wins'].str.split(" ").str[1].replace('·', 0).astype(int)
    players['podiums_count'] = players['podium'].str.split(" ").str[1].replace('·', 0).astype(int)
    players['topten_count'] = players['top 10'].str.split(" ").str[1].replace('·', 0).astype(int)

    colnames = ["pdga_no", "name", 'cur_pdga_rank', "events_rating", "avg_elite_finish", "wins_count", "podiums_count", "topten_count"]
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
    udisc['cur_udisc_rank'] = udisc['#'].str.split(' ').str[0].str.extract('(\d+)', expand=False).astype(int)
    udisc['cur_udisc_index'] = udisc['udisc_index'].str.split(' ').str[0].astype(float)
    udisc['name'] = udisc['name'].apply(unidecode.unidecode)

    colnames = ['name', 'cur_udisc_index', 'cur_udisc_rank']
    udisc = udisc[colnames]
    return udisc

# join
def merge_dfs(current, pdga, udisc):
    pdga_merged = current.merge(pdga, on=['pdga_no'], how='left')
    pdga_merged = pdga_merged.rename(columns={'name_x': 'name'}).drop(columns='name_y')

    total = pdga_merged.merge(udisc, left_on="udisc_name", right_on='name', how='outer') # we want the non matches from udisc
    total['udisc_name']=total['udisc_name'].fillna(total['name_y']) # move udisc names to our name column
    total = total.sort_values(by=['cur_udisc_rank', 'cur_pdga_rank', 'cur_rating', 'pdga_no'], ascending=[True, True, False, True], ignore_index=True)

    cols = ["udisc_name","pdga_no","cur_rating","cur_udisc_rank","cur_udisc_index","cur_pdga_rank"]
    final_df = total[cols]

    return final_df

def run(min_rating:int=990, save=False):
    print("generate_player_list...")
    current = generate_player_list(min_rating)
    print("generate_pdga_rankings...")
    pdga_rankings = generate_pdga_rankings()

    print("generate_udisc_rankings...")
    udisc = generate_udisc_rankings()

    print("merge_dfs...")
    final = merge_dfs(current, pdga_rankings, udisc)
    
    # calculate cost using exponential decay
    final['cur_price'] = cost.calc_cost(final['cur_udisc_index'].fillna(0), decay_rate=0.0175)
    final['cur_price'] = final['cur_price'].astype(int)
    
    if save:
        print("sending to your data/ folder")
        final.to_csv(f"./data/players_{min_rating}.csv", index=False)

    return final

if __name__ == "__main__":
    print("Enter year you want player finishes from: ")

    final = run(save=False)
    
