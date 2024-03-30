
# Setup -------------------------------------------------------------------

library(tidyverse)
library(lubridate)
library(ggtext)
library(ggrepel)
library(showtext)
library(scales)
font_add_google(name = "Sora", family = "Sora")
showtext_auto()
source("https://raw.githubusercontent.com/spelk24/Data-Viz/main/functions/theme_sp.R")
fl_path <- "../data/training_data/20240224-Fort Lauderdale, FL - Tracked Workouts.csv"
nice_path <- "../data/training_data/20240608-Nice, France - Tracked Workouts.csv"
data <- bind_rows(
  read.csv(fl_path) %>% mutate(block="20240224-Fort-Lauderdale"),
  read.csv(nice_path) %>% mutate(block="20240608-Nice")
)


digest_colors <- c(
  "#EBA63F", # Orange
  "#3CBCC3", # Light Blue
  "#438945", # Green
  "#E40C2B", # Red
  "#454389", # Purple
  "#134A71", # Dark Blue
  "#436489", # Pale blue
  "#e3d8b1", # Cream
  "#c7e9c0" # Light Green
)


# Data Prep ---------------------------------------------------------------

interval_runs <- data %>% 
  filter(Workout.Type == "Interval Run") %>% 
  filter(!str_detect(Workout.Plan, "Peloton")) %>% 
  filter(str_length(Pacing) > 20) %>% 
  mutate(
    Pacing = str_remove_all(Pacing, " "),
    Interval.Peak.HR = str_remove_all(Interval.Peak.HR, " "),
    Date = lubridate::as_date(Date, format = "%m/%d/%y")
  ) %>% 
  select(
    Date,
    Workout.Type,
    Workout.Plan,
    Pacing,
    Interval.Peak.HR,
    Notes
  )

paces <- interval_runs %>% 
  separate_rows(Pacing, sep = ",") %>%
  select(Date, Pacing) %>% 
  rename(interval_pace=Pacing) %>% 
  group_by(Date) %>% 
  mutate(interval_num = row_number()) %>% 
  ungroup()

heart_rate <- interval_runs %>% 
  separate_rows(Interval.Peak.HR, sep = ",") %>%
  select(Date, Interval.Peak.HR) %>% 
  rename(peak_hr=Interval.Peak.HR) %>% 
  group_by(Date) %>% 
  mutate(interval_num = row_number()) %>% 
  ungroup()

interval_run_long <- interval_runs %>% 
  select(Date, Workout.Plan) %>% 
  left_join(paces, by = c("Date")) %>% 
  left_join(heart_rate, by = c("Date", "interval_num")) %>% 
  mutate(
    minutes = as.integer(str_split(interval_pace, ":", simplify = T)[ ,1]) * 60,
    seconds = as.integer(str_split(interval_pace, ":", simplify = T)[ ,2]),
    interval_pace_seconds = minutes + seconds,
    peak_hr = as.integer(peak_hr),
    distance = str_extract(Workout.Plan, "\\d+m"),
    date_distance = paste(Date, distance, sep = " - ")
  )

interval_cycle <- interval_run_long %>% 
  distinct(distance, Date) %>% 
  group_by(distance) %>% 
  arrange(Date) %>% 
  mutate(cycle_number = row_number()) %>% 
  ungroup()
 
final_df <- interval_run_long %>% 
  left_join(interval_cycle, by = c("Date", "distance")) %>% 
  mutate(cycle_number = as.character(cycle_number))


# Viz ---------------------------------------------------------------------

# Heart Rate
ggplot(final_df) +
  geom_step(
    aes(
      x = interval_num,
      y = peak_hr,
      color = cycle_number
    )
  ) +
  facet_wrap(~distance) +
  theme_sp()

# Pace
ggplot(final_df) +
  geom_step(
    aes(
      x = interval_num,
      y = interval_pace_seconds,
      color = cycle_number
    )
  ) +
  facet_wrap(~distance) +
  theme_sp()
