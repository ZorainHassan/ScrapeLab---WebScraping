
"""
Module 2: Movie Metadata Scraping
Team 3 - ScrapeLab

This module collects movie information from Letterboxd
for action movies released between 2000 and 2009.

Information collected:
- Movie title
- Release year
- Movie URL
- Letterboxd average rating
- Number of ratings
- Movie genres
"""

# Import the libraries we need
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import random
import os


# --------------------------------------------------
# 1. Connect to Module 1
# --------------------------------------------------

print("Module 2 connected to Module 1 browser!")
print("Current page:", driver.current_url)

# Make sure the data folder exists
os.makedirs(data_folder, exist_ok=True)

# Set the file paths
details_path = data_folder + "/movie_details_sample.csv"
final_path = data_folder + "/final_movie_dataset.csv"


# --------------------------------------------------
# 2. Collect all movies from Letterboxd
# --------------------------------------------------

# Check if we already have the complete movie list
if os.path.exists(full_list_path):

    print("\nLoading the saved movie list...")

    df = pd.read_csv(full_list_path)

    print("Total movies loaded:", len(df))

else:

    # Store all movies from every page
    all_movies = []

    # Go through the movie pages one by one
    for page_number in range(1, safety_page_limit + 1):

        print("\nScraping page", page_number)

        # Open the current page
        driver.get(base_url.format(page_number))

        # Wait a random amount of time
        time.sleep(random.uniform(min_delay, max_delay))

        # Read the page
        soup = BeautifulSoup(
            driver.page_source,
            "html.parser"
        )

        # Find all movie containers
        poster_items = soup.find_all(
            "li",
            class_="posteritem"
        )

        print("Movie containers found:", len(poster_items))

        # Stop when there are no more movies
        if len(poster_items) == 0:

            print("No more movies found. Stopping.")
            break

        # Get information about each movie
        for item in poster_items:

            movie_info = item.find(
                "div",
                class_="react-component",
                attrs={"data-item-name": True}
            )

            if movie_info:

                full_title = movie_info.get("data-item-name")

                # Separate the movie title and release year
                match = re.match(
                    r"^(.*?)\s+\((\d{4})\)$",
                    full_title
                )

                if match:

                    title = match.group(1)
                    year = match.group(2)

                else:

                    title = full_title
                    year = None

                # Get the movie URL and rating
                movie_url = movie_info.get("data-item-link")
                rating = item.get("data-average-rating")

                # Add the movie information to our list
                all_movies.append({

                    "Title": title,
                    "Release Year": year,
                    "URL": movie_url,
                    "Letterboxd Rating": rating

                })

    # Put all movies into a DataFrame
    df = pd.DataFrame(all_movies)

    # Remove movies that appear more than once
    df = df.drop_duplicates(subset="URL")

    # Save the complete movie list
    df.to_csv(
        full_list_path,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nComplete movie list saved!")
    print("Total unique movies:", len(df))


# --------------------------------------------------
# 3. Load the 10% movie sample
# --------------------------------------------------

# Check if the sample already exists
if os.path.exists(sample_path):

    print("\nLoading the saved 10% sample...")

    sample_df = pd.read_csv(sample_path)

else:

    # Create a random 10% sample
    sample_df = df.sample(
        frac=sample_percent,
        random_state=random_seed
    )

    # Save the sample
    sample_df.to_csv(
        sample_path,
        index=False,
        encoding="utf-8-sig"
    )

    print("10% sample created and saved!")

print("Number of movies in sample:", len(sample_df))


# --------------------------------------------------
# 4. Scrape genres and number of ratings
# --------------------------------------------------

# Check if we already scraped the movie details
if os.path.exists(details_path) and len(pd.read_csv(details_path)) == len(sample_df):

    print("\nLoading the saved movie details...")

    details_df = pd.read_csv(details_path)

    print("Movies with detailed information:", len(details_df))

else:

    print("\nStarting to scrape movie details...")

    # Store the detailed movie information
    movie_details = []

    # Go through each movie in the sample
    for index, movie in sample_df.iterrows():

        print("\nScraping movie", index + 1, "of", len(sample_df))
        print("Title:", movie["Title"])

        # Open the movie's detail page
        movie_url = "https://letterboxd.com" + movie["URL"]

        driver.get(movie_url)

        # Wait a random amount of time
        time.sleep(random.uniform(min_delay, max_delay))

        # Read the movie page
        soup = BeautifulSoup(
            driver.page_source,
            "html.parser"
        )

        # Get the number of ratings
        rating_info = soup.find(
            "a",
            class_="averagerating"
        )

        number_of_ratings = None

        if rating_info:

            rating_text = rating_info.get("data-original-title")

            if rating_text:

                ratings_match = re.search(
                    r"based on ([\d,]+) ratings",
                    rating_text
                )

                if ratings_match:

                    number_of_ratings = ratings_match.group(1)

        # Get the movie genres
        genre_info = soup.find_all(
            "a",
            href=re.compile(r"^/films/genre/[^/]+/$")
        )

        genres = []

        for genre in genre_info:

            genre_name = genre.get_text(strip=True)

            # Avoid adding the same genre twice
            if genre_name not in genres:

                genres.append(genre_name)

        # Save all the movie information
        movie_details.append({

            "Title": movie["Title"],
            "Release Year": movie["Release Year"],
            "URL": movie["URL"],
            "Letterboxd Rating": movie["Letterboxd Rating"],
            "Number of Ratings": number_of_ratings,
            "Genres": ", ".join(genres)

        })

        # Save our progress after every 50 movies
        if (index + 1) % 50 == 0:

            details_df = pd.DataFrame(movie_details)

            details_df.to_csv(
                details_path,
                index=False,
                encoding="utf-8-sig"
            )

            print("Progress saved:", index + 1, "movies")

    # Save the final detailed results
    details_df = pd.DataFrame(movie_details)

    details_df.to_csv(
        details_path,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nDetail scraping completed!")
    print("Total movies scraped:", len(details_df))


# --------------------------------------------------
# 5. Clean the movie dataset
# --------------------------------------------------

print("\nCleaning the movie dataset...")

# Make a copy of the completed dataset
cleaned_df = details_df.copy()

# Convert release years into numbers
cleaned_df["Release Year"] = pd.to_numeric(
    cleaned_df["Release Year"],
    errors="coerce"
)

# Convert Letterboxd ratings into numbers
cleaned_df["Letterboxd Rating"] = pd.to_numeric(
    cleaned_df["Letterboxd Rating"],
    errors="coerce"
)

# Remove commas from the number of ratings
# Then convert them into numbers
cleaned_df["Number of Ratings"] = pd.to_numeric(
    cleaned_df["Number of Ratings"]
    .astype("string")
    .str.replace(",", "", regex=False),
    errors="coerce"
)

# Remove duplicate movies
cleaned_df = cleaned_df.drop_duplicates(
    subset="URL"
)


# --------------------------------------------------
# 6. Save the final dataset
# --------------------------------------------------

cleaned_df.to_csv(
    final_path,
    index=False,
    encoding="utf-8-sig"
)

print("\nFinal dataset saved successfully!")
print("Saved to:", final_path)


# --------------------------------------------------
# 7. Check the final dataset
# --------------------------------------------------

print("\n========== FINAL DATASET CHECK ==========")

# Check the total number of movies
print("\nTotal movies:", len(cleaned_df))

# Check the dataset size
print("Dataset shape:", cleaned_df.shape)

# Check for duplicate movie URLs
print(
    "Duplicate movie URLs:",
    cleaned_df["URL"].duplicated().sum()
)

# Check for missing values
print("\nMissing values:")
print(cleaned_df.isnull().sum())

# Check for movies without genres
empty_genres = (
    cleaned_df["Genres"].fillna("").str.strip() == ""
).sum()

print("\nMovies without genres:", empty_genres)

# Check the release year range
print("\nRelease year range:")

print(
    cleaned_df["Release Year"].min(),
    "-",
    cleaned_df["Release Year"].max()
)

# Check the rating range
print("\nLetterboxd rating range:")

print(
    cleaned_df["Letterboxd Rating"].min(),
    "-",
    cleaned_df["Letterboxd Rating"].max()
)

# Display the first five movies
print("\nFirst five movies:")
print(cleaned_df.head())

print("\n========== MODULE 2 COMPLETED ==========")
import pandas as pd

details_df = pd.read_csv("data/movie_details_sample.csv")

print("Number of movie details:", len(details_df))
print(details_df.head())