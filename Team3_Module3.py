# --------------------------------------------
# MODULE 3: User Review Text Scraping
# Member Name: Yuuka Matsumoto
# Team 3: ScrapeLab
# --------------------------------------------
#
# What this module does:
#   1. Connect to the browser ("driver") and parameters from Module 1
#   2. Load the movie dataset produced by Module 2 ("final_movie_dataset.csv")
#   3. Navigate to each movie's review sub-pages
#   4. Extract review title, review text, review date, and user rating
#   5. export parsed reviews to CSV ("reviews_raw.csv")
# ------------------------------------------------------------



# Parameters from Module 1 (I changed the loading time setting)
# ------------------------------------------------------------
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import undetected_chromedriver as uc

# Create a blank settings object for Chrome
options = uc.ChromeOptions()    

# Open Chrome with those settings; "driver" is now our remote control
driver = uc.Chrome(options=options)
driver.maximize_window()

# --- Sampling ---
sample_percent = 0.10           # 10% of the total population
random_seed = 42                # fixed seed so every run picks the same movies

# --- Output paths ---
data_folder = "data"
full_list_path = "data/all_2000s_action_movies.csv"
sample_path = "data/sample_movies.csv"
html_folder = "letterboxd_reviews_html"


# --- Polite scraping ---  
### I changed the setting because the original setting was too fast for review scraping 
### and The Letterboxd's website protection bot stop the running code

min_delay = 5                  # minimum seconds between page loads
max_delay = 15             # maximum seconds between page loads   

# ------------------------------------------------------------



# Settings for Module 3
# ------------------------------------------------------------

# --- Resume settings ---
start_movie_idx = 573       # 0-indexed: 573 = 574nd movie
resume_page_for_start_movie = 206   # 206 = 206th page


# %% Part A: Connect to Module 1 & Set Output Paths
# -----------------------------------------------


print("Current page:", driver.current_url)

os.makedirs(data_folder, exist_ok=True)

input_movie_path = os.path.join(data_folder, "final_movie_dataset.csv")
reviews_raw_path = os.path.join(data_folder, "reviews_raw.csv")



# %% Part B: Load Movie Dataset from Module 2
# -----------------------------------------------


movies_df = pd.read_csv(input_movie_path, encoding="utf-8-sig")

print("Total movies to process:", len(movies_df))   # The number has to be 734!



# %% Part C: Helper Function to Parse Review HTML
# -----------------------------------------------

# Convert star like '★★★½' into float (3.5).
def parse_star_rating(label_text):

    if not label_text:
        return None
    stars = label_text.count("★") * 1.0
    if "½" in label_text:
        stars += 0.5
    return stars if stars > 0 else None


# Extract text, date, and rating from Letterboxd review HTML.
def parse_reviews_from_soup(soup):

    parsed = []

    for item in soup.select("div.listitem article.production-viewing"):
        body = item.select_one("div.body-text")
        if body is None:
            continue

        # Review text
        p_texts = []
        for p in body.select("p"):
            txt = p.get_text(" ", strip=True)
            if txt:
                p_texts.append(txt)
        review_text = " ".join(p_texts).strip()

        if not review_text:
            continue

        # Review date
        review_date = None
        time_tag = item.select_one("time.timestamp") or item.select_one("time")
        if time_tag and time_tag.get("datetime"):
            review_date = time_tag["datetime"].strip()
        elif time_tag:
            review_date = time_tag.get_text(strip=True)

        # User evaluation
        user_rating = None
        rating_svg = item.select_one("span.inline-rating svg")
        if rating_svg:
            label = rating_svg.get("aria-label")
            if not label:
                title_el = rating_svg.find("title")
                if title_el:
                    label = title_el.get_text(strip=True)
            user_rating = parse_star_rating(label)

        parsed.append({
            "review_text": review_text,
            "review_date": review_date,
            "user_rating": user_rating,
        })

    return parsed


# %% Part D: Scrape Reviews Across Movies and Pages
# -----------------------------------------------

all_reviews = []
blocked = False


for idx, movie in movies_df.iloc[start_movie_idx:].iterrows():
    movie_title = movie["Title"]
    release_year = movie["Release Year"]
    movie_url = str(movie["URL"]).strip()

    if not movie_url.startswith("/"):
        movie_url = "/" + movie_url

    print(f"\n[{idx + 1}/{len(movies_df)}] {movie_title} ({release_year})")

    # The first movie starts from assigned page.
    page_number = resume_page_for_start_movie if idx == start_movie_idx else 1

    while True:
        review_page_url = f"https://letterboxd.com{movie_url}reviews/by/added/page/{page_number}/"
        print(f"  Loading page {page_number}: {review_page_url}")

        driver.get(review_page_url)
        time.sleep(random.uniform(min_delay, max_delay))

        page_source = driver.page_source or ""
        page_title = driver.title or ""

        if "Just a moment" in page_title or "Security check" in page_source:
            print("  Cloudflare verification detected. Stopping to avoid blocks.")
            blocked = True
            break

        soup = BeautifulSoup(page_source, "html.parser")
        page_reviews = parse_reviews_from_soup(soup)

        print(f"  Reviews found on page {page_number}: {len(page_reviews)}")

        if len(page_reviews) == 0:
            print("  No more reviews on this page. Moving to next movie.")
            break

        for rev in page_reviews:
            rev.update({
                "movie_title": movie_title,
                "release_year": release_year,
                "movie_url": movie_url,
            })
            all_reviews.append(rev)

        page_number += 1

    if blocked:
        break


# %% Part E: Clean Duplicates and Save Final Reviews CSV
# -----------------------------------------------

expected_cols = [
    "movie_title",
    "release_year",
    "movie_url",
    "review_title",
    "review_text",
    "review_date",
    "user_rating",
]

new_df = pd.DataFrame(all_reviews) if len(all_reviews) > 0 else pd.DataFrame(columns=expected_cols)

if os.path.exists(reviews_raw_path):
    existing_df = pd.read_csv(reviews_raw_path, encoding="utf-8-sig")
    reviews_df = pd.concat([existing_df, new_df], ignore_index=True)
else:
    reviews_df = new_df

if len(reviews_df) > 0:
    reviews_df = reviews_df.drop_duplicates(
        subset=["movie_url", "review_text", "review_date"]
    )
    cols_present = [c for c in expected_cols if c in reviews_df.columns]
    reviews_df = reviews_df[cols_present]
else:
    reviews_df = pd.DataFrame(columns=expected_cols)

reviews_df.to_csv(reviews_raw_path, index=False, encoding="utf-8-sig")


print("\n========== MODULE 3 RESUME COMPLETED ==========")
print("Blocked early:", blocked)
print("New reviews scraped in this run:", len(new_df))
print("Total unique reviews saved:", len(reviews_df))
print("Saved to:", reviews_raw_path)