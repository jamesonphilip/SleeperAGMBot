# --- Sleeper Dynasty Assistant GM ---

import streamlit as st
import requests
import pandas as pd
import json
from bs4 import BeautifulSoup
import lxml

# --- Configuration ---
DEEPSEEK_API_KEY = "sk-efec2ddcafba46ff949e25dad349a0c2"

# --- Sleeper API Functions ---
def get_user_id(username):
    url = f"https://api.sleeper.app/v1/user/{username}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("user_id")
    return None

def get_leagues(user_id, season):
    url = f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/{season}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def get_league_settings(league_id):
    url = f"https://api.sleeper.app/v1/league/{league_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def get_rosters(league_id):
    url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def get_players():
    url = "https://api.sleeper.app/v1/players/nfl"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def get_draft_picks(league_id):
    url = f"https://api.sleeper.app/v1/league/{league_id}/traded_picks"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []

# --- Dynasty Rankings Scraper ---
def get_dynasty_rankings():
    response = requests.get("https://www.fantasypros.com/nfl/rankings/dynasty-overall.php")
    soup = BeautifulSoup(response.content, "lxml")
    rankings = {}
    table = soup.find("table", {"id": "rank-data"})
    if table:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3:
                player_name = cols[1].get_text(strip=True)
                rank = cols[0].get_text(strip=True)
                rankings[player_name] = int(rank)
    return rankings

def find_dynasty_rank(player_name, rankings):
    return rankings.get(player_name, "N/A")

def estimate_trade_value(dynasty_rank):
    if dynasty_rank == "N/A":
        return "N/A"
    if dynasty_rank <= 5:
        return 7000
    elif dynasty_rank <= 15:
        return 6500
    elif dynasty_rank <= 30:
        return 6000
    elif dynasty_rank <= 50:
        return 5500
    else:
        return 4000

# --- Dynasty Rookie Scraper ---
def get_rookie_names():
    rookie_url = "https://www.fantasypros.com/nfl/rankings/dynasty-rookies.php"
    response = requests.get(rookie_url)
    soup = BeautifulSoup(response.content, "lxml")
    rookie_names = []
    table = soup.find("table", {"id": "rank-data"})
    if table:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                player_name = cols[1].get_text(strip=True)
                rookie_names.append(player_name)
    return rookie_names

# --- DeepSeek Generic Analyzer ---
def analyze_with_deepseek(prompt):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            st.error(f"DeepSeek Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        st.error(f"DeepSeek Connection Error: {e}")
        return None

# --- Waiver Wire Helpers ---

def get_free_agents(players_data, league_owned_players, rookie_names, dynasty_rankings):
    """Find available free agents with dynasty rank info."""
    free_agents = []
    for pid, pdata in players_data.items():
        player_name = pdata.get("full_name", "Unknown")
        if player_name != "Unknown" and pid not in league_owned_players:
            free_agents.append({
                "Name": player_name,
                "Position": pdata.get("position", "UNK"),
                "NFL Team": pdata.get("team", "UNK"),
                "Age": pdata.get("age", "UNK"),
                "Dynasty Rank": find_dynasty_rank(player_name, dynasty_rankings),
                "Rookie": player_name in rookie_names
            })
    free_agents = [fa for fa in free_agents if isinstance(fa["Dynasty Rank"], int)]
    free_agents = sorted(free_agents, key=lambda x: x["Dynasty Rank"])
    return free_agents

def build_waiver_prompt_v2(starters_list, bench_list, free_agents):
    """Create an AI prompt that lets DeepSeek detect weaknesses and suggest best free agents."""
    short_list = free_agents[:30]

    prompt = f"""
You are helping a Dynasty fantasy football manager improve their roster via waiver wire pickups.

Here is the user's current roster:

**Starters:**
{json.dumps(starters_list, indent=2)}

**Bench:**
{json.dumps(bench_list, indent=2)}

Here are the available free agents in the league (sorted by dynasty value):

{json.dumps(short_list, indent=2)}

Instructions:
1. Analyze the user's current team positional strengths and weaknesses
2. Identify the 10 best available free agents that would improve their roster
3. For each recommendation, include:
    - Player Name
    - Position
    - Short 1-2 sentence justification why they fit (based on team need, upside, roster balance, dynasty value)
4. Format cleanly in a markdown table: Rank | Player | Pos | Justification
"""

    return prompt

# --- Streamlit App UI ---

st.set_page_config(page_title="Sleeper Dynasty Assistant GM", layout="wide")
st.title("🏈 Sleeper Dynasty Assistant GM")

username = st.text_input("Enter your Sleeper Username:")
season = st.number_input("Enter Season (e.g., 2025):", value=2025, step=1)

if username and season:
    with st.spinner(f"Fetching leagues for {username} ({season})..."):
        user_id = get_user_id(username)
        if not user_id:
            st.error("Couldn't find user ID. Check the username.")
            st.stop()

        leagues = get_leagues(user_id, season)
        if not leagues:
            st.error("No leagues found for this user/season.")
            st.stop()

        league_names = [l.get("name", "Unnamed League") for l in leagues]
        selected_league = st.selectbox("Choose your league:", league_names)
        league = next(l for l in leagues if l.get("name") == selected_league)
        league_id = league.get("league_id")

    with st.spinner(f"Fetching data for league: {selected_league}..."):
        league_settings = get_league_settings(league_id)
        rosters = get_rosters(league_id)
        players_data = get_players()
        dynasty_rankings = get_dynasty_rankings()
        rookie_names = get_rookie_names()

        if not (league_settings and rosters and players_data):
            st.error("Couldn't load full league data.")
            st.stop()

        # Build league owned players
        league_owned_players = set()
        for roster in rosters:
            for pid in roster.get('players', []):
                league_owned_players.add(pid)

        # Get your roster
        user_roster = None
        for roster in rosters:
            if roster.get("owner_id") == user_id:
                user_roster = roster
                break

        if not user_roster:
            st.error("Couldn't find your roster.")
            st.stop()

        record = f"{user_roster.get('settings', {}).get('wins', 0)}-{user_roster.get('settings', {}).get('losses', 0)}"
        points_for = user_roster.get('settings', {}).get('fpts', 0)

        # Build starters, bench, rookies
        starters_list = []
        bench_list = []
        available_rookies = []

        for pid in user_roster.get('starters', []):
            p = players_data.get(pid, {})
            starters_list.append({
                "Name": p.get("full_name", "Unknown"),
                "Position": p.get("position", "UNK"),
                "NFL Team": p.get("team", "UNK"),
                "Age": p.get("age", "UNK"),
                "Dynasty Rank": find_dynasty_rank(p.get("full_name", ""), dynasty_rankings),
                "Trade Value": estimate_trade_value(find_dynasty_rank(p.get("full_name", ""), dynasty_rankings))
            })

        for pid in user_roster.get('players', []):
            if pid not in user_roster.get('starters', []):
                p = players_data.get(pid, {})
                bench_list.append({
                    "Name": p.get("full_name", "Unknown"),
                    "Position": p.get("position", "UNK"),
                    "NFL Team": p.get("team", "UNK"),
                    "Age": p.get("age", "UNK"),
                    "Dynasty Rank": find_dynasty_rank(p.get("full_name", ""), dynasty_rankings),
                    "Trade Value": estimate_trade_value(find_dynasty_rank(p.get("full_name", ""), dynasty_rankings))
                })

        for pid, pdata in players_data.items():
            player_name = pdata.get("full_name", "Unknown")
            if player_name in rookie_names and pid not in league_owned_players:
                available_rookies.append({
                    "Name": player_name,
                    "Position": pdata.get("position", "UNK"),
                    "NFL Team": pdata.get("team", "UNK"),
                    "Age": pdata.get("age", "UNK"),
                    "Dynasty Rank": find_dynasty_rank(player_name, dynasty_rankings),
                    "Trade Value": estimate_trade_value(find_dynasty_rank(player_name, dynasty_rankings))
                })

        starters_df = pd.DataFrame(starters_list)
        bench_df = pd.DataFrame(bench_list)
        rookies_df = pd.DataFrame(available_rookies)

        # --- Tabs Setup ---
        tab1, tab2, tab3 = st.tabs(["🧠 Team Analyzer", "🏆 League Info", "📈 Waiver Wire Targets"])

        # --- TEAM ANALYZER TAB ---
        with tab1:
            st.header("Your Team Overview")
            st.write(f"**Record:** {record} | **Points For:** {points_for}")

            st.subheader("⭐ Starters")
            st.dataframe(starters_df)

            st.subheader("📋 Bench")
            st.dataframe(bench_df)

            st.subheader(f"🎯 Available {season} Rookies (Not Rostered)")
            if not rookies_df.empty:
                st.dataframe(rookies_df)
            else:
                st.write("No available rookies found.")

            st.subheader("🧠 DeepSeek Dynasty Analysis")
            team_prompt = f"""
Analyze my fantasy football dynasty roster.

Starters:
{starters_list}

Bench:
{bench_list}

Available Rookies:
{available_rookies}

Provide:
- Strengths
- Weaknesses
- Rookie Draft Advice
- Trade Recommendations
- Dynasty Outlook
"""
            if st.button("Run Full Team Analysis"):
                with st.spinner("Analyzing with DeepSeek..."):
                    team_analysis = analyze_with_deepseek(team_prompt)
                    if team_analysis:
                        st.success("Analysis Ready!")
                        st.text_area("Team Analysis", value=team_analysis, height=400)
                    else:
                        st.error("DeepSeek analysis failed.")

        # --- LEAGUE INFO TAB ---
        with tab2:
            st.header("🏆 League Info Overview")
            league_info = {
                "League Name": selected_league,
                "Teams": league_settings.get("total_rosters", '?'),
                "Roster Positions": ", ".join(league_settings.get('roster_positions', [])),
            }
            st.table(pd.DataFrame(league_info.items(), columns=["Detail", "Value"]))

            st.subheader("Scoring Settings")
            scoring_settings = league_settings.get('scoring_settings', {})
            if scoring_settings:
                scoring_table = pd.DataFrame(scoring_settings.items(), columns=["Stat", "Points"])
                st.dataframe(scoring_table)

        # --- WAIVER WIRE AI TARGETS TAB ---
        with tab3:
            st.header("📈 AI-Powered Waiver Wire Targets")

            if st.button("🔍 Analyze Waiver Wire"):
                with st.spinner("Analyzing Free Agents with DeepSeek..."):
                    free_agents = get_free_agents(players_data, league_owned_players, rookie_names, dynasty_rankings)
                    waiver_prompt = build_waiver_prompt_v2(starters_list, bench_list, free_agents)
                    waiver_analysis = analyze_with_deepseek(waiver_prompt)

                    if waiver_analysis:
                        st.success("AI Waiver Wire Analysis Ready!")
                        st.text_area("Top 10 Waiver Recommendations", value=waiver_analysis, height=500)
                    else:
                        st.error("DeepSeek waiver analysis failed.")
