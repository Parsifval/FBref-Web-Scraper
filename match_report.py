import re
import requests
from time import sleep
from bs4 import BeautifulSoup

from config import leagues_match_report

def main():
    for league in leagues_match_report.items():
        league_urls = league[1]
        match_list = get_matches(league_urls)
        get_match_report(match_list)


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


def get_match_report(urls: list):
    for url in urls:
        req = requests.get(f"https://fbref.com{url}")
        comm = re.compile("<!--|-->")
        soup = BeautifulSoup(comm.sub("", req.text), 'lxml')
        score_box_divs = soup.find_all('div', class_='scorebox')
        team_stats_divs = soup.find_all('div', id='team_stats')

        for div in score_box_divs:
            scores = soup.find_all('div', class_='score')
            score_list = []
            for score in scores:
                score_list.append(score.getText())

            referee_div = div.find('strong', string='Officials').find_next_sibling('small')
            referee_span = referee_div.find('span') if referee_div else None
            referee = referee_span.getText()
            referee = referee.replace(" (Referee)", "")

            span = div.find('span', class_='venuetime')
            if span and 'data-venue-date' in span.attrs:
                venue_date = span['data-venue-date']
            else:
                venue_date = None

            teams_link = div.find('a', string=re.compile('Historical Head-to-Head'))
            if teams_link:
                teams = teams_link.text.split(' vs. ')
                if len(teams) == 2:  # Make sure we actually have two teams
                    home_team = teams[0]
                    opponent = teams[1].replace(' Historical Head-to-Head', '')  # Remove ' Historical Head-to-Head' from the second team's name
            else:
                home_team, opponent = None, None

        for div in team_stats_divs:
            strongs = div.find_all('strong')[:4]
            home_possession = strongs[0].getText()
            away_possession = strongs[1].getText()

        sub_dict = {
            "date": venue_date, "home_team": home_team, "away_team": opponent,
            "referee": referee, "home_possession": home_possession, "away_possession": away_possession
            }

        print(sub_dict)
        sleep(3)



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