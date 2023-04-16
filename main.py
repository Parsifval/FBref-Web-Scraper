import re
import os
import requests
import pandas as pd
from time import sleep
from config import leagues
from bs4 import BeautifulSoup

def main() -> None:
    for league in leagues.items():
        print(f"{league[0]}")
        league_url = league[1]
        player_list = get_players(league_url)
        print(f"{len(player_list)} players found")
        for player in player_list.items():
            player_name = player[1]['player_name']
            player_id = player[1]['player_id']
            print(f"{player[0]} / {len(player_list)}: {player_name}")
            matches = get_player_matches(player_id, player_name)
            write_to_pkl(games=matches, league=league[0], player_name=player_name, player_id=player_id)

def get_players(url: str) -> dict:
    """
    Gets a list of players for a given league

    Args:
        url (str): URL associated with the list of players for a given league

    Returns:
        dict: Dictionary with index number, player's ID, and player's name

    Example:
        {0: {'player_name': 'Name', 'player_id': 'id'}}
    """
    req = get_request(url=url)
    print(f"Getting player list: {req}")
    comm = re.compile("<!--|-->") #Removes comments from HTML
    soup = BeautifulSoup(comm.sub("", req.text), 'lxml')
    td = soup.find_all('td')

    dict_player_name_id = {}
    k = 0
    for cell in td:
        if cell.attrs['data-stat'] == 'player':
            player_name = cell.attrs['csk']
            player_id = cell.attrs['data-append-csv']
            dict_player_name_id[k] = {'player_name' : player_name,
                                      'player_id' : player_id}
            k += 1

    return dict_player_name_id

def get_player_matches(id: str, player_name: str) -> dict:
    """
    Takes a player ID and name and returns a dict of the corresponding player's games by
    year

    Args:
        id (str): Corresponding player's ID
        player_name (str): Corresponding player's name

    Returns:
        dict: Dictionary with year, game number, and the stats for that game

    Example:
        {"2023": {"0": { "aerials_lost": "0", "aerials_won": "1", ...}}}
    """
    seasons = [
            '2023', #'2022', '2021', '2020', '2019', '2018', '2017',
           # '2016', '2015', '2014', '2013', '2012', '2011', '2010',
            ] #Which seasons to include

    dict_game_stats = {}
    for year in seasons:
        url = f"https://fbref.com/en/players/{id}/matchlogs/{year}/misc/"
        req = get_request(url=url)
        #print(f"Requesting match log for {year}: {req}")
        comm = re.compile("<!--|-->") #Removes comments from HTML
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

        sleep(4)
        dict_game_stats[year] = year_game_stats

    return dict_game_stats


def get_request(url: str) -> dict:
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
    return None


def write_to_pkl(games: dict, league: str, player_name: str, player_id: str) -> None:
    '''
    Takes dict of games converts them into pandas dataframes, adds them to
    dictionary, take the values from dict and adds them to list to then be
    concatenated by pd.concat and wrote to .pkl file
    '''
    df_dict = {}
    for index, (year, df) in enumerate(games.items()):
        data = pd.DataFrame.from_dict(df, 'index')
        df_dict[index] = data

    path = os.path.join("Player-Data", league, f"{player_name}-{player_id}.pkl")
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)

    complete_player_data = pd.concat(df_dict.values())
    complete_player_data.to_pickle(path)

if __name__ == '__main__':
    main()

