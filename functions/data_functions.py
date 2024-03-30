import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials

NO_ROXZONE_LIST = ["2023 Stockholm_HYROX ELITE_Men", "2023 Stockholm_HYROX ELITE_Women"]
STATIONS = [
    "SkiErg",
    "Sled-Push",
    "Sled-Pull",
    "Burpee-Broad-Jump",
    "Row",
    "Farmers-Carry",
    "Lunges",
    "Wallballs"
]

# --- Data Loaders
def load_data(path):
    results = pd.read_csv(
        path,
        dtype={
            "desc": "string",
            "time_day": "string",
            "time": "string",
            "diff": "string",
            "fullname": "string",
            "age_class": "string",
            "start_no": "string",
            "event_id": "string",
            "season": "string"
        }
    )
    results = results.drop_duplicates()
    return results

def map_splits(results, no_rox_event_ids=NO_ROXZONE_LIST):
    # mapping
    split_mapping = {
        1: "Run-1",
        2: "Post-Run-1-Rox",
        3: "SkiErg",
        4: "Post-SkiErg-Rox",
        5: "Run-2",
        6: "Post-Run-2-Rox",
        7: "Sled-Push",
        8: "Post-Sled-Push-Rox",
        9: "Run-3",
        10: "Post-Run-3-Rox",
        11: "Sled-Pull",
        12: "Post-Sled-Pull-Rox",
        13: "Run-4",
        14: "Post-Run-4-Rox",
        15: "Burpee-Broad-Jump",
        16: "Post-Burpee-Broad-Jump-Rox",
        17: "Run-5",
        18: "Post-Run-5-Rox",
        19: "Row",
        20: "Post-Row-Rox",
        21: "Run-6",
        22: "Post-Run-6-Rox",
        23: "Farmers-Carry",
        24: "Post-Farmers-Carry-Rox",
        25: "Run-7",
        26: "Post-Run-7-Rox",
        27: "Lunges",
        28: "Post-Lunges-Rox",
        29: "Run-8",
        30: "Wallballs"
    }

    no_rox_split_mapping = {
        1: "Run-1",
        2: "SkiErg",
        3: "Run-2",
        4: "Sled-Push",
        5: "Run-3",
        6: "Sled-Pull",
        7: "Run-4",
        8: "Burpee-Broad-Jump",
        9: "Run-5",
        10: "Row",
        11: "Run-6",
        12: "Farmers-Carry",
        13: "Run-7",
        14: "Lunges",
        15: "Run-8",
        16: "Wallballs"
    }

    # Apply mapping
    results["split_num"] = results.groupby(["event_id", "race_person_id"]).cumcount()+1
    results["split_name"] = results.apply(
        lambda row: no_rox_split_mapping[row["split_num"]]
        if row["event_id"] in no_rox_event_ids 
        else split_mapping.get(row["split_num"], "Unknown"),
        axis=1
    )
    return results

def get_clean_results(path):
    results = load_data(path).drop_duplicates()

    # Race-Person ID
    results["race_person_id"] = results["event_id"] + "_" + results["fullname"] + results["start_no"]
    # Remove coutnry clean name
    results["clean_name"] = results["fullname"].str.split(" \(").str[0].str.strip()
    # Map splits
    results = map_splits(results)

    # Regular expression for matching "HH:MM:SS" format
    time_pattern = r"^[\d]{1,2}:[\d]{2}:[\d]{2}$"

    # Add an indicator column 'time_format_valid'
    # True if 'time' matches the "HH:MM:SS" format, False otherwise
    results["time_format_valid"] = results["time"].str.match(time_pattern)
    bad_race_data = (
        results[results["time_format_valid"] == False]
        ["race_person_id"]
        .drop_duplicates()
        .to_list()
    )
    print(f"Bad race data count: {len(bad_race_data)}")
    # Drop bad race data to create clean results
    clean_results = results[~results["race_person_id"].isin(bad_race_data)].reset_index(drop=True)
    # Get total seconds
    clean_results["total_seconds"] = pd.to_timedelta(clean_results["time"]).dt.total_seconds()
    # Get new time diff
    clean_results["split_seconds"] = (
        clean_results
        .groupby(["event_id", "fullname"])["total_seconds"]
        .diff()
    )
    clean_results["split_seconds"] = clean_results["split_seconds"].fillna(clean_results["total_seconds"])
    return clean_results

# --- Analysis Helpers
def get_elites_athletes(df):
    elites = (
        df[df["event_id"].str.contains("ELITE")]["clean_name"]
        .drop_duplicates()
        .to_list()
    )
    return elites

def percentile_rank(group):
    return (1 - group.rank(pct=True)) * 100

def convert_to_min_sec(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    sec = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{sec:02d}"

def get_race_finisher_df(clean_results, elite_athletes, stations=STATIONS):
    race_finisher_df = (
        clean_results[clean_results["split_name"]=="Wallballs"]
        .assign(
            sub_60=lambda df: df["total_seconds"] < (60*60),
            sub_65=lambda df: df["total_seconds"] < (65*60),
            sub_70=lambda df: df["total_seconds"] < (70*60),
            sub_75=lambda df: df["total_seconds"] < (75*60),
            sub_80=lambda df: df["total_seconds"] < (80*60),
            sub_85=lambda df: df["total_seconds"] < (85*60),
            sub_90=lambda df: df["total_seconds"] < (90*60),
            elite_athlete=lambda df: df["clean_name"].isin(elite_athletes)
        )
        [[
            "fullname",
            "clean_name",
            "age_class",
            "event_id",
            "race_person_id",
            "season",
            "total_seconds",
            "sub_60",
            "sub_65",
            "sub_70",
            "sub_75",
            "sub_80",
            "sub_85",
            "sub_90",
            "elite_athlete"
        ]]
        .reset_index(drop=True)
    )
    race_finishers = race_finisher_df["race_person_id"].drop_duplicates().to_list()

    race_wide_splits = (
        clean_results[clean_results["race_person_id"].isin(race_finishers)]
        [["race_person_id", "split_name", "split_seconds"]]
        .pivot(index="race_person_id", columns="split_name", values="split_seconds")
    )
    race_finisher_full = (
        pd.merge(race_finisher_df, race_wide_splits, on="race_person_id", how="left")
        .assign(
            total_run=lambda x: x.filter(regex=r"^Run-").sum(axis=1),
            total_rox_zone=lambda x: x.filter(like="Rox").sum(axis=1),
            total_station=lambda x: x.filter(items=stations).sum(axis=1),
            avg_run_all=lambda x: x.filter(regex=r"^Run-").mean(axis=1),
            avg_run_exclude_first=lambda x: x.filter(regex=r"^Run-(2|3|4|5|6|7)$").mean(axis=1),
            min_run_exclude_first=lambda x: x.filter(regex=r"^Run-(2|3|4|5|6|7)$").min(axis=1),
            max_run_exclude_first=lambda x: x.filter(regex=r"^Run-(2|3|4|5|6|7)$").max(axis=1)
        )
        .assign(total_run_and_rox=lambda x: x["total_run"] + x["total_rox_zone"])
        .assign(
            run_and_rox_pct=lambda x: x["total_run_and_rox"] / x["total_seconds"],
            station_pct=lambda x: x["total_station"] / x["total_seconds"],
            run_range_exclude_first=lambda x: x["max_run_exclude_first"] - x["min_run_exclude_first"],
            run_range_pct_exclude_first=lambda x: 
                (x["max_run_exclude_first"] - x["min_run_exclude_first"])
                / x["avg_run_exclude_first"]
        )
    )


    # Race Division
    race_finisher_full["event_name"] = race_finisher_full["event_id"].apply(lambda x: x.split("_")[0]) 
    race_finisher_full['race_division'] = np.where(
        race_finisher_full['event_id'].str.contains("PRO_Men"), 'Pro Men',
        np.where(race_finisher_full['event_id'].str.contains("ELITE_Men"), 'Elite Men',
        np.where(race_finisher_full['event_id'].str.contains("PRO_Women"), 'Pro Women',
        np.where(race_finisher_full['event_id'].str.contains("ELITE_Women"), 'Elite Women',
        np.where(race_finisher_full['event_id'].str.contains("HYROX_Men"), 'Open Men',
        np.where(race_finisher_full['event_id'].str.contains("HYROX_Women"), 'Open Women',
        'Unknown')))))
    )

    return race_finisher_full

def get_race_averages_df(race_finisher_df, group_cols=["event_name", "race_division", "sub_75"], stations=STATIONS):
    columns_to_average = [
        "total_seconds",
        "total_run",
        "total_station",
        "total_run_and_rox",
        "run_and_rox_pct",
        "avg_run_all",
        "avg_run_exclude_first",
        "run_range_exclude_first",
        "run_range_pct_exclude_first"
    ] + stations
    agg_dict = {col: "mean" for col in columns_to_average}
    agg_dict["race_person_id"] = "count"

    race_averages = (
        race_finisher_df
        .groupby(group_cols, as_index=False)
        .agg(agg_dict)
        .rename(
            columns = {"race_person_id":"total_racers"}
        )
    )

    for column in columns_to_average:
        if len(group_cols) > 1:
            race_averages[f"{column}_percentile"] = (
                race_averages
                .groupby(group_cols[1])[f"{column}"].transform(percentile_rank)
            )
        else:
            race_averages[f"{column}_percentile"] = (
                race_averages[f"{column}"].transform(percentile_rank)
            )

        race_averages[f"{column}_time"] = (
            race_averages[f"{column}"]
            .apply(convert_to_min_sec)
        )
    return race_averages

def get_final_race_average_df(race_averages, keep_percentiles=True, time_group=None):
    final_column_order = [
        "event_name",
        "total_racers",
        "total_seconds_time",
        "total_run_time",
        "total_station_time",
        "total_run_and_rox_time",
        "SkiErg_time",
        "Sled-Push_time",
        "Sled-Pull_time",
        "Burpee-Broad-Jump_time",
        "Row_time",
        "Farmers-Carry_time",
        "Lunges_time",
        "Wallballs_time",
        "total_seconds_percentile",
        "total_run_percentile",
        "total_station_percentile",
        "total_run_and_rox_percentile",
        "SkiErg_percentile",
        "Sled-Push_percentile",
        "Sled-Pull_percentile",
        "Burpee-Broad-Jump_percentile",
        "Row_percentile",
        "Farmers-Carry_percentile",
        "Lunges_percentile",
        "Wallballs_percentile"
    ]

    if not keep_percentiles:
        final_column_order = [col for col in final_column_order if "percentile" not in col]

    if time_group:
        final_column_order.append(time_group)
        race_averages = race_averages[race_averages[time_group]==True].reset_index(drop=True)

    final_df = race_averages[final_column_order]
    final_df.columns = [
        ' '.join(word.capitalize() for word in col.replace('_', ' ').replace('-', ' ').split()) for col in final_df.columns
    ]
    final_df = (
        round_float_columns(final_df)
        .rename(
            columns={
                "Total Seconds Time": "Total Time",
                "Total Seconds Percentile": "Total Time Percentile"
            }
        )
        .sort_values(by=["Total Time"], ascending=True)
    )
    
    return final_df

def get_final_ind_race_df(df, stations=STATIONS):
    percentile_cols = [
        "total_seconds",
        "total_run",
        "total_station",
        "total_run_and_rox",
        "run_and_rox_pct",
        "avg_run_all",
        "avg_run_exclude_first",
        "run_range_exclude_first",
        "run_range_pct_exclude_first"
    ] + stations

    for column in percentile_cols:
        df[f"{column}_percentile"] = (
            df[f"{column}"].transform(percentile_rank)
        )

        df[f"{column}_time"] = (
            df[f"{column}"]
            .apply(convert_to_min_sec)
        )

    # Col selection
    final_column_order = [
        "clean_name",
        "age_class",
        "event_name",
        "total_seconds_time",
        "total_run_time",
        "total_station_time",
        "total_run_and_rox_time",
        "SkiErg_time",
        "Sled-Push_time",
        "Sled-Pull_time",
        "Burpee-Broad-Jump_time",
        "Row_time",
        "Farmers-Carry_time",
        "Lunges_time",
        "Wallballs_time",
        "total_seconds_percentile",
        "total_run_percentile",
        "total_station_percentile",
        "total_run_and_rox_percentile",
        "SkiErg_percentile",
        "Sled-Push_percentile",
        "Sled-Pull_percentile",
        "Burpee-Broad-Jump_percentile",
        "Row_percentile",
        "Farmers-Carry_percentile",
        "Lunges_percentile",
        "Wallballs_percentile"
    ]
    df = (
        df[final_column_order]
        .rename(
            columns={
                "clean_name":"Name", 
                "total_seconds_time": "total_time",
                "total_seconds_percentile": "total_time_percentile"
            }
        )
        .sort_values(by=["total_time"], ascending=True)
    )
    df.columns = [' '.join(word.capitalize() for word in col.replace('_', ' ').replace('-', ' ').split()) for col in df.columns]
    df = round_float_columns(df)
    return df

def write_df_to_google_sheet(sheet_name, df, credentials_json, tab_name='Sheet1'):
    """
    Writes a pandas DataFrame to a specified Google Sheet and tab.
    
    Args:
    sheet_name: The name of the Google Sheet.
    df: The pandas DataFrame to write.
    credentials_json: Path to the JSON file with Google service account credentials.
    tab_name: The name of the tab within the Google Sheet where the data will be written (defaults to 'Sheet1').
    
    Returns:
    None
    """
    # Define the scope and authorize the client
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_json, scope)
    client = gspread.authorize(credentials)
    
    # Open the spreadsheet
    sheet = client.open(sheet_name)
    
    # Select the right tab or create it if it doesn't exist
    try:
        worksheet = sheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        worksheet = sheet.add_worksheet(title=tab_name, rows="100", cols="20")

    # Convert DataFrame to list of lists (including header)
    values = [df.columns.tolist()] + df.values.tolist()
    
    # Update the worksheet with values
    worksheet.clear()  # Clear existing values
    worksheet.update('A1', values)

def round_float_columns(df):
    """
    Rounds all float columns in the DataFrame to 0 decimal points.
    
    Args:
    df: The pandas DataFrame whose float columns are to be rounded.
    
    Returns:
    A new DataFrame with all float columns rounded to 0 decimal points.
    """
    # Create a new DataFrame to avoid modifying the original one
    rounded_df = df.copy()
    
    # Iterate through each column in the DataFrame
    for column in rounded_df.columns:
        # If the column is of float type, round it to 0 decimal points
        if rounded_df[column].dtype == 'float':
            rounded_df[column] = rounded_df[column].round(0).astype('int')
    return rounded_df
