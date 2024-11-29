import threading
import signal
from telegram import send_message, handle_updates
from utils.db import get_chat_ids, list_redditors_db
from reddit_observer import auth, observe_submissions, observe_comments
import time
import queue
import logging
import traceback
import gc

logging.basicConfig(
    level=logging.ERROR,
    filename="utils/errors.log",
    format="%(asctime)s - %(levelname)s - %(message)s",
)

STOP_EVENT = threading.Event()


def handle_shutdown_signal(signum, frame):
    print("Shutdown signal received.")
    STOP_EVENT.set()


def observe_submission_loop(reddit, redditor, chat_ids, stop_event, thread_exit_event):
    submission_stream = None
    try:
        while not stop_event.is_set() and not thread_exit_event.is_set():
            print(f"started submission thread: {redditor[0]}")
            try:
                submission_stream = reddit.redditor(redditor[0]).stream.submissions(
                    skip_existing=True,
                    pause_after=0,
                )
                while not stop_event.is_set() and not thread_exit_event.is_set():
                    message = observe_submissions(submission_stream, redditor)
                    if message:
                        send_message(message, chat_ids)
                    time.sleep(30)
            except Exception as e:
                print(f"Error with submission stream for {redditor[0]}: {e}")
                logging.error(
                    f"An error occurred in submission stream for {redditor[0]}",
                    exc_info=True,
                )
                submission_stream = None
                gc.collect()
                # Optional: short delay before retrying
                time.sleep(10)
    except Exception as e:
        print(f"Stream error for {redditor[0]}: {e}")
        logging.error(
            f"An error occurred in observe submissions LOOP for {redditor[0]}",
            exc_info=True,
        )
        return



def observe_comments_loop(reddit, redditor, chat_ids, stop_event, thread_exit_event):
    comment_stream = None
    try:
        while not stop_event.is_set() and not thread_exit_event.is_set():
            print(f"started comments thread: {redditor[0]}")
            try:
                comment_stream = reddit.redditor(redditor[0]).stream.comments(
                    skip_existing=True,
                    pause_after=0,
                )
                while not stop_event.is_set() and not thread_exit_event.is_set():
                    message = observe_comments(comment_stream, redditor)
                    if message:
                        send_message(message, chat_ids)
                    time.sleep(30)
            except Exception as e:
                print(f"Error with comments stream for {redditor[0]}: {e}")
                logging.error(
                    f"An error occurred in comments stream for {redditor[0]}",
                    exc_info=True,
                )
                # Optional: short delay before retrying
                time.sleep(10)
    except Exception as e:
        print(f"Stream error for {redditor[0]}: {e}")
        logging.error(
            f"An error occurred in observe comments LOOP for {redditor[0]}",
            exc_info=True,
        )
        comment_stream = None
        gc.collect()
        return


def handle_update_loop(
    stop_event, reddit, created_redditors_queue, removed_redditor_queue
):
    try:
        while not stop_event.is_set():
            handle_updates(reddit, created_redditors_queue, removed_redditor_queue)
    except Exception as e:
        print(f"Exception in handle update loop: {e}")


def handle_new_redditor(created_redditors_queue, threads, stop_event, chat_ids, reddit):
    while not stop_event.is_set():
        try:
            thread_exit_event = threading.Event()
            redditor = created_redditors_queue.get(timeout=10)
            thread_submission = threading.Thread(
                target=observe_submission_loop,
                args=(reddit, redditor, chat_ids, stop_event, thread_exit_event),
            )
            thread_submission.daemon = True
            thread_submission.name = redditor[0]

            thread_submission.start()

            thread_comment = threading.Thread(
                target=observe_comments_loop,
                args=(reddit, redditor, chat_ids, stop_event, thread_exit_event),
            )
            thread_comment.daemon = True
            thread_comment.name = redditor[0]

            thread_comment.start()
            threads.append(
                {
                    "name": redditor[0],
                    "threads": [thread_submission, thread_comment],
                    "exit_event": thread_exit_event,
                }
            )
            print(f"started thread for {redditor}")
        except queue.Empty:
            # Queue is empty; continue the loop
            continue

        except Exception as e:
            print(f"Error in handle_new_redditor: {e}")
            traceback.print_exc()


def handle_removed_redditor(removed_redditors_queue, threads, stop_event):
    while not stop_event.is_set():
        try:
            redditor = removed_redditors_queue.get(timeout=10)
            for thread in threads:
                # print(thread)
                if thread["name"].strip() == redditor.strip():
                    print(f"{redditor} thread ending")
                    thread["exit_event"].set()
                    for inner_thread in thread["threads"]:
                        if inner_thread.is_alive():
                            inner_thread.join()
                            print(f"{redditor} thread got ended")

        except queue.Empty:
            # Queue is empty; continue the loop
            continue
        except Exception as e:
            print(f"Error in handle_removed_redditor: {e}")
            traceback.print_exc()


def main():
    created_redditor_queue = queue.Queue()
    removed_redditors_queue = queue.Queue()
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)

    reddit = auth()
    threads = []
    redditors = list_redditors_db()
    chat_ids = get_chat_ids()
    non_redditor_threads = []

    send_message(
        chat_ids=chat_ids,
        message="Starting Reddit-Bot V 1.0 🎇 New Commands:\n/list\n/add <redditor> <rating>\n/remove <redditor>\n/mute <redditor> <days>\n/unmute <redditor>\n/giverockets <redditor> <amount(can be negative)>",
    )

    try:
        for redditor in redditors:
            thread_exit_event = threading.Event()
            thread_submission = threading.Thread(
                target=observe_submission_loop,
                args=(reddit, redditor, chat_ids, STOP_EVENT, thread_exit_event),
            )
            thread_submission.daemon = True
            thread_submission.name = redditor[0]

            thread_submission.start()

            thread_comment = threading.Thread(
                target=observe_comments_loop,
                args=(reddit, redditor, chat_ids, STOP_EVENT, thread_exit_event),
            )
            thread_comment.daemon = True
            thread_comment.name = redditor[0]

            thread_comment.start()
            threads.append(
                {
                    "name": redditor[0],
                    "threads": [thread_submission, thread_comment],
                    "exit_event": thread_exit_event,
                }
            )

        telegram_update_handler_thread = threading.Thread(
            target=handle_update_loop,
            args=(STOP_EVENT, reddit, created_redditor_queue, removed_redditors_queue),
        )
        telegram_update_handler_thread.daemon = True
        non_redditor_threads.append(telegram_update_handler_thread)
        telegram_update_handler_thread.start()

        handle_new_redditor_thread = threading.Thread(
            target=handle_new_redditor,
            args=(created_redditor_queue, threads, STOP_EVENT, chat_ids, reddit),
        )
        handle_new_redditor_thread.daemon = True
        non_redditor_threads.append(handle_new_redditor_thread)
        handle_new_redditor_thread.start()

        handle_removed_redditor_thread = threading.Thread(
            target=handle_removed_redditor,
            args=(removed_redditors_queue, threads, STOP_EVENT),
        )
        handle_removed_redditor_thread.daemon = True
        non_redditor_threads.append(handle_removed_redditor_thread)
        handle_removed_redditor_thread.start()

        sent_message = False

        while not STOP_EVENT.is_set():

            if time.localtime().tm_hour == 22 and sent_message == False:
                print(
                    send_message(chat_ids=chat_ids, message="🕒Still running hihi🏃‍♂️‍➡️")
                )
                sent_message = True

            if time.localtime().tm_hour != 22:
                sent_message = False

            time.sleep(0.1)  # Reduce CPU usage

        print("joining threads")
        # Signal all threads to stop
        for thread in non_redditor_threads:
            thread.join()
            if thread.is_alive():
                print(f"Thread {thread.name} did not terminate.")

        for thread in threads:
            for inner_thread in thread["threads"]:
                inner_thread.join()
                if inner_thread.is_alive():
                    print(f"Thread {thread.name} did not terminate.")
        print("threads joined")

        send_message("shutting down⛔", chat_ids)
    except Exception as e:
        print(f"Exception in main loop: {e}")


if __name__ == "__main__":
    main()
