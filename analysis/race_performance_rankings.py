# ------------ Setup
import sys
from pathlib import Path
current_script_path = Path(__file__).parent
root_directory = current_script_path.parent
if str(root_directory) not in sys.path:
    sys.path.append(str(root_directory))

from functions.data_functions import (
    get_clean_results,
    get_elites_athletes,
    get_race_finisher_df
)
import pandas as pd
pd.set_option("display.precision", 2)

# ------------ Data Paths
results_path = "../data/hyrox_results_pro.csv"
event_path = "../data/hyrox_events.csv"

# ------------ Clean Results
clean_results = get_clean_results(results_path)
events = pd.read_csv(event_path)
race_finisher_df = get_race_finisher_df(clean_results, elite_athletes)
race_finishers_pro_men = (
    race_finisher_df[race_finisher_df["race_division"]
    .isin(["Pro Men", "Elite Men"])]
    .merge(
        events,
        how="left",
        left_on = ["event_name", "season"],
        right_on = ["Event Name", "season"]
    )
)

# ------------ ELO Data Prep
elo_prep_df = (
    race_finishers_pro_men[race_finishers_pro_men["sub_70"]]
    [["clean_name", "event_name", "Order", "elite", "total_seconds"]]
    .reset_index(drop=True)
    .sort_values("Order")
)

# Initialize Elo ratings for each athlete
initial_rating = 1500
ratings = elo_prep_df["clean_name"].unique()
ratings = pd.DataFrame(ratings, columns=["clean_name"])
ratings["elo_rating"] = initial_rating

# Generate pairwise matchups from each race
matchups = []

for event in elo_prep_df["event_name"].unique():
    event_df = elo_prep_df[elo_prep_df["event_name"] == event].sort_values("total_seconds")
    athletes = event_df["clean_name"].tolist()
    event_elite = event_df[event_df["event_name"] == event]["elite"].unique()[0]
    
    # Generate all pairwise matchups within this event
    for i in range(len(athletes)):
        for j in range(i+1, len(athletes)):
            winner = athletes[i]
            loser = athletes[j]
            matchups.append([winner, loser, event, event_elite])

matchups_df = pd.DataFrame(matchups, columns=["winner", "loser", "event_name", "event_elite"])

# --------- ELO Calculation
def calculate_expected_score(rating_a, rating_b):
    """
    Calculate the expected score (probability of winning) for A in a matchup of A vs. B.
    """
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def update_elo_ratings(winner_rating, loser_rating, event_elite):
    """
    Update Elo ratings for a single matchup.
    Returns the updated ratings as (new_winner_rating, new_loser_rating).
    """
    if event_elite == "Yes":
        k=32
    else:
        k=16

    expected_score_winner = calculate_expected_score(winner_rating, loser_rating)
    expected_score_loser = 1 - expected_score_winner
    
    # Actual scores: winner gets 1, loser gets 0
    actual_score_winner = 1
    actual_score_loser = 0
    
    # Update ratings
    new_winner_rating = winner_rating + k * (actual_score_winner - expected_score_winner)
    new_loser_rating = loser_rating + k * (actual_score_loser - expected_score_loser)
    
    return new_winner_rating, new_loser_rating

# Apply the update for each matchup
# Note: This is a simplified outline. Actual implementation will need to loop through matchups_df and update ratings.
# This would typically involve looking up the current ratings in the ratings dataframe, updating them, and then saving the new ratings back.

# Placeholder for demonstration - replace with actual implementation

# Since the actual loop through matchups_df involves updating the ratings DataFrame and depends on your specific data setup,
# you'll need to implement this part in your environment. Here's a pseudo-code outline of the steps involved:

for index, matchup in matchups_df.iterrows():
    # Lookup current ratings
    winner_rating = ratings.loc[ratings['clean_name'] == matchup['winner'], 'elo_rating'].values[0]
    loser_rating = ratings.loc[ratings['clean_name'] == matchup['loser'], 'elo_rating'].values[0]


    # Update ratings based on the matchup outcome
    new_winner_rating, new_loser_rating = update_elo_ratings(
        winner_rating,
        loser_rating,
        matchup["event_elite"]
    )
    
    # Save the updated ratings back to the ratings DataFrame
    ratings.loc[ratings['clean_name'] == matchup['winner'], 'elo_rating'] = new_winner_rating
    ratings.loc[ratings['clean_name'] == matchup['loser'], 'elo_rating'] = new_loser_rating

# Reminder: The actual implementation of the loop is necessary to update the ratings through all matchups.
