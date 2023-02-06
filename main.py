import re
#import pprint
import requests
import pandas as pd
from time import sleep
from bs4 import BeautifulSoup

player_id_url = "https://fbref.com/en/comps/9/stats/Premier-League-Stats" # Base URL for Premier League

def main():
    player_list = get_players()
    print(f"{len(player_list)} players found")
    for player in player_list.items():
        player_name = player[1]['player_name']
        player_id = player[1]['player_id']
        print(f"{player[0]}: {player_name}")
        matches = get_player_matches(player_id, player_name)
        write_to_pkl(matches, player_name)
        

def get_players() -> 'dict':
    req = requests.get(player_id_url)
    print(f"Getting player list: {req}")
    comm = re.compile("<!--|-->") #Removes comments from HTML
    soup = BeautifulSoup(comm.sub("",req.text), 'lxml')
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

def get_player_matches(id: 'str', player_name: 'str') -> 'dict':
    '''
    Takes a player ID and returns a dict of the corresponding players games by
    year
    '''
    seasons = [
            '2023', '2022', '2021', '2020', '2019', '2018', '2017',
            '2016', '2015', '2014', '2013', '2012', '2011', '2010',
            ] #Which seasons to include

    dict_game_stats = {}
    for year in seasons:
        url = f"https://fbref.com/en/players/{id}/matchlogs/{year}/misc/"
        req = requests.get(url)
        print(f"Requesting match log for {year}: {req}")
        comm = re.compile("<!--|-->") #Removes comments from HTML
        soup = BeautifulSoup(comm.sub("",req.text), 'lxml')
        td = soup.find_all('td')
        tr = soup.find_all('th')

        year_game_stats = {}
        sub_dict = {}
        dates = []
        i = 0
        for row in tr: #Match date is not a table cell so needs to be parsed seperately
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

    #pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(dict_game_stats)
    return dict_game_stats

def write_to_pkl(games: 'dict', player_name: 'str'):
    '''
    Takes dict of games converts them into pandas dataframes then adds them to
    dictionary, take the values from dict and adds them to list to then be
    concatenated by pd.concat and wrote to .pkl file
    '''
    i = 0
    df_dict = {}
    for year in games:
        df = games[year]
        data = pd.DataFrame.from_dict(df, 'index')
        df_dict[i] = data
        i += 1
    
    df_list = []
    for value in df_dict.values():
        df_list.append(value)

    complete_player_data = pd.concat(df_list)
    complete_player_data.to_pickle(f"{player_name}.pkl")


if __name__ == '__main__':
    main()


