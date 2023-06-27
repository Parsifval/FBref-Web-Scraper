import re
import os
import requests
import pandas as pd
from time import sleep
from config import leagues, seasons, stats
from bs4 import BeautifulSoup

def main():
    for league in leagues.items():
        league_url = league[1]
        player_list = get_players(league_url)
        print(f"{league[0]}: {len(player_list)} players found")
        for player in player_list.items():
            print(f"{player[0]} / {len(player_list)}: {player[1]['player_name']}")
            for stat in stats:
                player_name = player[1]['player_name']
                player_id = player[1]['player_id']
                matches = get_player_matches(player_id, player_name, stat)
                dict_to_write = {
                    "matches": matches,
                    "stat": stat,
                    "league": league[0],
                    "player": player_name,
                    "player_id": player_id
                    }

                write_to_pkl(dict_to_write)


def get_players(urls: list) -> dict:
    """
    Gets a list of players for a given league

    Args:
        url (str): URL associated with the list of players for a given league

    Returns:
        dict: Dictionary with index number, player's ID, and player's name

    Example:
        {0: {'player_name': 'Name', 'player_id': 'id'}}
    """
    dict_player_name_id = {}

    def is_new_player(player_name, player_id):
        return not any(
            player['player_name'] == player_name and player['player_id'] == player_id for player in dict_player_name_id.values()
            )

    for url in urls:
        req = get_request(url)
        comm = re.compile("<!--|-->") # Removes comments from HTML
        soup = BeautifulSoup(comm.sub("", req.text), 'lxml')
        td = soup.find_all('td')
        k = 0
        for cell in td:
            if cell.attrs['data-stat'] == 'player':
                player_name = cell.attrs['csk']
                player_id = cell.attrs['data-append-csv']

                if is_new_player(player_name, player_id):
                    dict_player_name_id[k] =  {
                        'player_name' : player_name,
                        'player_id' : player_id
                        }

                    k += 1

    return dict_player_name_id


def get_player_matches(id: str, player_name: str, stat: str) -> dict:
    """
    Takes a player ID and name and returns a dict of the corresponding player's games by
    year

    Args:
        id (str): Corresponding player's ID
        stat (str): Corresponsing FBRef stats page
        player_name (str): Corresponding player's name

    Returns:
        dict: Dictionary with year, game number, and the stats for that game

    Example:
        {"2023": {"0": { "aerials_lost": "0", "aerials_won": "1", ...}}}
    """
    dict_game_stats = {}
    for year in seasons:
        url = f"https://fbref.com/en/players/{id}/matchlogs/{year}/{stat}/"
        req = get_request(url=url)
        if req is None: # If get_request() cannot return response it will return a None value
            continue

        #print(f"Requesting match log for {year}: {req}")
        comm = re.compile("<!--|-->") # Removes comments from HTML
        soup = BeautifulSoup(comm.sub("",req.text), 'lxml')
        td = soup.find_all('td')
        tr = soup.find_all('th')

        year_game_stats = {}
        sub_dict = {}
        dates = []
        i = 0
        for row in tr: # Match date is not a table cell so needs to be parsed seperately
            if 'csk' in row.attrs:
                dates.append(row.attrs['csk'])

        for cell in td:
            sub_dict['player_name'] = player_name
            sub_dict[cell.attrs['data-stat']] = cell.getText()
            if cell.attrs['data-stat'] == 'match_report': # match_report is the last cell in each row
                if (sub_dict['result'] == '') and (sub_dict['team'] == ''):
                    sub_dict = {}
                    continue 
                
                if (len(dates) != i) and (len(dates) != 0):
                    sub_dict['game_date'] = dates[i]

                year_game_stats[i] = sub_dict
                sub_dict = {}
                i += 1

        sleep(3)
        dict_game_stats[year] = year_game_stats

    return dict_game_stats


def get_request(url: str):
    """
    Sends a GET request to a given URL

    Args:
        url (str): URL to which the get request is sent
    """
    retries = 0
    sleep_time = 3
    while retries < 5:
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error occurred: {e}")
        except requests.exceptions.Timeout as e:
            print(f"Timeout error occurred: {e}")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
        except Exception as e:
            print(f"An unknown error occurred: {e}")
        retries += 1
        sleep(sleep_time)
        sleep_time = sleep_time * 3
    
    print("Max retries reached")
    return None
    

def write_to_pkl(to_write: dict) -> None:
    """
    Takes a dictionary of matches and writes them to a .pkl file in their corresponding directory

    Args:
        to_write (dict): A dictionary containing the match data to be written to a .pkl file. The dictionary
                         should include keys for 'matches', 'stat', 'league', 'player', and 'player_id'.

    """
    df_dict = {}
    for index, (year, df) in enumerate(to_write["matches"].items()):
        data = pd.DataFrame.from_dict(df, 'index')
        df_dict[index] = data

    path = os.path.join(
        "Player-Data", to_write["stat"], to_write["league"], f"{to_write['player']}-{to_write['player_id']}.pkl"
        )

    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)

    complete_player_data = pd.concat(df_dict.values())
    complete_player_data.to_pickle(path)


if __name__ == '__main__':
    main()
