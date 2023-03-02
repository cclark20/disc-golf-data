from src import cli
from src import players
from src import udisc_live
from src import gdrive
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
        client = gdrive.auth_gspread()
        df = gdrive.get_sheet_df(client, sheet, 'players')
        print(df.head())
        
        # update
        merged = pd.merge(players_df, df, on=['udisc_name'], how='left')
        players_df['init_price'] = merged['init_price'].fillna(0).astype(int)
        players_df['ch_price']  = players_df['cur_price'] - players_df['init_price']
        players_df['updated'] = str(datetime.date.today())
        players_df = players_df.replace(np.nan, None)
        print(players_df.tail())

        # replace google worksheet
        if args.update_gsheet:
            gdrive.replace_sheet(client, sheet, 'players', data=players_df)

        
    if args.tournament:
        totals = udisc_live.run(args.tid, args.rounds, False)
        totals = totals.values.tolist()
        if args.update_gsheet:
            service = gdrive.authenticate()
            gdrive.append_to_sheet(service, totals)


if __name__ == "__main__":
    args = cli.command_args()
    main(args)
