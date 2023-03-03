from src import cli
from src import players
from src import udisc_live
from src import gdrive
from src import projection
import pandas as pd
import datetime
import numpy as np


def main(args):

    if args.players:
        # get updated players df
        players_df = players.run()
        print(players_df.head())

        # get previous players list
        sheet='fantasy-disc-golf-2023'
        worksheet='players'
        client = gdrive.auth_gspread()
        df = gdrive.get_sheet_df(client, sheet, worksheet)
        print(df.head())
        
        # update
        merged = pd.merge(players_df, df, on=['udisc_name'], how='left')
        players_df['init_price'] = merged['init_price'].fillna(5).astype(int)
        players_df['ch_price']  = players_df['cur_price'] - players_df['init_price']
        players_df['updated'] = str(datetime.date.today())
        players_df = players_df.replace(np.nan, None)
        print(players_df.tail())
        print(players_df.describe())

        # replace google worksheet
        if args.update_gsheet:
            gdrive.replace_sheet(client, sheet, worksheet, data=players_df)

        
    if args.tournament:
        totals = udisc_live.run(args.tid, False)

        # bring in gsheet data
        sheet='fantasy-disc-golf-2023'
        worksheet = 'event_results_DEV'
        client = gdrive.auth_gspread()

        # get data (with formula results) from gsheet
        df = gdrive.get_sheet_df(client, sheet, worksheet)
        df = df[df['keep']==1].drop(columns=['keep'])
        df['points'] = df['points'].replace('#DIV/0!', None)
        df = df.drop(columns=['season', 'start', 'style'])
        print('\nhead of event_results sheet')
        print(df.head())

        # check if tourn exists in sheet 
        match_col = 'lookup'
        matching_rows = df[ df[ match_col].isin(totals[match_col]) ]
        if not matching_rows.empty:
            print('\nalready in sheet')
            print('updating whats there...')
            # replace rows with matches on lookup with new data
            for index, row in matching_rows.iterrows():
                df.loc[index, totals.columns] =  totals.loc[totals[match_col] == row[match_col]].iloc[0]  
            df = projection.run(df)

        else:
            print('\nnew tournament. adding to sheet')
            df = pd.concat([df, totals])

            df = projection.run(df)

        print('\nfinal df:')
        print(df)
        # replace google worksheet
        if args.update_gsheet:
            data_worksheet = 'event_results_data_DEV'
            gdrive.replace_sheet(client, sheet, data_worksheet, data=df)   



if __name__ == "__main__":
    args = cli.command_args()
    main(args)
