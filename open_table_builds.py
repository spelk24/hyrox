# --- Imports
from functions.data_functions import *
import gspread
from oauth2client.service_account import ServiceAccountCredentials
pd.set_option("display.precision", 2)
mens_path = "data/hyrox_results_open_Men.csv"
wommens_path = "data/hyrox_results_open_Women.csv"


# --- Clean Results & Elite Athletes
clean_results = pd.concat(
    [
        get_clean_results(mens_path),
        get_clean_results(wommens_path)
    ],
    ignore_index=True
)
elite_athletes = get_elites_athletes(clean_results)

# -- Race Finishers by Division
race_finisher_df = get_race_finisher_df(clean_results, elite_athletes)

# divisions
race_finishers_open_men = race_finisher_df[race_finisher_df["race_division"]=="Open Men"]
race_finishers_open_women = race_finisher_df[race_finisher_df["race_division"]=="Open Women"]

# --- Race Averages
race_averages_open_men = get_race_averages_df(race_finishers_open_men, group_cols=["event_name", "sub_90"])
race_averages_open_women = get_race_averages_df(race_finishers_open_women, group_cols=["event_name", "sub_90"])

# --- Final DFs
race_final_open_men = get_final_race_average_df(race_averages_open_men, time_group="sub_90")
race_final_open_women = get_final_race_average_df(race_averages_open_women, time_group="sub_90")

ind_final_open_men = get_final_ind_race_df(race_finishers_open_men)
ind_final_open_women = get_final_ind_race_df(race_finishers_open_women)

# --- Write DFs to Google
write_df_to_google_sheet(
    sheet_name="data_driven_hyrox_source", 
    df=race_final_open_men, 
    credentials_json="google_credentials.json",
    tab_name="Race-Open-Men"
)

write_df_to_google_sheet(
    sheet_name="data_driven_hyrox_source", 
    df=race_final_open_women, 
    credentials_json="google_credentials.json",
    tab_name="Race-Open-Women"
)

# Ind dfs
write_df_to_google_sheet(
    sheet_name="hyrox_open_individual", 
    df=ind_final_open_men, 
    credentials_json="google_credentials.json",
    tab_name="Ind-Open-Men"
)


write_df_to_google_sheet(
    sheet_name="hyrox_open_individual", 
    df=ind_final_open_women, 
    credentials_json="google_credentials.json",
    tab_name="Ind-Open-Women"
)
