import argparse
import sys

def command_args():
    parser = argparse.ArgumentParser('cli tool for dg scraper.')
    parser.add_argument('--env',
                        type=str,
                        default='dev',
                        choices=['dev','prod']
                        )
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
    parser.add_argument('--live',
                        action='store_true',
                        help='include to run udisc scraper every 5 mins until 8pm est'
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
    parser.add_argument('--curr_round',
                        type=int,
                        required=False)
    args = parser.parse_args()

    if not args.players and not args.tournament and not args.live_tournament:
        raise Exception('must enter either --players or --tournament')
    if args.live and not args.curr_round:
        raise Exception('must provide curr round if running live scores')
    if not args.live:
        args.curr_round = 1
    if args.env == 'dev':
        args.env_suffix = '_DEV'
    else:
        args.env_suffix = ''

    return args