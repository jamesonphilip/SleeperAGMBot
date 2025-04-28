# --- Sleeper Dynasty Assistant GM ---

import streamlit as st
import requests
import pandas as pd
import json
from bs4 import BeautifulSoup
import lxml
from fpdf import FPDF

# --- FantasyPros Dynasty Rookie Rankings Scraper ---
def get_rookie_names():
    """Scrape FantasyPros Dynasty Rookie Rankings to get current rookie names."""
    rookie_url = "https://www.fantasypros.com/nfl/rankings/dynasty-rookies.php"
    response = requests.get(rookie_url)
    soup = BeautifulSoup(response.content, "lxml")
    rookie_names = []

    table = soup.find("table", {"id": "rank-data"})
    if table:
        rows = table.find_all("tr")[1:]  # Skip header
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                player_name = cols[1].get_text(strip=True)
                rookie_names.append(player_name)
    return rookie_names

# --- Configuration ---
DEEPSEEK_API_KEY = "sk-efec2ddcafba46ff949e25dad349a0c2"
FANTASYPROS_DYNASTY_RANKINGS_URL = "https://www.fantasypros.com/nfl/rankings/dynasty-overall.php"

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

def get_user_roster(rosters, user_id):
    for roster in rosters:
        if roster.get("owner_id") == user_id:
            return roster
    return None

# --- FantasyPros Dynasty Rankings Scraper ---
def get_dynasty_rankings():
    response = requests.get(FANTASYPROS_DYNASTY_RANKINGS_URL)
    soup = BeautifulSoup(response.content, "lxml")
    rankings = {}
    table = soup.find("table", {"id": "rank-data"})
    if table:
        rows = table.find_all("tr")[1:]  # Skip header
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3:
                player_name = cols[1].get_text(strip=True)
                rank = cols[0].get_text(strip=True)
                rankings[player_name] = int(rank)
    return rankings

def find_dynasty_rank(player_name, rankings):
    return rankings.get(player_name, "N/A")

# --- Trade Value Simulator ---
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

# --- DeepSeek AI Analyzer ---
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

# --- PDF Generator ---
def generate_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    
    max_width = 180  # Width limit to split words manually if needed

    for line in text.split('\n'):
        if len(line) > 100:
            # If line is too long, split manually every 80 characters
            words = [line[i:i+80] for i in range(0, len(line), 80)]
            for word in words:
                pdf.multi_cell(0, 10, word)
        else:
            pdf.multi_cell(0, 10, line)
    
    return pdf

# --- Dynasty Pick Helpers ---
def get_draft_picks(league_id):
    url = f"https://api.sleeper.app/v1/league/{league_id}/traded_picks"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []

def organize_picks(picks, user_id):
    user_picks = []
    for pick in picks:
        if pick.get("owner_id") == user_id:
            season = pick.get("season")
            round_num = pick.get("round")
            original_owner = pick.get("previous_owner_id", "")
            pick_label = f"{season} Round {round_num}"
            user_picks.append({
                "Label": pick_label,
                "Original Owner": original_owner
            })
    return user_picks

def get_team_display_name(roster, owner_id_lookup):
    metadata = roster.get("metadata") or {}
    team_name = metadata.get("team_name")
    if team_name:
        return team_name
    else:
        return owner_id_lookup.get(roster.get("owner_id"), f"Owner {roster.get('owner_id')[:6]}")

# --- Build Owner ID to Username Map ---
def build_owner_id_lookup(rosters):
    lookup = {}
    for roster in rosters:
        owner_id = roster.get("owner_id")
        if owner_id:
            metadata = roster.get("metadata") or {}
            username = metadata.get("nickname")
            if username:
                lookup[owner_id] = username
    return lookup

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
        user_roster = get_user_roster(rosters, user_id)

        if not (league_settings and rosters and players_data and user_roster):
            st.error("Couldn't load full league data.")
            st.stop()

        record = f"{user_roster.get('settings', {}).get('wins', 0)}-{user_roster.get('settings', {}).get('losses', 0)}"
        points_for = user_roster.get('settings', {}).get('fpts', 0)

        league_owned_players = set()
        for roster in rosters:
            for pid in roster.get('players', []):
                league_owned_players.add(pid)

        starters_list = []
        bench_list = []
        # --- Pull Rookie Names Dynamically ---
rookie_names = get_rookie_names()

available_rookies = []

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
            if pdata.get('rookie_year') == int(season) and pid not in league_owned_players:
                available_rookies.append({
                    "Name": pdata.get("full_name", "Unknown"),
                    "Position": pdata.get("position", "UNK"),
                    "NFL Team": pdata.get("team", "UNK"),
                    "Age": pdata.get("age", "UNK"),
                    "Dynasty Rank": find_dynasty_rank(pdata.get("full_name", ""), dynasty_rankings),
                    "Trade Value": estimate_trade_value(find_dynasty_rank(pdata.get("full_name", ""), dynasty_rankings))
                })

        starters_df = pd.DataFrame(starters_list)
        bench_df = pd.DataFrame(bench_list)
        rookies_df = pd.DataFrame(available_rookies)

        # --- Setup Tabs ---
        tab1, tab2, tab3 = st.tabs(["🧠 Team Analyzer", "🔄 Trade Analyzer", "🏆 League Info"])

        # --- TEAM ANALYZER TAB ---
        with tab1:
            st.header("Your Team Overview")
            st.write(f"**Record:** {record} | **Points For:** {points_for}")

            st.subheader("⭐ Starters (with Dynasty Rank & Trade Value)")
            st.dataframe(starters_df)

            st.subheader("📋 Bench (with Dynasty Rank & Trade Value)")
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

            Please provide:
            1. Team Strengths
            2. Weaknesses
            3. Rookie Draft Strategy
            4. Recommended Trades
            5. Dynasty Outlook
            """

            if st.button("🧠 Run Full Team Analysis"):
                with st.spinner("DeepSeek analyzing your team..."):
                    team_analysis = analyze_with_deepseek(team_prompt)
                    if team_analysis:
                        st.success("Team Analysis Ready!")
                        st.text_area("Full Team Analysis", value=team_analysis, height=400)
                        st.download_button("⬇️ Download Team Analysis as PDF", generate_pdf(team_analysis).output(dest='S').encode('latin1'), file_name="team_analysis.pdf", mime="application/pdf")
                    else:
                        st.error("DeepSeek analysis failed.")
        # --- TRADE ANALYZER TAB ---
        with tab2:
            st.header("🔄 Dynasty Trade Analyzer (Multi-Player + Picks)")

            picks_data = get_draft_picks(league_id)
            owner_id_lookup = build_owner_id_lookup(rosters)

            # Your Team A players + picks
            your_players = starters_list + bench_list
            your_player_names = sorted([p['Name'] for p in your_players if p['Name'] != "Unknown"])

            your_selected_players = st.multiselect("Select Your Players (Team A):", your_player_names)
            your_selected_players_full = [p for p in your_players if p['Name'] in your_selected_players]

            your_picks = organize_picks(picks_data, user_id)
            your_pick_labels = [p["Label"] for p in your_picks]
            your_selected_picks = st.multiselect("Select Your Picks (Team A):", your_pick_labels)

            # Opponent Team B
            other_teams = []
            for roster in rosters:
                if roster.get("owner_id") != user_id:
                    owner_id = roster.get("owner_id")
                    team_name = get_team_display_name(roster, owner_id_lookup)
                    other_teams.append({
                        "team_name": team_name,
                        "owner_id": owner_id,
                        "players": roster.get("players", [])
                    })

            team_b_selected = st.selectbox("Select Opponent Team (Team B):", [t["team_name"] for t in other_teams])
            team_b = next((t for t in other_teams if t["team_name"] == team_b_selected), None)

            # Opponent players + picks
            if team_b:
                team_b_owner_id = team_b["owner_id"]
                team_b_player_ids = team_b["players"]
                team_b_players = []
                for pid in team_b_player_ids:
                    p = players_data.get(pid, {})
                    team_b_players.append({
                        "Name": p.get("full_name", "Unknown"),
                        "Position": p.get("position", "UNK"),
                        "NFL Team": p.get("team", "UNK"),
                        "Age": p.get("age", "UNK"),
                        "Dynasty Rank": find_dynasty_rank(p.get("full_name", ""), dynasty_rankings),
                        "Trade Value": estimate_trade_value(find_dynasty_rank(p.get("full_name", ""), dynasty_rankings))
                    })

                team_b_player_names = sorted([p['Name'] for p in team_b_players if p['Name'] != "Unknown"])
                opponent_selected_players = st.multiselect("Select Their Players (Team B):", team_b_player_names)
                opponent_selected_players_full = [p for p in team_b_players if p['Name'] in opponent_selected_players]

                team_b_picks = organize_picks(picks_data, team_b_owner_id)
                team_b_pick_labels = [p["Label"] for p in team_b_picks]
                opponent_selected_picks = st.multiselect("Select Their Picks (Team B):", team_b_pick_labels)

                if your_selected_players_full or your_selected_picks or opponent_selected_players_full or opponent_selected_picks:
                    st.subheader("📊 Trade Package Summary")

                    your_package = pd.DataFrame({
                        "Asset": [p["Name"] for p in your_selected_players_full] + your_selected_picks,
                        "Type": ["Player"] * len(your_selected_players_full) + ["Pick"] * len(your_selected_picks),
                        "Trade Value": [p["Trade Value"] if isinstance(p["Trade Value"], int) else 0 for p in your_selected_players_full] + [500 for _ in your_selected_picks]
                    })

                    opponent_package = pd.DataFrame({
                        "Asset": [p["Name"] for p in opponent_selected_players_full] + opponent_selected_picks,
                        "Type": ["Player"] * len(opponent_selected_players_full) + ["Pick"] * len(opponent_selected_picks),
                        "Trade Value": [p["Trade Value"] if isinstance(p["Trade Value"], int) else 0 for p in opponent_selected_players_full] + [500 for _ in opponent_selected_picks]
                    })

                    st.write("**Your Package (Team A)**")
                    st.dataframe(your_package)

                    st.write("**Their Package (Team B)**")
                    st.dataframe(opponent_package)

                    total_your_value = your_package["Trade Value"].sum()
                    total_their_value = opponent_package["Trade Value"].sum()

                    st.metric(label="Total Trade Value", value=f"Your Side: {total_your_value} vs Their Side: {total_their_value}")

                    trade_prompt = f"""
                    Dynasty Trade Proposal:

                    Offering (Team A - You):
                    Players: {[p['Name'] for p in your_selected_players_full]}
                    Picks: {your_selected_picks}

                    Receiving (Team B - {team_b_selected}):
                    Players: {[p['Name'] for p in opponent_selected_players_full]}
                    Picks: {opponent_selected_picks}

                    Analyze if this is a fair trade, based on player value, pick value, position scarcity, age, and dynasty team context.
                    Provide recommendation:
                    - Accept
                    - Decline
                    - Depends on roster needs
                    """

                    if st.button("🤔 Analyze This Trade"):
                        with st.spinner("DeepSeek analyzing full trade..."):
                            trade_analysis = analyze_with_deepseek(trade_prompt)
                            if trade_analysis:
                                st.success("Trade Analysis Ready!")
                                st.text_area("Trade Analysis", value=trade_analysis, height=350)
                                st.download_button("⬇️ Download Trade Analysis as PDF", generate_pdf(trade_analysis).output(dest='S').encode('latin1'), file_name="trade_analysis.pdf", mime="application/pdf")
                            else:
                                st.error("DeepSeek trade analysis failed.")

        # --- LEAGUE INFO TAB ---
        with tab3:
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
