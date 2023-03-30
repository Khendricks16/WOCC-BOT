import asyncio
import json
import os
from sys import exit
from datetime import datetime

import ssl
import websockets

from bot import Bot
import logger_conf



# GroupMe account specific environment variables
GM_TK = os.getenv("GM_TK")
USER_ID = os.getenv("USER_ID")
GROUP_ID = os.getenv("GROUP_ID")
BOT_ID = os.getenv("BOT_ID")



async def establish_connection(websocket) -> None:
    """Connects the given websocket to the GroupMe's push service."""

    call_id = 1

    # Step 1: Handshake
    payload = [
      {
        "channel":"/meta/handshake",
        "version":"1.0",
        "supportedConnectionTypes":["websocket"],
        "id":f"{call_id}"
      }
    ]

    await websocket.send(json.dumps(payload))
    
    # Initialize returned clientId for remaining server call
    client_id = json.loads(await websocket.recv())[0]["clientId"]

    # Update call_id
    call_id += 1

    # Step 2: Subscribe to the user channel
    payload = [
      {
        "channel":"/meta/subscribe",
        "clientId":f"{client_id}",
        "subscription":f"/user/{USER_ID}",
        "id":f"{call_id}",
        "ext":
          {
            "access_token":f"{GM_TK}",
            "timestamp":int(datetime.now().timestamp())
          }
      }
    ]

    await websocket.send(json.dumps(payload))

    # Connection Status
    connection = json.loads(await websocket.recv())[0]["successful"]

    if connection:
        return
    else:
        raise websockets.exceptions.InvalidHandshake


async def main():
    # Initialize wocc_bot
    wocc_bot = Bot(GM_TK, USER_ID, GROUP_ID, BOT_ID, logger_conf.bot_logger)

    notifications_logger = logger_conf.notifications_logger

    # Ensure a TLS context is made
    context = ssl.create_default_context()

    if not isinstance(context, ssl.SSLContext):
        return


    # Set up websocket with push server
    async with websockets.connect("wss://push.groupme.com/faye", ssl=context, logger=logger_conf.websocket_logger) as ws:
        try:
            await establish_connection(ws)
        except websockets.exceptions.InvalidHandshake:
            return
        
        for i in range(1):
            # Get new alert from server
            push_data = json.loads(await ws.recv())

            # Handle incoming data
            
            notifications_logger.info(push_data[0]["data"]["alert"])

            # Check if messages was a command from a user and from the valid group chat
            user_message = push_data[0]["data"]["subject"]["text"]
            user_message_group_id = push_data[0]["data"]["subject"]["group_id"]

            if user_message.strip().casefold() in wocc_bot.commands.keys() and user_message_group_id == wocc_bot.group_id:
              # Create coroutine for the following Bot command
              asyncio.create_task(wocc_bot.commands[user_message.strip().casefold()]())
          
            

if __name__ == "__main__":
    asyncio.run(main())
    exit(0)