import requests
import pandas as pd
import unidecode
pd.options.mode.chained_assignment = None  # default='warn'

def generate_player_list(min_rating = 1005):
    pdga = pd.DataFrame(columns = ['Name', 'PDGA #', 'Rating', 'Class', 'City', 'State/Prov', 'Country', 'Membership Status'])

    for i in list(range(50)):
        URL = f"https://www.pdga.com/players?FirstName=&LastName=&PDGANum=&Status=Current&Gender=M&Class=P&MemberType=All&City=&StateProv=All&Country=All&Country_1=All&UpdateDate=&order=Rating_1&sort=desc&page={i}"
        page = requests.get(URL)
        dfs = pd.read_html(page.text)
        results = dfs[0]
        
        pdga = pdga.append(results, ignore_index=True)

        if pdga.iloc[-1]['Rating'] <= min_rating:
            break
    
    pdga = pdga.drop(columns = ['Class','City','Membership Status'])
    pdga['Name'] = pdga['Name'].apply(unidecode.unidecode)
    return pdga

def generate_player_finishes(players_df, year=2021):
    year = year
    players_stats = players_df

    for i in range(len(players_stats)):
        try:
            URL = f"https://www.pdga.com/player/{players_stats['PDGA #'][i]}/stats/{year}"
            page = requests.get(URL)
            dfs = pd.read_html(page.text)
            player = dfs[1]
        except:
            continue
        try:
            # only DGPT, Majors, and no silver series
            # player = player.drop(columns = ["Points", "Prize", "Dates"])
            player = player[(player["Tournament"].str.contains("DGPT")) |
                            (player["Tier"] == "M") |
                            (player["Tier"] == "XM")]
            player = player[(player["Tournament"].str.contains("Silver Series") == False) &
                            (player["Tournament"].str.contains("Match Play") == False) &
                            (player["Tournament"].str.contains("DGPT Championship") == False)].reset_index(drop=True)

            for m in range(len(player["Tournament"])):
                if player["Tournament"][m] in players_stats:
                    players_stats.at[i, player["Tournament"][m]] = player["Place"][m]
                else:
                    players_stats[player["Tournament"][m]] = None
                    players_stats.at[i, player["Tournament"][m]] = player["Place"][m]
        except:
            continue

    # remove non US tournaments
    players_2 = players_stats.dropna(axis=1, thresh=5).reset_index(drop=True)

    # add descriptive stats
    players_2['avg_finish'] = players_2.iloc[:, 5:19].mean(axis=1).round(2)
    players_2['best_finish'] = players_2.iloc[:, 5:19].min(axis=1)
    players_2['worst_finish'] = players_2.iloc[:, 5:19].max(axis=1)
    players_2['sd'] = players_2.iloc[:, 5:19].std(axis=1).round(2)
    players_2['amt_played'] = players_2.iloc[:, 5:19].count(axis=1)

    colnames = ["Name", "PDGA #", "Rating", "Country", "avg_finish", "best_finish", "worst_finish", "sd", "amt_played"]
    players_2 = players_2[colnames]
    players_2.rename(columns={"PDGA #": 'pdga_no'}, inplace=True)
    return players_2

# function to get pdga world rankings
def generate_pdga_rankings():
    URL = "https://www.pdga.com/united-states-tour-ranking-open"
    page = requests.get(URL)
    dfs = pd.read_html(page.text)

    players = dfs[0].iloc[::2]
    players.columns= players.columns.str.lower()
    players['#'] = players['#'].astype(int)
    players['pdga_no'] = players['player'].str.split('#').str[-1].astype(int)
    players['Name'] = players['player'].str.split('.').str[0].str[:-2]
    players['Name'] = players['Name'].apply(unidecode.unidecode)
    players['events_rating'] = players['rating'].str.split(" ").str[1]
    players['avg_elite_result'] = players['elite'].str.split(" ").str[1]
    players['wins_count'] = players['wins'].str.split(" ").str[1]
    players['podiums_count'] = players['podium'].str.split(" ").str[1]
    players['topten_count'] = players['top 10'].str.split(" ").str[1]

    colnames = ["Name", "pdga_no", "events_rating", "avg_elite_result", "wins_count", "podiums_count", "topten_count", "avg"]
    players = players[colnames]
    return players

# udisc rankings
def generate_udisc_rankings():
    URL = "https://udisclive.com/world-rankings/mpo"
    page = requests.get(URL)
    udisc_dfs = pd.read_html(page.text)

    udisc = udisc_dfs[0]
    udisc.columns = udisc.columns.str.lower()
    udisc.rename(columns={"dominance index": "index", "playerclick rows to compare players": "player"}, inplace=True)
    udisc['rank'] = udisc['#'].str.split(' ').str[0].str.extract('(\d+)', expand=False).astype(int)
    udisc['index'] = udisc['index'].str.split(' ').str[0].astype(float)
    udisc['Name'] = udisc['player']
    udisc['Name'] = udisc['Name'].apply(unidecode.unidecode)

    udisc = udisc.iloc[:, 2:]
    return udisc

# join
def merge_dfs(prev_year, pdga, udisc):
    players_2 = prev_year
    pdga_rankings = pdga
    udisc=udisc

    pdga_merged = players_2.merge(pdga_rankings, on=['pdga_no'], how='left')
    pdga_merged.rename(columns={"Name_x":"Name"}, inplace=True)

    pdga_merged.replace(["Richard Wysocki","Eagle Wynne McMahon","Nathan Sexton","Benjamin Callaway"], 
                        ["Ricky Wysocki","Eagle McMahon","Nate Sexton","Ben Callaway"], inplace=True)

    total = pdga_merged.merge(udisc, on="Name", how='right')
    total = total.sort_values(by=['rank', 'avg', 'Rating', 'pdga_no'])

    bins = [0,4,9,19,100]
    labels = [4,3,2,1]
    total['tier'] = pd.cut(total['index'], bins=bins, labels=labels)

    cols = ["Name","pdga_no","tier","Rating","index","avg","avg_finish","amt_played","best_finish","worst_finish","sd","podiums_count","topten_count"]
    final_df = total[cols]
    final_df.rename(columns={"index":"udisc_index","avg":"pdga_rank","Rating":"current_rating"}, inplace=True)

    final_df['amt_played'] = final_df['amt_played'].fillna(0).astype(int)
    #anyone without pdga number is rated below 1000, which we dont want
    final_df = final_df[final_df['pdga_no'].notna()]
    final_df['pdga_no'] = final_df['pdga_no'].astype(int)
    return final_df

if __name__ == "__main__":
    print("Enter year you want player finishes from: ")
    year = int(input())
    print(f"Gathering {year}'s data...")

    print("getting current top golfers...")
    current = generate_player_list(1000)

    print(f"getting player finishes from {year}...")
    finishes = generate_player_finishes(current, year)

    print("getting pdga's rankings...")
    pdga_rankings = generate_pdga_rankings()

    print("getting udisc world rankings")
    udisc = generate_udisc_rankings()

    print("joining the data...")
    final = merge_dfs(finishes, pdga_rankings, udisc)

    print("sending to your data/ folder")
    current.to_csv("data/players/top_golfers.csv", index=False)
    finishes.to_csv(f"data/players/player_finishes_{year}.csv", index=False)
    final.to_csv(f"data/players/pdga_udisc_{year}_joined.csv", index=False)
