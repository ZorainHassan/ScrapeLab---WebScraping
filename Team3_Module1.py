# --------------------------------------------
# MODULE 1: Environment Setup & Configuration
# Member Name: Minh Anh Le
# Team 3: ScrapeLab
# ----------------------------------------------
#
#
# Research question:
#   "How has modern audience sentiment toward 2000s action movies
#    evolved over time, and which films maintain 'evergreen' appeal
#    for streaming platforms?"
#
# What this module does:
#   1. Import all required libraries
#   2. Configure and open a browser that can bypass Cloudflare’s bot detection on Letterboxd
#   3. Connect to Letterboxd’s 2000s action movie page and verify the connection is working.
#   4. Define project parameters (URLs, sample size, paths)
#   5. Prepare the output folders for the team
#
# After this module runs, the browser is open and verified.
# Module 2 will use it to scrape the actual movie data.
# ------------------------------------------------------------


# %% Part A: Import Libraries
# -----------------------------------------------
#
# Each library has a specific role in our scraping pipeline.


import undetected_chromedriver as uc   # Selenium that bypasses Cloudflare (unlike regular webdriver)
from bs4 import BeautifulSoup          # reads HTML structure to find movie data 
import pandas as pd                    # stores data in table format for easy export
import time                            # pauses between page loads to be polite
import random                          # picks random movies without human bias
import os                              # creates folders and checks file paths


# %% Part B: Open a Chrome Browser
# -------------------------------------------------
#
# We first tried using regular Selenium to open Chrome, but
# Cloudflare detected it was a script and the verification
# failed. The website would not load at all.
#
# So we switched to undetected_chromedriver, which removes
# the automation fingerprint that Cloudflare looks for. This
# way Cloudflare treats our browser as a regular visitor. 
# No login or CAPTCHA needed.


print("Opening Chrome browser (undetected mode)...")

# Create a blank settings object for Chrome
options = uc.ChromeOptions()    

# Open Chrome with those settings; "driver" is now our remote control
driver = uc.Chrome(options=options)
driver.maximize_window()

print("  Browser is open.")


# %% Part C: Connect to Letterboxd and Handle Cloudflare
# ------------------------------------------------------
#
# We load the first page to check if Cloudflare lets us through.
# While loading, we check if "Security check" or "Just a moment"
# appears in the source code, which means Cloudflare is still
# blocking us. If yes, we wait longer or solve it manually.
#
# Then we verify by checking if "film-poster" appears in the
# source code, which is the HTML element Letterboxd uses to
# display each action movie. If it's there, the page loaded
# and the connection is ready for Module 2.


print("\nStep 1: Connecting to Letterboxd")

base_url = "https://letterboxd.com/films/genre/action/decade/2000s/page/{}/"

# Load page 1 to trigger and pass the Cloudflare check
first_url = base_url.format(1)
print(f"\n  Loading first page: {first_url}")
print("  (Cloudflare check may take a few seconds...)")
driver.get(first_url)
time.sleep(8)

# Check: did Cloudflare let us through?
if "Just a moment" in driver.page_source or "Security check" in driver.page_source:  # driver.page_source grabs the full HTML of whatever is on screen right now
    print("  Cloudflare is still checking. Waiting 10 more seconds...")
    time.sleep(10)

# Verify the page loaded by checking for movie elements in the HTML
if "film-poster" in driver.page_source:           #"film-poster" appears in Letterboxd's page source code
    print("  Connection successful! Letterboxd is accessible.")
else:
    print("  WARNING: Page may not have loaded correctly.")
    print("  Check the Chrome window and try running this cell again.")


# %% Part D: Define Project Parameters
# ---------------------------------------------------------
#
# Letterboxd lists roughly 7,344 action movies from the 2000s,
# spread across about 103 browse pages (72 movies per page).
# Scraping all of them and then analyzing every single review
# would take too long, so we take a random 10% sample instead.
# That gives us around 734 movies, which is large enough to
# represent the full population without hand-picking bias.
#
# We store these as variables in one place so they are easy
# to find and update if anything needs to change later.


print("\nSTEP 2: Project configuration")

# --- Scraping targets ---
# base_url is already defined above
# The genre/decade filter gives us all 2000s action movies

# --- Sampling ---
sample_percent = 0.10           # 10% of the total population
random_seed = 42                # fixed seed so every run picks the same movies

# --- Output paths ---
data_folder = "data"
full_list_path = "data/all_2000s_action_movies.csv"
sample_path = "data/sample_movies.csv"
html_folder = "letterboxd_reviews_html"

# --- Polite scraping ---
min_delay = 2                   # minimum seconds between page loads
max_delay = 5                   # maximum seconds between page loads
safety_page_limit = 150         # stop after this many pages (in case of errors)

print(f"\n  Target URL pattern: {base_url}")
print(f"  Sample size: {int(sample_percent * 100)}% of total movies found")
print(f"  Random seed: {random_seed} (for reproducibility)")
print(f"  Delay between pages: {min_delay}-{max_delay} seconds")
print(f"  Full list will be saved to: {full_list_path}")
print(f"  Sample will be saved to: {sample_path}")
print(f"  Review HTML folder: {html_folder}/")


# %% Part E: Create Storage Folders
# -------------------------------------------------------
# We create two folders for the team to store their output.
# Module 2 will save downloaded review pages into "letterboxd_reviews_html".
# Module 3 will save parsed review data as CSVs into "data".
# exist_ok=True skips the folder if it already exists instead of crashing.

os.makedirs(data_folder, exist_ok=True)       # CSV movie lists go here
os.makedirs(html_folder, exist_ok=True)        # raw review HTML pages go here

print(f"\n  Created folder: {data_folder}/")
print(f"  Created folder: {html_folder}/")


# %% Summary
# ----------------------------------------------------
#
# At this point, the environment is ready:
#   - Browser is open and has passed Cloudflare
#   - All project parameters are defined
#   - Output folders exist
#
# The 'driver' object and all config variables (base_url,
# sample_percent, random_seed, paths, delays) are in memory
# for Module 2 to use.
#
# Next: Module 2 will loop through the Letterboxd pages using
# this browser, extract movie data, and save the results.

print(f"\n{'-' * 50}")
print("MODULE 1 COMPLETE: Environment is ready")
print("-" * 50)
print("  Browser: open and connected to Letterboxd")
print("  Base URL: {base_url}")
print(f"  Sample rate: {int(sample_percent * 100)}%")
print(f"  Random seed: {random_seed}")
print(f"  Output folders: {data_folder}/, {html_folder}/")
print("\n  Next: Module 2 will scrape movie data from Letterboxd.")
