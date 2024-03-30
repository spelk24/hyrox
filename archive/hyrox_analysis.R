library(tidyverse)
library(lubridate)
library(ggtext)
library(ggrepel)
library(showtext)
library(scales)
font_add_google(name = "Sora", family = "Sora")
showtext_auto()
source("https://raw.githubusercontent.com/spelk24/Data-Viz/main/functions/theme_sp.R")
data <- read.csv("data/hyrox_results.csv")

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

# BUILD DATASETS ---------------------------------------------------------------

# Define Split Names
clean_df <- data %>% 
  # Filter to Men's Pro Races
  filter(
    str_detect(event_id, "HYROX PRO_Men")
  ) %>% 
  # Bad Row Indicator
  mutate(
    bad_data = case_when(
      str_length(diff) > 6 ~ "Yes",
      TRUE ~ "No"
    )
  ) %>% 
  group_by(event_id, fullname) %>% 
  mutate(split_num = row_number()) %>% 
  ungroup() %>% 
  mutate(
    split_name = case_when(
      split_num == 1 ~ "Run-1",
      split_num == 2 ~ "Post-Run-1-Rox",
      split_num == 3 ~ "SkiErg",
      split_num == 4 ~ "Post-SkiErg-Rox",
      split_num == 5 ~ "Run-2",
      split_num == 6 ~ "Post-Run-2-Rox",
      split_num == 7 ~ "Sled-Push",
      split_num == 8 ~ "Post-Sled-Push-Rox",
      split_num == 9 ~ "Run-3",
      split_num == 10 ~ "Post-Run-3-Rox",
      split_num == 11 ~ "Sled-Pull",
      split_num == 12 ~ "Post-Sled-Pull-Rox",
      split_num == 13 ~ "Run-4",
      split_num == 14 ~ "Post-Run-4-Rox",
      split_num == 15 ~ "Burpee-Broad-Jump",
      split_num == 16 ~ "Post-Burpee-Broad-Jump-Rox",
      split_num == 17 ~ "Run-5",
      split_num == 18 ~ "Post-Run-5-Rox",
      split_num == 19 ~ "Row",
      split_num == 20 ~ "Post-Row-Rox",
      split_num == 21 ~ "Run-6",
      split_num == 22 ~ "Post-Run-6-Rox",
      split_num == 23 ~ "Farmers-Carry",
      split_num == 24 ~ "Post-Farmers-Carry-Rox",
      split_num == 25 ~ "Run-7",
      split_num == 26 ~ "Post-Run-7-Rox",
      split_num == 27 ~ "Lunges",
      split_num == 28 ~ "Post-Lunges-Rox",
      split_num == 29 ~ "Run-8",
      split_num == 30 ~ "Wall-Balls"
    ),
    split_name = factor(
      split_name,
      levels = c(
        "Run-1",
        "Post-Run-1-Rox",
        "SkiErg",
        "Post-SkiErg-Rox",
        "Run-2",
        "Post-Run-2-Rox",
        "Sled-Push",
        "Post-Sled-Push-Rox",
        "Run-3",
        "Post-Run-3-Rox",
        "Sled-Pull",
        "Post-Sled-Pull-Rox",
        "Run-4",
        "Post-Run-4-Rox",
        "Burpee-Broad-Jump",
        "Post-Burpee-Broad-Jump-Rox",
        "Run-5",
        "Post-Run-5-Rox",
        "Row",
        "Post-Row-Rox",
        "Run-6",
        "Post-Run-6-Rox",
        "Farmers-Carry",
        "Post-Farmers-Carry-Rox",
        "Run-7",
        "Post-Run-7-Rox",
        "Lunges",
        "Post-Lunges-Rox",
        "Run-8",
        "Wall-Balls"
      )
    ),
    minutes = as.integer(str_split(diff, ":", simplify = T)[,1]),
    seconds = as.integer(str_split(diff, ":", simplify = T)[,2]),
    total_seconds = (minutes*60)+seconds
  ) %>% 
  distinct()

# Summary Table by Race
race_summary = clean_df %>% 
  group_by(event_id, fullname) %>% 
  summarise(
    total = sum(total_seconds),
    .groups = "drop"
  ) %>% 
  mutate(
    min = floor(total/60),
    sec = round(((total/60) %% 1)*60),
    sec_char = ifelse(sec < 10, paste0("0", sec), sec),
    time = paste0(as.character(min), ":", as.character(sec_char))
  ) %>% 
  group_by(event_id) %>% 
  arrange(total) %>% 
  mutate(
    rk = row_number(),
    percentile = percent_rank(-total)
  ) %>% 
  ungroup() %>% 
  mutate(
    performance_group = factor(case_when(
      percentile >= .90 ~ "> 90th",
      percentile >= .75 ~ "75th-90th",
      percentile >= .50 ~ "50th-75th",
      percentile >= .25 ~ "25th-50th",
      TRUE ~ "0th-25th"
    ),
    levels = c(
      "> 90th",
      "75th-90th",
      "50th-75th",
      "25th-50th",
      "0th-25th"
    )
    ),
    podium = ifelse(rk <= 3, "Y", 'N')
  ) %>% 
  filter(percentile >= 0)

# Group Lookup
group_lookup <- race_summary %>%
  select(
    event_id,
    fullname,
    ov_performance_group = performance_group,
    ov_podium = podium,
    ov_rk = rk,
    ov_percentile = percentile
  )

# Event Summary
event_summary <- clean_df %>% 
  select(event_id, fullname, split_name, total_seconds) %>%
  group_by(event_id, split_name) %>% 
  arrange(total_seconds) %>% 
  mutate(
    split_rk = row_number(),
    percentile = percent_rank(-total_seconds)
  ) %>%
  ungroup() %>%
  mutate(
    min = floor(total_seconds/60),
    sec = round(((total_seconds/60) %% 1)*60),
    sec_char = ifelse(sec < 10, paste0("0", sec), sec),
    time = paste0(as.character(min), ":", as.character(sec_char))
  ) %>% 
  filter(percentile >= 0) %>% 
  select(!c(min, sec, sec_char)) %>% 
  left_join(group_lookup, by = c("event_id", "fullname"))

# GRAPHS ------------------------------------------------------------------

station_data <- event_summary %>% 
  filter(
    str_detect(event_id, "PRO_Men"),
    !str_detect(split_name, "Rox"),
    !str_detect(split_name, "Run"),
  ) %>% 
  filter(!is.na(ov_performance_group)) %>% 
  group_by(ov_performance_group, split_name) %>% 
  summarise(
    avg_percentile = mean(percentile),
    avg_time = mean(total_seconds),
    .groups = "drop"
  ) %>% 
  mutate(plot_time = as.POSIXct(avg_time, origin = "1970-01-01", tz = "UTC"))

run_data <- event_summary %>% 
  filter(
    str_detect(event_id, "PRO_Men"),
    !str_detect(split_name, "Rox"),
    str_detect(split_name, "Run"),
  ) %>% 
  filter(!is.na(ov_performance_group)) %>% 
  group_by(ov_performance_group, split_name) %>% 
  summarise(
    avg_percentile = mean(percentile),
    avg_time = mean(total_seconds),
    .groups = "drop"
  )

format_minutes_seconds <- function(seconds) {
  mins <- floor(seconds / 60)
  secs <- seconds %% 60
  sprintf("%02d:%02d", mins, secs)
}

# Station Mean Time - Sled Pull and Wallball standout
ggplot(station_data) +
  geom_line(
    aes(
      x = split_name,
      y = avg_time,
      color = ov_performance_group,
      group = ov_performance_group
    ),
  ) +
  scale_color_manual(values = digest_colors) +
  scale_x_discrete(
    expand = c(0,0)
  ) +
  scale_y_continuous(
    labels = format_minutes_seconds,
    breaks = c(0,120,240,360,480,600, 720)
  ) +
  labs(
    title = "Average Time in Stations by Performance Group (Pro Men)",
    subtitle = "Performance groups are determined by overall finish percentile"
  ) +
  theme_sp(
    title_family = "Sora",
    text_family = "Sora",
    plots_pane = T,
    base_size = 10,
    md = F
  ) +
  theme(
    plot.subtitle = element_text(size = 10),
    panel.grid.minor = element_blank(),
    axis.line = element_line(color = "#252525"),
    legend.position = "top",
    legend.text = element_text(size = 8, hjust = 0),
    legend.title = element_blank(),
    axis.title = element_blank(),
    axis.text.x = element_text(angle = 90, hjust = 1),
    axis.ticks = element_line(color = "#252525")
  )

# Run Mean Times - Top performers stay steady throughout
ggplot(run_data) +
  geom_line(
    aes(
      x = split_name,
      y = avg_time,
      color = ov_performance_group,
      group = ov_performance_group
    ),
  ) +
  scale_color_manual(values = digest_colors) +
  scale_x_discrete(
    expand = c(0,0)
  ) +
  scale_y_continuous(
    labels = format_minutes_seconds,
    breaks = c(0,120,240,360,480,600)
  ) +
  labs(
    title = "Average Time in Runs by Performance Group (Pro Men)",
    subtitle = "Performance groups are determined by overall finish percentile"
  ) +
  theme_sp(
    title_family = "Sora",
    text_family = "Sora",
    plots_pane = T,
    base_size = 10,
    md = F
  ) +
  theme(
    plot.subtitle = element_text(size = 10),
    panel.grid.minor = element_blank(),
    axis.line = element_line(color = "#252525"),
    legend.position = "top",
    legend.text = element_text(size = 8, hjust = 0),
    legend.title = element_blank(),
    axis.title = element_blank(),
    axis.text.x = element_text(angle = 90, hjust = 1),
    axis.ticks = element_line(color = "#252525")
  )


# Compare Event by Race ---------------------------------------------------

station_event_compare <- clean_df %>% 
  filter(
    #split_name == "Sled-Push",
    event_id %in% c(
      "2023 New York_HYROX PRO_Men",
      "2023 Rimini_HYROX PRO_Men",
      "2023 Sydney_HYROX PRO_Men"
    ),
    !str_detect(split_name, "Rox"),
    !str_detect(split_name, "Run")
  ) %>% 
  mutate(
    event_name = str_replace(
      event_id,
      "_HYROX PRO_Men",
      ""
    )
  )

avg_station <- station_event_compare %>% 
  group_by(event_name, split_name) %>% 
  summarise(avg_time = round(mean(total_seconds)), .groups = "drop")

ggplot(station_event_compare) +
  geom_jitter(
    aes(x = event_name, y = total_seconds, color = event_name),
    width = .2,
    alpha = .4,
    size= .9
  ) +
  # Avg Text
  geom_text_repel(
    data = avg_station,
    aes(
      x = event_name,
      y = avg_time,
      label = format_minutes_seconds(avg_time)
    ),
    color = "#252525",
    alpha = .9,
    min.segment.length = 0,
    size = 3,
    family = "Sora",
    lineheight = .8,
    box.padding = 0.5,
    segment.curvature = .1,
    segment.ncp = 3,
    segment.angle = 30,
    nudge_y = 0,
    nudge_x = .5
  ) +
  scale_y_continuous(
    labels = format_minutes_seconds
  ) +
  scale_color_manual(values = digest_colors) +
  facet_wrap(~split_name, scales = "free_y", nrow = 4) +
  labs(
    title = "All Station Comparison - 2023/34 Hyrox Season",
    subtitle = "MENS PRO",
    caption = "Data Source: results.hyrox.com"
  ) +
  theme_sp(
    title_family = "Sora",
    text_family = "Sora",
    plots_pane = T,
    base_size = 12,
    md = F
  ) +
  theme(
    plot.subtitle = element_text(size = 10),
    panel.grid.minor = element_blank(),
    axis.line = element_line(color = "#252525"),
    legend.position = "none",
    axis.title = element_blank(),
    #axis.text.x = element_text(angle = 90, hjust = 1),
    axis.ticks = element_line(color = "#252525")
  )


# SLED PULLS
station_event_compare <- clean_df %>% 
  filter(
    split_name == "Sled-Pull",
    event_id %in% c(
      "2023 New York_HYROX PRO_Men",
      "2023 Rimini_HYROX PRO_Men",
      "2023 Sydney_HYROX PRO_Men"
    )
  ) %>% 
  mutate(
    event_name = str_replace(
      event_id,
      "_HYROX PRO_Men",
      ""
    )
  )

avg_station <- station_event_compare %>% 
  group_by(event_name) %>% 
  summarise(avg_time = round(mean(total_seconds)), .groups = "drop")

ggplot(station_event_compare) +
  geom_jitter(
    aes(x = event_name, y = total_seconds, color = event_name),
    width = .2,
    alpha = .7
  ) +
  # Avg Text
  geom_text_repel(
    data = avg_station,
    aes(
      x = event_name,
      y = avg_time,
      label = format_minutes_seconds(avg_time)
    ),
    color = "#252525",
    alpha = .9,
    min.segment.length = 0,
    size = 5,
    family = "Sora",
    lineheight = .8,
    box.padding = 0.5,
    segment.curvature = 1,
    segment.ncp = 3,
    segment.angle = 30,
    nudge_y = 0,
    nudge_x = .5
  ) +
  scale_y_continuous(
    labels = format_minutes_seconds
  ) +
  scale_color_manual(values = digest_colors) +
  labs(
    title = "Sled Pull Comparison - 2023/34 Hyrox Season",
    subtitle = "MENS PRO",
    caption = "Data Source: results.hyrox.com"
  ) +
  theme_sp(
    title_family = "Sora",
    text_family = "Sora",
    plots_pane = T,
    base_size = 12,
    md = F
  ) +
  theme(
    plot.subtitle = element_text(size = 10),
    panel.grid.minor = element_blank(),
    axis.line = element_line(color = "#252525"),
    legend.position = "none",
    axis.title = element_blank(),
    #axis.text.x = element_text(angle = 90, hjust = 1),
    axis.ticks = element_line(color = "#252525")
  )
