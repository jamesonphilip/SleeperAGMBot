from espn_api.baseball import League
from datetime import datetime

# --- ESPN credentials and league/team info ---
league_id = 2052016760
team_id = 9
season = 2025

# --- These values are from your cookies ---
swid = "{9130D2A0-0297-4AE0-ABDA-6BE1A48BD011}"
espn_s2 = "AEB3dIp1zc%2BMmUr4z63ozXUDIVSbpHyaJEEfOGWN%2FNVSDtlcJKTQ3MKm%2FQsur%2Bd8IqIjlfAXlbrskiCYXe%2F9hIVfNNde7Alatw8xaYMjgTUXQiCL0K3jhAK5cxTLBafr6tBk6d%2F6%2FXLLfNibJiOVYzFBTSx1hvBgN3kbqtv5c63GIcaOFYgYplolSsPgr%2BdHxsR2ddFc9Nbkt3DUeKhHVR7QFhH9pOpycFfRT6CaUVf1ttFKYoXZEEGR9aODT88zFagg5isWojAuQiTPMOX7Nvy%2Fcss3xny5yjyrGk15BrE5vmqRWlRP5yyb%2FX0gWn8Lzl8%3D"

# --- Map ESPN slot IDs to position names ---
slot_map = {
    0: "C", 1: "1B", 2: "2B", 3: "3B", 4: "SS",
    5: "MI", 6: "CI", 7: "OF", 8: "OF", 9: "OF",
    10: "UTIL", 11: "P", 12: "P", 13: "P", 14: "P",
    15: "P", 16: "P", 17: "P", 18: "BN", 19: "IR",
    20: "IR+", 21: "NA", 22: "UTIL", 23: "SP", 24: "RP", 25: "BE"
}

# --- Connect to your fantasy baseball league ---
league = League(
    league_id=league_id,
    year=season,
    swid=swid,
    espn_s2=espn_s2
)

# --- Get your team ---
my_team = league.get_team_data(team_id)

# --- Get today's date for filtering ---
today = datetime.now().strftime('%Y-%m-%d')

# --- Print team and set initial empty lineup ---
print(f"Your team: {my_team.team_name}")
print("Optimizing your lineup for today...")

# --- Sort roster by slot for lineup positions ---
sorted_roster = sorted(my_team.roster, key=lambda p: p.lineupSlot)

import datetime

# Get today's date
today = datetime.date.today().strftime('%Y-%m-%d')  # Format it as 'YYYY-MM-DD'

# --- Filter out players not active today and rank by performance ---
optimal_lineup = {}
for player in sorted_roster:
    name = player.name
    lineup_slot = slot_map.get(player.lineupSlot, f"Slot {player.lineupSlot}")
    eligible = [slot_map.get(slot, f"Slot {slot}") for slot in player.eligibleSlots]

    # Print the player's attributes to understand its structure
    print(f"Player: {player.name}, Position: {player.position}, Projected Total Points: {player.projected_total_points}")  # Print all available attributes of the player
    
    # Check if the player has a schedule and print it
    if hasattr(player, 'schedule'):
        print(f"Schedule for {name}: {player.schedule}")  # Print the schedule if available

    if hasattr(player, 'schedule') and player.schedule:
        for game in player.schedule:
            if hasattr(game, 'date'):
                print(f"Player: {name}, Game Date: {game.date}, Today: {today}")  # Debugging print
                playing_today = game.date == today  # Compare date directly

                if playing_today:
                    optimal_lineup[lineup_slot] = name
                    break  # No need to check further games for this player

# --- Print the optimal lineup ---
if optimal_lineup:
    print("\nOptimal Lineup for Today:")
    for slot, player in optimal_lineup.items():
        print(f"{slot}: {player}")
else:
    print("\nNo players are scheduled to play today.")

