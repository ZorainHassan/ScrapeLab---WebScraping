# -*- coding: utf-8 -*-
"""
Created on Tue Nov 24 13:41:59 2026

@author: mrzee
"""

# =============================================================================
# # Module 4: Data Cleaning, Merging & Exporting
# # Member: Zorain
# # Team 3: ScrapeLab
# =============================================================================

from pathlib import Path
import html
import re
import pandas as pd

PROJECT_DIR = Path.cwd()
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = DATA_DIR / "Module4_output_Zorain"

MOVIES_FILE = DATA_DIR / "final_movie_dataset.csv"
REVIEWS_FILE = DATA_DIR / "reviews_raw.csv"

if not MOVIES_FILE.exists() or not REVIEWS_FILE.exists():
    raise FileNotFoundError(
        f"Expected both CSV files in: {DATA_DIR}\n"
        "If they are elsewhere, update MOVIES_FILE and REVIEWS_FILE."
    )

movies_raw = pd.read_csv(MOVIES_FILE, encoding="utf-8-sig")
reviews_raw = pd.read_csv(
    REVIEWS_FILE,
    encoding="utf-8-sig",
    dtype={"movie_url": "string", "review_date": "string"}
)

# To understand data structure of each file
print("Movies:", movies_raw.shape)
print("Reviews:", reviews_raw.shape)
print("Movie columns:", movies_raw.columns.tolist())
print("Review columns:", reviews_raw.columns.tolist())
print("\nMissing values in Movies df:\n", movies_raw.isna().sum())
print("\nMissing values in Reviews df:\n", reviews_raw.isna().sum())
movies_raw.head(5)
print(reviews_raw)

# =============================================================================
# ## DATA CLEANING
# =============================================================================
# movies_raw-> handling appropriate naming convention, dtypes, missing values

# Renaming variables for ease & using copy() function to make a real duplicate
movies = movies_raw.rename(columns={
    "Title": "movie_title",
    "Release Year": "movie_release_year",
    "URL": "movie_url",
    "Letterboxd Rating": "lb_average_rating",
    "Number of Ratings": "lb_rating_count",
    "Genres": "genres"
}).copy()

# making the column text & removing whitespace at the beginning or end.
# The URL is our join key as it identifies the same film in both files 
movies["movie_url"] = movies["movie_url"].astype("string").str.strip()
movies["movie_title"] = movies["movie_title"].astype("string").str.strip()

# forcing coerce to make blank value stay missing instead of becoming 0
movies["movie_release_year"] = pd.to_numeric(
    movies["movie_release_year"], errors="coerce"
).astype("Int64")

movies["lb_average_rating"] = pd.to_numeric(
    movies["lb_average_rating"], errors="coerce"
)

movies["lb_rating_count"] = pd.to_numeric(
    movies["lb_rating_count"]
        .astype("string")
        .str.replace(",", "", regex=False),
    errors="coerce"
).astype("Int64")

movies["genres"] = (
    movies["genres"].astype("string").str.strip().replace("", pd.NA)
)

print("Duplicate movie URLs:", movies["movie_url"].duplicated().sum())

# This URL checks protect the merge. Each movie must have a URL, 
# and each data URL must appear only once. If either condition fails, 
# the code stops and tells there is something to resolve before merging.
if movies["movie_url"].isna().any():
    raise ValueError("Some data rows have no movie URL.")
if movies["movie_url"].duplicated().any():
    raise ValueError("Data URLs must be unique before the merge.")
    
    
# reviews_raw -> Clean Review text, ratings and dates.
# Keeping the raw date and text so the cleaning is auditable.
reviews = reviews_raw.rename(columns={
    "movie_title": "review_movie_title",
    "release_year": "review_release_year",
    "review_date": "review_date_raw"
}).copy()

reviews["movie_url"] = reviews["movie_url"].astype("string").str.strip()
reviews["review_movie_title"] = (
    reviews["review_movie_title"].astype("string").str.strip()
)

reviews["review_release_year"] = pd.to_numeric(
    reviews["review_release_year"], errors="coerce"
).astype("Int64")

reviews["user_rating"] = pd.to_numeric(
    reviews["user_rating"], errors="coerce"
)

reviews["review_text_raw"] = reviews["review_text"].astype("string")
reviews["review_date_raw"] = (
    reviews["review_date_raw"].astype("string").str.strip()
)

# Detect the scrape-added marker ONLY when it appears at the end
# this handle “... more”, “..more” and “… more”.
truncation_pattern = re.compile(r"(?:…|\.{2,})\s*more\s*$", flags=re.IGNORECASE)

reviews["text_maybe_truncated"] = reviews["review_text_raw"].str.contains(
    truncation_pattern,
    na=False
)

# Clean formatting artifacts, without rewriting the review itself.
def clean_review_text(value):
    if pd.isna(value):
        return pd.NA

# decodes HTML entities, 
    text = html.unescape(str(value))
#replaces text that looks like an HTML tag with a space
    text = re.sub(r"<[^>]+>", " ", text)
#remove the Letterboxd-style ending, but only at the very end
    text = truncation_pattern.sub("", text)
#remove invisible control characters and normalize whitespace.
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text if text else pd.NA #else return missing value marker 

# mapping changes to every value in column while review_text_raw stays 
# available for checking
reviews["review_text"] = (
    reviews["review_text_raw"].map(clean_review_text).astype("string")
)

# Flagging possible Truncation für ellipses
reviews["text_maybe_truncated"] = reviews["review_text_raw"].str.contains(
    r"(?:…|\.{3})\s*more\s*$",
    case=False,
    na=False
)

# Parsing dates as it contains both dates and timestamps
# fullmatch tests whether the entire value follows the year-month-day pattern
reviews["review_date_raw"] = reviews["review_date_raw"].astype("string").str.strip()
date_only = reviews["review_date_raw"].str.fullmatch(
    r"\d{4}-\d{2}-\d{2}", na=False
)

# Parse only YYYY-MM-DD. This creates a date with no time or timezone.
# Invalid dates become missing (NaT); they are not guessed or repaired.
date_only_text = reviews["review_date_raw"].str.slice(0, 10)
reviews["review_date"] = pd.to_datetime(
    date_only_text,
    format="%Y-%m-%d",
    errors="coerce"
)

#.dt.year extracts the year from each parsed date,
# so that we can group by for a yearly trend analysis.
reviews["review_year"] = reviews["review_date"].dt.year.astype("Int64")

print("Blank cleaned review texts:", reviews["review_text"].isna().sum())
print("Dates that did not parse:", reviews["review_date"].isna().sum())
print("Possibly truncated reviews:", reviews["text_maybe_truncated"].sum())
print("Missing user ratings:", reviews["user_rating"].isna().sum())


# =============================================================================
# # Merging reviews dataset with movies dataframe
# =============================================================================

if "review_title" in reviews.columns and reviews["review_title"].isna().all():
    reviews = reviews.drop(columns="review_title")

# Merging table using movie_url - I'm merging first, then identify dates 
# outside the analysis window and dates earlier than the film’s release year.

# As per our RQ, time period is 2000-2026
ANALYSIS_START = pd.Timestamp("2000-01-01")
ANALYSIS_END = pd.Timestamp.today().normalize()

merged = reviews.merge(
    movies,
    on="movie_url",
    how="left", # keeps every review even if a matching movie record is absent
    validate="many_to_one", # since many reviews can belong to single movie
    indicator=True # temp adds a col showing whether review found a movie match
)

#it turns the merge indicator into a simple True/False column
#The code then removes the temporary `_merge` column.
merged["data_matched"] = merged["_merge"].eq("both")
merged = merged.drop(columns="_merge")

# A date is outside the chosen period if it failed to parse or is outside
# the inclusive start/end dates.
outside_period = (
    merged["review_date"].isna()
    | (merged["review_date"] < ANALYSIS_START)
    | (merged["review_date"] > ANALYSIS_END)
)

# A review date before the film's release year is a separate warning
pre_release_date = (
    merged["review_date"].notna()
    & merged["movie_release_year"].notna()
    & (merged["review_date"].dt.year < merged["movie_release_year"])
)

date_audit = merged.loc[
    outside_period | pre_release_date,
    [
        "review_date_raw",
        "review_date",
        "review_release_year",
        "movie_release_year",
        "review_movie_title",
        "movie_url",
        "review_text_raw"
    ]
].copy()


print("Review rows before merge:", len(reviews))
print("Rows after merge:", len(merged))
print("Unmatched review URLs:", (~merged["data_matched"]).sum())
print("Rows outside chosen date period:", outside_period.sum())
print("Rows dated before the film's release year:", pre_release_date.sum())
print("\nInspect these date exceptions before filtering:")
print(date_audit.to_string(index=False))

if len(merged) != len(reviews):
    raise ValueError("The merge changed the number of review rows.")
    
#row-count checks ensuring merge did not multiply or lose review rows
# to check whether the release year recorded in the review file disagrees 
# with the movie dataset
release_year_mismatches = (
    merged["review_release_year"].notna()
    & merged["movie_release_year"].notna()
    & (merged["review_release_year"] != merged["movie_release_year"])
).sum()

print("Release-year mismatches:", release_year_mismatches)

if len(merged) != len(reviews):
    raise ValueError("The merge changed the number of review rows.")


# Truncation-evidence coding that prints the count and sample endings

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

truncation_evidence = merged.loc[
    merged["text_maybe_truncated"],
    [
        "movie_title",
        "movie_release_year",
        "movie_url",
        "review_date_raw",
        "review_text_raw",
        "review_text"
    ]
].copy()

print(
    "Rows with an ending ellipsis followed by 'more':",
    len(truncation_evidence)
)
print(
    "Share of all reviews:",
    round(100 * len(truncation_evidence) / len(merged), 2),
    "%"
)

# Showing examples including the original ending and the cleaned ending
sample_size = min(10, len(truncation_evidence))
if sample_size:
    examples = truncation_evidence.sample(
        n=sample_size,
        random_state=42
    )
    for _, row in examples.iterrows():
        print("\nMovie:", row["movie_title"])
        print("Original ending:", str(row["review_text_raw"])[-120:])
        print("Cleaned ending: ", str(row["review_text"])[-120:])

# =============================================================================
# #Exporting files
# =============================================================================

evidence_file = OUTPUT_DIR / "truncation_evidence.csv"
truncation_evidence.to_csv(
    evidence_file,
    index=False,
    encoding="utf-8-sig"
)
print("\nFull evidence saved to:", evidence_file)

# Exporting Cleaned Datasets
master_file = OUTPUT_DIR / "merged_module4_master_file.csv"
analysis_file = OUTPUT_DIR / "final_module4_merged.csv"

# Keeping all records and date flags in the auditable master file
merged["outside_analysis_period"] = outside_period
merged["date_precedes_release_year"] = pre_release_date

merged.to_csv(
    master_file,
    index=False,
    encoding="utf-8-sig",
    date_format="%Y-%m-%d"
)

# Excluding flagged dates only from this analysis copy
exclude_dates = outside_period | pre_release_date
analysis_df = merged.loc[~exclude_dates].copy()

analysis_df.to_csv(
    analysis_file,
    index=False,
    encoding="utf-8-sig",
    date_format="%Y-%m-%d"
)

print("Master rows:", len(merged))
print("Rows excluded from the analysis copy:", exclude_dates.sum())
print("Analysis rows:", len(analysis_df))
print("Master saved to:", master_file)
print("Analysis copy saved to:", analysis_file)
