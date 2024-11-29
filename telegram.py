from utils.config import TELEGRAM_BOT_TOKEN
from utils.db import get_offset_db, save_offset_db
from utils.db import (
    add_redditor_db,
    list_redditors_db,
    mute_redditor_db,
    remove_redditor_db,
    unmute_redditor_db,
    give_rockets_db,
)
from reddit_observer import check_redditor_exists
import requests
import traceback


def handle_updates(reddit, created_redditor_queue, removed_redditor_queue):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    offset = get_offset_db() + 1
    try:
        updates = requests.get(url=url, params={"offset": offset}).json()
        if len(updates["result"]) != 0:
            save_offset_db(updates["result"][-1]["update_id"])
            for update in updates["result"]:
                print(f"received update :\n{update}")
                chat_id = update["message"]["from"]["id"]
                update_text = update["message"]["text"]
                if "/add" in update_text:
                    add_redditor(
                        chat_id,
                        update_text[len("/add") + 1 :].split(" "),
                        reddit,
                        created_redditor_queue,
                    )

                elif "/remove" in update_text:
                    remove_redditor(
                        chat_id,
                        update_text[len("/remove") + 1 :],
                        removed_redditor_queue,
                    )
                elif "/list" in update_text:
                    list_redditors(chat_id)
                elif "/mute" in update_text:
                    mute_redditor(chat_id, update_text[len("/mute") + 1 :].split(" "))
                elif "/unmute" in update_text:
                    unmute_redditor(chat_id, update_text[len("/unmute") + 1 :])
                elif "/giverockets" in update_text:
                    give_rockets(
                        chat_id, update_text[len("/giverockets") + 1 :].split(" ")
                    )

    except Exception as e:
        print(f"Error in telegram update handler: {e}")
        print(traceback.format_exc())


def send_message(message, chat_ids):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    response = []
    for id in chat_ids:
        params = {"chat_id": id, "text": message}

        response.append(requests.post(url, data=params).json())
    return response


def add_redditor(chat_id, args, reddit, created_redditors_queue):
    if len(args) != 2:
        send_message(
            chat_ids=[chat_id],
            message="💩missing arguments: /add <redditor> <rating 1-10>",
        )
    elif not check_redditor_exists(reddit, args[0]):
        send_message(chat_ids=[chat_id], message="💩redditor does not exist")
    elif int(args[1]) < 1 or int(args[1]) > 10:
        send_message(chat_ids=[chat_id], message="💩rating must be between 1 - 10")
    else:
        add_redditor_db(args[0], args[1])
        created_redditors_queue.put(tuple(args))
        send_message(chat_ids=[chat_id], message=f"{args[0]} has been added👀")


def list_redditors(chat_id):
    redditors = list_redditors_db()
    message = "redditors:\n"
    for redditor in redditors:
        message += redditor[0] + "\nrating:  " + int(redditor[1]) * "🚀" + "\n"
    send_message(message=message, chat_ids=[chat_id])


def mute_redditor(chat_id, args):
    redditors = list_redditors_db()
    redditors = [redditor[0] for redditor in redditors]
    if len(args) != 2:
        send_message(
            chat_ids=[chat_id],
            message="💩missing argument. correct ussage: /mute <redditor> <days>",
        )
    elif args[0] not in redditors:
        send_message(
            chat_ids=[chat_id], message="💩redditor to mute could not be found"
        )
        list_redditors(chat_id)
    else:
        mute_redditor_db(args[0], args[1])
        send_message(
            chat_ids=[chat_id], message=f"{args[0]} is now muted for {args[1]} days🤫"
        )


def remove_redditor(chat_id, redditor, removed_redditor_queue):
    redditors = list_redditors_db()
    redditors = [redditor[0] for redditor in redditors]
    if redditor not in redditors:
        send_message(
            message=f"💩couldn't find {redditor} in database. check spelling",
            chat_ids=[chat_id],
        )
    elif remove_redditor_db(redditor=redditor):
        send_message(message="removed redditor👋", chat_ids=[chat_id])
        list_redditors(chat_id=chat_id)
        removed_redditor_queue.put(redditor)
    else:
        send_message(
            message="💩couldnt remove redditor. check spelling.", chat_ids=[chat_id]
        )


def unmute_redditor(chat_id, redditor):
    redditors = list_redditors_db()
    redditors = [redditor[0] for redditor in redditors]

    if redditor not in redditors:
        send_message(
            chat_ids=[chat_id], message="💩redditor to mute could not be found"
        )
        list_redditors(chat_id)
    else:
        unmute_redditor_db(redditor)
        send_message(chat_ids=[chat_id], message=f"{redditor} unmuted👀")


def give_rockets(chat_id, args):
    redditors = list_redditors_db()
    redditors = [redditor[0] for redditor in redditors]

    if len(args) != 2:
        send_message(
            chat_ids=[chat_id],
            message="💩missing argument. correct ussage: /giverockets <redditor> <amount>",
        )

    elif args[0] not in redditors:
        send_message(
            chat_ids=[chat_id], message="💩redditor to promote could not be found"
        )
        list_redditors(chat_id)

    else:
        give_rockets_db(args[0], args[1])
        send_message(message=f"changed rating of {args[0]}", chat_ids=(chat_id,))
