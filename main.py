from src import cli
from src import players
from src import udisc_live
from src import gdrive
from src import projection
import pandas as pd
import datetime
import time
import numpy as np


def main(args):

    if args.players:
        # get updated players df
        players_df = players.run()
        print(players_df.head(20))

        if args.connected:
            # get previous players list
            sheet='fantasy-disc-golf-2023'
            worksheet=f'players{args.env_suffix}'
            client = gdrive.auth_gspread()
            df = gdrive.get_sheet_df(client, sheet, worksheet)
            print(f'\nIncoming player list')
            print(df.head(10))
            
            # update
            merged = pd.merge(players_df, df, on=['udisc_name'], how='left')
            players_df['prev_price'] = merged['cur_price_y'].fillna(5).astype(int) # get cur price from incoming df
            players_df['init_price'] = merged['init_price'].fillna(5).astype(int)
            players_df['week_ch_price']  = players_df['cur_price'] - players_df['prev_price']
            players_df['ovr_ch_price']  = players_df['cur_price'] - players_df['init_price']
            players_df['updated'] = str(datetime.date.today())
            players_df = players_df.replace(np.nan, None)
            # update column order
            cols = ['udisc_name', 'pdga_no', 'cur_rating', 'cur_udisc_rank', 'cur_udisc_index', 'cur_pdga_rank',
                    'init_price', 'ovr_ch_price',
                    'prev_price', 'week_ch_price',
                    'cur_price', 'updated']
            players_df=players_df[cols]

            print('\nupated player list')
            print(players_df.head(25))

            # replace google worksheet
            if args.update_gsheet:
                gdrive.replace_sheet(client, sheet, worksheet, data=players_df)

        
    if args.tournament:
        stop_time = datetime.datetime.now().replace(hour=20,minute=0,second=0) # stop at 8pm EST
        while datetime.datetime.now() < stop_time:
            totals = udisc_live.run(args.tid, False)

            if args.connected:
                # bring in gsheet data
                sheet='fantasy-disc-golf-2023'
                worksheet = f'event_results{args.env_suffix}'
                client = gdrive.auth_gspread()

                # get data (with formula results) from gsheet
                df = gdrive.get_sheet_df(client, sheet, worksheet)
                df = df[df['keep']==1].drop(columns=['keep'])
                df['points'] = df['points'].replace('#DIV/0!', None)
                df = df.drop(columns=['season', 'start', 'style', 'current price'])
                print('\nhead of event_results sheet')
                print(df.head())
                # remove current tourn so we can replace
                df = df[df['tournament'] != args.tid]
                df = pd.concat([df, totals])

                # run projections
                df = projection.run(df)

                df = df.sort_values(by=['tournament', 'place','projection', 'name'],
                                    ascending = [True, True, False, True])
                df = df.replace(np.nan, None)
                df['updated'] = str(datetime.date.today())
                print('\nfinal df:')
                print(df)
                print('\ntournament you ran for:')
                print(df[df['tournament']==args.tid])

                # save locally
                if args.local_save:
                    save_path = './data/event_results.csv'
                    df.to_csv(save_path, index=False)

                # replace google worksheet
                if args.update_gsheet:
                    data_worksheet = f'event_results_data{args.env_suffix}'
                    gdrive.replace_sheet(client, sheet, data_worksheet, data=df)  

            # stop if not live
            if not args.live:
                break

            # wait for 5 mins before continuing
            time.sleep(300)

if __name__ == "__main__":
    args = cli.command_args()
    main(args)
