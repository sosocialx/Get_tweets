import asyncio
import os
import pandas as pd
from datetime import datetime, timedelta, timezone
from random import randint
from twikit import TooManyRequests
import csv
from get_article import get_article
from get_replies import get_replies
from X_login import main as login
import sys
import subprocess

# Create the 'tweetsdf' folder if it doesn't exist
output_folder = 'tweetsdf'
os.makedirs(output_folder, exist_ok=True)

PROGRESS_FILE = "progress.txt"  # File to store processed tweet IDs

# Function to load processed tweet IDs from the progress file
def load_processed_tweet_ids():
    processed_tweet_ids = set()
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as file:
            for line in file:
                processed_tweet_ids.add(line.strip())  # Add tweet ID to the set
    return processed_tweet_ids

# Function to save processed tweet IDs to the progress file
def save_processed_tweet_ids(processed_tweet_ids):
    with open(PROGRESS_FILE, "a") as file:
        for tweet_id in processed_tweet_ids:
            file.write(f"{tweet_id}\n")

async def fetch_tweets_within_week(client, username, cursor=None):
    """
    Fetch all tweet IDs, full texts, URLs, and their replies for a user within the past week with built-in pagination.
    """
    # Calculate the cutoff date (7 days ago) with UTC timezone
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=1000)

    # Load previously processed tweet IDs
    processed_tweet_ids = load_processed_tweet_ids()

    while True:
        try:
            tweetid = None

            # Fetch user data
            user_data = await client.get_user_by_screen_name(username)
            user_id = user_data.id

            # Initial tweet fetch, with optional cursor
            tweets_data = await client.get_user_tweets(user_id=user_id, tweet_type="Tweets", count=20, cursor=cursor)

            # Check if tweets are available
            if not tweets_data:
                break

            for tweet in tweets_data:
                # Skip already processed tweets
                if tweet.id in processed_tweet_ids:
                    continue

                # Parse the 'created_at' field using the correct format
                created_at = datetime.strptime(tweet.created_at, "%a %b %d %H:%M:%S %z %Y")

                if created_at < one_week_ago:
                    print("Encountered a tweet older than one week. Stopping fetch.")
                    return  # Stop fetching

                # Fetch replies for the tweet using the get_replies function
                replies = await get_replies(tweet.id, client)

                # Extract URLs from the tweet
                tweet_urls = [url['expanded_url'] for url in tweet.urls if 'expanded_url' in url]

                # Check if any URL contains the word 'article'
                article_text = None
                for url in tweet_urls:
                    if "article" in url:
                        article_link = f"https://x.com/{username}/status/{tweet.id}"
                        article_text = get_article(article_link)  # Call the article scraper function
                        break  # Only process the first matching URL

                # Save the current tweet's data to the CSV file immediately after processing
                await save_tweet_ids_and_texts_to_csv(username, [(tweet.id, tweet.full_text, tweet_urls, replies, article_text)])
                tweetid = tweet.id
                print(f"Tweet ID: {tweet.id}")
                print(f"Tweet Text: {tweet.full_text}")
                print(f"URLs: {', '.join(tweet_urls)}")
                print(f"Replies: {len(replies)-1} replies")
                if article_text:
                    print(f"Article Text: {article_text}")
                processed_tweet_ids.add(tweet.id)  # Add to processed set
                save_processed_tweet_ids([tweet.id]) # Save processed tweet IDs to the progress file
                

            # Save the cursor and username for pagination
            cursor = tweets_data.next_cursor  # Correctly retrieve the next cursor
            await save_cursor_and_username(username, cursor)


        except TooManyRequests as e:
            print(f"An error occurred: {e}")
            delay = 60
            print(f"Waiting for {delay} seconds before the next login")
            if tweetid:
                print(f"Last fetched tweet id: {tweetid} for {username}")
            await asyncio.sleep(delay)
            # Exit and restart the script
            subprocess.run(["python", "Scrape_tweets.py"])  # Run the script again
            exit(0)  # Restart the script

        except Exception as e:
            print(f"An error occurred: {e}")
            delay = 60
            print(f"Waiting for {delay} seconds before the next login")
            if tweetid:
                print(f"Last fetched tweet id: {tweetid} for {username}")
            await asyncio.sleep(delay)
            # Exit and restart the script
            subprocess.run(["python", "Scrape_tweets.py"])  # Run the script again
            exit(0)  # Restart the script

async def save_cursor_and_username(username, next_cursor):
    """
    Save the username and next_cursor for pagination in a text file.
    """
    with open("cursor_data.txt", "w") as f:
        f.write(f"{username},{next_cursor}\n")
    print(f"Cursor for {username} saved.")

async def save_tweet_ids_and_texts_to_csv(username, tweets):
    """
    Save tweet IDs, tweet full texts, URLs, replies, and article text to a CSV file named after the account in the 'tweetsdf' folder.
    """
    filename = os.path.join(output_folder, f"{username}.csv")  # Save to the 'tweetsdf' folder

    # Open the file in append mode to add data incrementally
    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        # Write the header only if the file is empty
        if file.tell() == 0:  # Check if the file is empty
            writer.writerow(["Tweet ID", "Tweet Text", "URLs", "Replies", "Article Text"])

        for tweet_id, tweet_text, tweet_urls, replies, article_text in tweets:
            writer.writerow([tweet_id, tweet_text, "|".join(tweet_urls), "|".join(replies), article_text or ""])

    print(f"Tweet for {username} saved to {filename}")

async def process_influencers_from_csv(file_path):
    # Load the CSV file
    df = pd.read_csv(file_path)
    
    # Strip any leading or trailing whitespace from the column names
    df.columns = df.columns.str.strip()
    
    # Extract usernames from the 'URL' column
    usernames = df['URL'].apply(lambda x: x.split('/')[-1])

    # Initialize the client using your login script
    client = await login()

    if not client:
        print("Failed to initialize client. Exiting.")
        return

    # Load progress from the cursor_data.txt if it exists
    progress_user = None
    progress_cursor = None
    if os.path.exists('cursor_data.txt'):
        with open('cursor_data.txt', 'r') as f:
            for line in f:
                saved_username, saved_cursor = line.strip().split(",")
                # If there's a match with the current username from the CSV
                if saved_username in usernames.values:
                    progress_user = saved_username
                    progress_cursor = saved_cursor
                    break  # Exit the loop once we find the progress user

    if progress_user and progress_cursor:
        # Start by processing the user in progress
        print(f"Resuming scraping for {progress_user} from cursor: {progress_cursor}")
        await fetch_tweets_within_week(client, progress_user, progress_cursor)

        # Get the index of the progress user using .index() for Series
        progress_user_index = usernames[usernames == progress_user].index[0]
        
        # If progress_user is not the last user, process the remaining users
        if progress_user_index < len(usernames) - 1:
            remaining_users = usernames.iloc[progress_user_index + 1:]  # Get users after the progress user
            for username in remaining_users:
                print(f"Processing remaining user {username}...")
                await fetch_tweets_within_week(client, username, None)
        else:
            print(f"Progress user {progress_user} is the last user. No remaining users to process.")
    else:
        print("No progress file found or malformed. Starting fresh.")
        # If no progress file exists or is malformed, process from the beginning
        for username in usernames:
            print(f"Starting fresh for {username}.")
            await fetch_tweets_within_week(client, username, None)
    
# Call the function with the path to the CSV file
file_path = 'influencers.csv'  # Adjust the file path as needed
asyncio.run(process_influencers_from_csv(file_path))
#neura