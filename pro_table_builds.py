# --- Imports
from functions.data_functions import *
import gspread
from oauth2client.service_account import ServiceAccountCredentials
pd.set_option("display.precision", 2)
path = "data/hyrox_results_pro.csv"


# --- Clean Results & Elite Athletes
clean_results = get_clean_results(path)
elite_athletes = get_elites_athletes(clean_results)

# -- Race Finishers by Division
race_finisher_df = get_race_finisher_df(clean_results, elite_athletes)
# divisions
race_finishers_pro_men = race_finisher_df[race_finisher_df["race_division"]=="Pro Men"]
race_finishers_elite_men = race_finisher_df[race_finisher_df["race_division"]=="Elite Men"]
race_finishers_pro_women = race_finisher_df[race_finisher_df["race_division"]=="Pro Women"]
race_finishers_elite_women = race_finisher_df[race_finisher_df["race_division"]=="Elite Women"]

# --- Race Averages
race_averages_pro_men = get_race_averages_df(race_finishers_pro_men, group_cols=["event_name", "sub_75"])
race_averages_elite_men = get_race_averages_df(race_finishers_elite_men, group_cols=["event_name"])
race_averages_pro_women = get_race_averages_df(race_finishers_pro_women, group_cols=["event_name", "sub_85"])
race_averages_elite_women = get_race_averages_df(race_finishers_elite_women, group_cols=["event_name"])

# --- Final DFs
race_final_pro_men = get_final_race_average_df(race_averages_pro_men, time_group="sub_75")
race_final_elite_men = get_final_race_average_df(race_averages_elite_men, False)
race_final_pro_women = get_final_race_average_df(race_averages_pro_women, time_group="sub_85")
race_final_elite_women = get_final_race_average_df(race_averages_elite_women, False)

ind_final_pro_men = get_final_ind_race_df(race_finishers_pro_men)
ind_final_elite_men = get_final_ind_race_df(race_finishers_elite_men)
ind_final_pro_women = get_final_ind_race_df(race_finishers_pro_women)
ind_final_elite_women = get_final_ind_race_df(race_finishers_elite_women)

# --- Write DFs to Google
write_df_to_google_sheet(
    sheet_name="data_driven_hyrox_source", 
    df=race_final_pro_men, 
    credentials_json="google_credentials.json",
    tab_name="Race-Pro-Men"
)

write_df_to_google_sheet(
    sheet_name="data_driven_hyrox_source", 
    df=race_final_elite_men, 
    credentials_json="google_credentials.json",
    tab_name="Race-Elite-Men"
)

write_df_to_google_sheet(
    sheet_name="data_driven_hyrox_source", 
    df=race_final_pro_women, 
    credentials_json="google_credentials.json",
    tab_name="Race-Pro-Women"
)

write_df_to_google_sheet(
    sheet_name="data_driven_hyrox_source", 
    df=race_final_elite_women, 
    credentials_json="google_credentials.json",
    tab_name="Race-Elite-Women"
)

# Ind dfs
write_df_to_google_sheet(
    sheet_name="hyrox_pro_individual", 
    df=ind_final_pro_men, 
    credentials_json="google_credentials.json",
    tab_name="Ind-Pro-Men"
)

write_df_to_google_sheet(
    sheet_name="hyrox_pro_individual", 
    df=ind_final_elite_men, 
    credentials_json="google_credentials.json",
    tab_name="Ind-Elite-Men"
)

write_df_to_google_sheet(
    sheet_name="hyrox_pro_individual", 
    df=ind_final_pro_women, 
    credentials_json="google_credentials.json",
    tab_name="Ind-Pro-Women"
)

write_df_to_google_sheet(
    sheet_name="hyrox_pro_individual", 
    df=ind_final_elite_women, 
    credentials_json="google_credentials.json",
    tab_name="Ind-Elite-Women"
)