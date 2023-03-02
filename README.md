# pdga-scraper
Scripts to scrape pdga and udisc live

## Setup
These scripts scrape dynamic websites (mainly udisclive.com). To do so, we need a web driver to work with `selenium`. It will execute the Javascript so that we can get the html info seen on the website. See this [link](https://www.geeksforgeeks.org/scrape-content-from-dynamic-websites/) for more info.

After downloading the driver, place at root level of this repo (code looks for it there), then install the necessary python packages:
```
pip install -r requirements.txt
```

## Usage
### Generate players csv
For now, the parameters are just set in the scripts themselves. For players.py, you can run for a specific year and for all players above a certain pdga rating.
```bash
python src/players.py
python src/players.py rerun # add rerun if you want to regenerate and override existing results. 
```

## Method
### Players
1. generate a list of players from the pdga site.
    - will only run if a csv with the set parameters does not exist in `./data/players/`
    - this step will ladd players from the pdga player list until it reaches players with ratings below the set minimum.
    - lastly, it scrapes the `udisclive.com` page for the given player to get their UDisc listed name
        - needed later on to join pdga and udisc df's
        - this is included here, because udisc uses the (all lowercase, no spaces) *PDGA* name of a player for the url of their player profiles.
    - the previous step takes time, so this df is written to a csv, to avoid rerunning each time.

2. generate pdga rankings
    - step 2 gets the full pdga rankings from https://www.pdga.com/united-states-tour-ranking-open
    - this adds some statistics and pdga's ranking for players. 

3. generate udisc world rankings
    - step 3 gets the UDisc world rankings from https://udisclive.com/world-rankings/mpo

4. join together
    - df 1 and 2 join easily on pdga number
    - that df can join to udisc, since we got the udisc name earlier
