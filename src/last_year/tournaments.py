import requests
import pandas as pd
import unidecode

def get_tournament_data(eventId):
    try:
        eventId = eventId
        URL = f"https://www.pdga.com/tour/event/{eventId}"
        page = requests.get(URL)
        dfs = pd.read_html(page.text)
        results = dfs[1]
    except:
        return print("registration not open yet or invalid event id.")
    if "Par" not in results.columns:
        colnames = ["Name", "PDGA#", "Rating"]
        results = results[colnames].sort_values(by=['Rating', 'PDGA#', 'Name'], ascending=[False, True, True]).reset_index(drop=True)
    else:
        rd_cols = [i for i in results.columns if "Rd" in i or "Finals" in i]
        colnames = ["Name", "PDGA#", "Rating"]
        colnames.extend(rd_cols)
        colnames.extend(["Par","Place"])
        results = results[colnames].sort_values(by=['Place', 'Rating', 'PDGA#', 'Name'], ascending=[True, False, True, True]).reset_index(drop=True)
    
    
    results['Name'] = results['Name'].apply(unidecode.unidecode)
    results.replace(["Richard Wysocki","Eagle Wynne McMahon","Nathan Sexton","Benjamin Callaway"], 
                    ["Ricky Wysocki","Eagle McMahon","Nate Sexton","Ben Callaway"], inplace=True)

    if "Par" in dfs[1].columns:
        results['best_round'] = results.iloc[:,3:-3].min(axis=1).astype(int)

    results = results[results['PDGA#'].notna()]
    results['PDGA#'] = results['PDGA#'].astype(int)
    results['Rating'] = results['Rating'].astype(int)
    return results

if __name__ == "__main__":
    print("1: run for all 2022 tournaments.\n2: input custom event id.")
    selection = int(input())
    if selection == 2:
        print("Enter event id (in pdga url for event)")
        eventId = int(input())
        print("Enter a tournament name name_year: ")
        eventName = str(input()).lower().replace(" ","_")
        results = get_tournament_data(eventId)
        if results is not None:
                results.to_csv(f"data/tournaments/event_{eventName}_{eventId}.csv", index=False)
    else:
        tournaments = {"LVC":55580,
                "WACO":55582,
                "Texas_State":55583,
                "JBO":55584,
                "Champions_Cup":55451, 
                "DDO":55585,
                "OTB":55586,
                "PXO":55587,
                "Preserve":55588,
                "Idlewild":55589,
                "EO":56013,
                "DGLO":55590,
                "LIS":55591,
                "DMC":55592,
                "Worlds":55460,
                "GMC":55593,
                "MVP":55594,
                "USDGC":55454}
        i = 0
        for name, id in tournaments.items():
            i += 1
            print(f"Getting {name}'s data...")
            results = get_tournament_data(id)
            if results is not None:
                results.to_csv(f"data/tournaments/event_{i:02d}_{name}_{id}.csv", index=False)
