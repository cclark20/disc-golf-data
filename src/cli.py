import argparse
import sys

def command_args():
    parser = argparse.ArgumentParser('cli tool for dg scraper.')
    parser.add_argument('--players',
                        action='store_true',
                        help='flag to run update player list'
                        )
    parser.add_argument('--min_rating',
                        type=int,
                        required=False,
                        help='get all players rated above this value. Default=990'
                        )
    parser.add_argument('--tournament',
                        action='store_true',
                        help='flag to get tournamnet results'
                        )
    parser.add_argument('--tid',
                        required='--tournament' in sys.argv,
                        help='udisc name of tournament (from udisclive url)'
                        )
    parser.add_argument('--update_gsheet',
                        action='store_true',
                        help='include if udpating google sheet')
    parser.add_argument('--local_save',
                        action='store_true',
                        help='include to save locally.')
    parser.add_argument('--connected',
                        action='store_true',
                        help='include to bring in connected google sheet data.')
    args = parser.parse_args()

    if not args.players and not args.tournament:
        raise Exception('must enter either --players or --tournament')

    return args