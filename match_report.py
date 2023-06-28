import re
import requests
from time import sleep
from bs4 import BeautifulSoup

from config import leagues_match_report

def main():
    for league in leagues_match_report.items():
        league_urls = league[1]
        match_list = get_matches(league_urls)


def get_matches(urls) -> list:
    url_list = []
    for url in urls:
        req = get_request(url)
        req = requests.get(url)
        comm = re.compile("<!--|-->")
        soup = BeautifulSoup(comm.sub("", req.text), 'lxml')
        td = soup.find_all('td')

        for cell in td:
            if cell.attrs['data-stat'] == "match_report":
                a_tag = cell.find('a')
                link = a_tag.get('href') if a_tag else None # Gets the href attribute from the <a> tag, if it exists
                if link is not None:
                    url_list.append(link)

    return url_list


def get_match_report(url):
    pass


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
    

if __name__ == '__main__':
    main()