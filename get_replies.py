import asyncio
from twikit import TooManyRequests  # Assuming this is the correct import for TMR errors

async def get_replies(tweet_id, client):
    """
    Function to fetch replies made by the author of a tweet recursively.
    Returns a list of reply texts, or a message indicating no replies by the author.
    """
    try:
        # Fetch the tweet by ID using the provided client
        tweet = await client.get_tweet_by_id(tweet_id)

        # Get the author handle from the tweet's user attribute
        author_handle = tweet.user.screen_name
        print(f"Author handle: {author_handle}")

        # Access related tweets (replies)
        tweets_replies = tweet.replies
        all_replies = []  # List to store the replies by the author

        # Iterate through each reply and check if the user_handle is the author of the reply
        for tweet_reply in tweets_replies:
            if tweet_reply.user.screen_name == author_handle:
                # If the reply is by the author, add the reply text to the list
                all_replies.append(tweet_reply.text)
                print(f"Found reply by {author_handle}: {tweet_reply.text}")
                
                # Recursively fetch replies to this reply
                nested_replies = await get_replies(tweet_reply.id, client)
                all_replies.extend(nested_replies)  # Add nested replies to the list

        # Return the replies as a list of strings, otherwise return a message indicating no replies
        return all_replies if all_replies else [""]

    except TooManyRequests as e:
        # If rate limit is exceeded, raise the error so it can be handled by the caller
        print(f"TooManyRequests error occurred while fetching replies for tweet {tweet_id}: {e}")
        raise TooManyRequests(f"Rate limit exceeded while fetching replies for tweet {tweet_id}")  # Re-raise to trigger restart
    
    except Exception as e:
        # Catch all other exceptions
        print(f"TooManyRequests error occurred while fetching replies for tweet {tweet_id}: {e}")
        raise TooManyRequests(f"Rate limit exceeded while fetching replies for tweet {tweet_id}")  # Re-raise to trigger restart