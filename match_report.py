import re
import os
import requests
import pandas as pd

from time import sleep
from bs4 import BeautifulSoup
from config import leagues_match_report

def main():
    for league in leagues_match_report.items():
        print(league[0])
        league_urls = league[1]
        match_list = get_matches(league_urls)
        write_to_pkl(match_list, league[0])
        

def get_matches(urls: list) -> dict:
    """
    Iterates over a list of URLs, makes GET requests to each URL, parses the HTML,
    and extracts links to match reports.
    """
    matches = {}
    for url in urls:
        req = get_request(url)
        req = requests.get(url)
        comm = re.compile("<!--|-->") # Not sure if this is necessary here
        soup = BeautifulSoup(comm.sub("", req.text), 'lxml')
        td = soup.find_all('td')

        k = 0
        sub_dict = {"Date": None, "Home": None, "Score": None, "Away": None, "Referee": None}
        for cell in td:
            if cell.attrs['data-stat'] == "home_team":
                a_tag = cell.find('a')
                if a_tag is not None:
                    sub_dict["Home"] = a_tag.text

            if cell.attrs['data-stat'] == "away_team":
                a_tag = cell.find('a')
                if a_tag is not None:
                    sub_dict["Away"] = a_tag.text

            if cell.attrs['data-stat'] == "score":
                a_tag = cell.find('a')
                if a_tag is not None:
                    sub_dict["Score"] = a_tag.text

            if cell.attrs['data-stat'] == "date":
                a_tag = cell.find('a')
                if a_tag is not None:
                    sub_dict["Date"] = a_tag.text
            
            if cell.attrs['data-stat'] == "referee":
                sub_dict["Referee"] = cell.text

            if all(sub_dict.values()):
                matches[k] = sub_dict
                k += 1
                sub_dict = {"Date": None, "Home": None, "Score": None, "Away": None, "Referee": None}

        sleep(3)
    
    return matches


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


def write_to_pkl(to_write: dict, league: str) -> None:
    data = pd.DataFrame(to_write.values())
    print(data.head())
    path = os.path.join("Match-Reports", f"{league}-match_reports.pkl")
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    data.to_pickle(path)


if __name__ == '__main__':
    main()