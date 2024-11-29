import praw
import praw.exceptions
from utils.config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
from utils.db import is_muted
import logging
import time


def auth():
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )
    return reddit


def observe_comments(comment_stream, redditor):
    """Monitor comments for a redditor"""
    try:
        comment = next(comment_stream)
        print(f"Checked {redditor} comments")
        if comment is None:
            return False
        print(f"received comment from {redditor[0]}")
        if (
            (comment.subreddit.display_name in {"wallstreetbets", "thetagang"})
            and not comment.is_submitter
            and not is_muted(redditor[0])
            and comment.created > time.time() - (60*60*24)
        ):
            return f"RATING: {int(redditor[1])*'🚀'}\n🎇New comment from {redditor[0]}:\n{comment.body}\nwww.reddit.com{comment.permalink}\n🎇"

    except StopIteration:
        return False
    except Exception as e:
        print(f"Error processing comment for {redditor}: {e}")
        logging.error(
            f"An error occurre in observe comments for {redditor[0]}", exc_info=True
        )
        raise


def observe_submissions(submission_stream, redditor):
    """Monitor submissions for a redditor"""
    try:
        submission = next(submission_stream)
        print(f"Checked {redditor} submission")
        if submission is None:
            return False
        print(f"received submission from {redditor[0]}")
        if (
            submission.subreddit.display_name in {"wallstreetbets", "thetagang"}
        ) and not is_muted(redditor[0]) and submission.created > time.time() - (60*60*24):
            return f"RATING: {int(redditor[1])*'🚀'}\n🎆New submission from {redditor[0]}:\n{submission.title}\n{submission.url}\n🎆"
    except StopIteration:
        return False
    except Exception as e:
        print(f"Error processing submission for {redditor}: {e}")
        logging.error(
            f"An error occurre in observe submissions for {redditor[0]}", exc_info=True
        )
        raise


def check_redditor_exists(reddit, redditor):
    try:
        redditor = reddit.redditor(redditor)
        redditor.fullname
        return True
    except praw.exceptions.RedditAPIException as e:
        # If RedditAPIException is raised, the redditor doesn't exist
        print(f"Error: {e}")
        return False  # Return False if the redditor does not exist
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
