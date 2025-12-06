import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import os
from pymongo import MongoClient
import json

# Base URL
BASE_URL = "https://www.pro-football-reference.com"

# Headers to mimic browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


# Function to get soup object
def get_soup(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


# Function to get all teams
def get_teams():
    teams_url = f"{BASE_URL}/teams/"
    soup = get_soup(teams_url)
    if not soup:
        return []

    teams = []
    active_teams = soup.find('table', id='teams_active')
    if active_teams:
        for row in active_teams.find('tbody').find_all('tr'):
            team_cell = row.find('th', {'data-stat': 'team_name'})
            if team_cell and team_cell.find('a'):
                team_name = team_cell.text.strip()
                team_url = BASE_URL + team_cell.find('a')['href']
                teams.append((team_name, team_url))
    return teams


# Function to get team seasons
def get_team_seasons(team_url, years):
    seasons = []
    soup = get_soup(team_url)
    if not soup:
        return seasons

    team_table = soup.find('table', id='team_index')
    if team_table:
        for row in team_table.find('tbody').find_all('tr'):
            year_cell = row.find('th', {'data-stat': 'year_id'})
            if year_cell and year_cell.text.isdigit():
                year = int(year_cell.text)
                if year in years:
                    season_url = BASE_URL + year_cell.find('a')['href'] if year_cell.find('a') else None
                    if season_url:
                        seasons.append((year, season_url))
    return seasons


# Function to scrape team stats
def scrape_team_games(season_url, team_name, year):
    soup = get_soup(season_url)
    if not soup:
        return None
    games = []
    team_stats_table = soup.find('table', id='games')
    if team_stats_table:
        print(f"TEAM GAMES TABLE")
        for row in team_stats_table.find('tbody').find_all('tr'):
            game = {'team': team_name, 'year': year, 'season_url': season_url}
            for th_col in row.find_all('th'):
                if 'data-stat' in th_col.attrs:
                    stat_name = th_col['data-stat']
                    stat_value = th_col.text.strip()
                    print(f"Found Stat {stat_name} = {stat_value}")
                    game[stat_name] = stat_value
            for column in row.find_all('td'):
                if 'data-stat' in column.attrs:
                    stat_name = column['data-stat']
                    stat_value = column.text.strip()
                    print(f"Found Stat {stat_name} = {stat_value}")
                    game[stat_name] = stat_value
            games.append(game)
    return games


# Function to scrape player stats
def scrape_player_stats(season_url, team_name, year):

    soup = get_soup(season_url)
    if not soup:
        return []

    players = []
    roster_table = soup.find('table', id='roster')
    if roster_table:
        for row in roster_table.find('tbody').find_all('tr'):
            player = {'Team': team_name, 'Year': year}
            player_name = row.find('td', {'data-stat': 'player'}).text.strip()
            player['Player'] = player_name
            for cell in row.find_all('td'):
                stat_name = cell['data-stat']
                stat_value = cell.text.strip()
                player[stat_name] = stat_value
            players.append(player)
    return players


# Main function
def main():
    # Create output directory
    output_dir = "C:\\Users\\nluge\\4dd\\nfl_stats"
    os.makedirs(output_dir, exist_ok=True)

    # Get years (last 20 years from current year)
    current_year = datetime.now().year
    years = list(range(current_year - 2, current_year + 1))

    # Get all teams
    teams = get_teams()
    print(f"Found {len(teams)} teams")

    for team_name, team_url in teams:
        print(f"Processing {team_name} - {team_url}")

        seasons = get_team_seasons(team_url, years)

        all_games = []
        for year, season_url in seasons:
            print(f"  Scraping {team_name} - {year}")
            # Scrape team stats
            team_games = scrape_team_games(season_url, team_name, year)
            for game in team_games:
                print(f"game: {game}")
            all_games.append(team_games)
            time.sleep(1)

        with open(f"{output_dir}/{team_name}_games.json", 'w', encoding='utf-8') as f:
            json.dump(all_games, f, indent=2, ensure_ascii=False)



if __name__ == "__main__":
    main()