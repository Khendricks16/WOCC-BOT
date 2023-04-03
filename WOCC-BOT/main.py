import asyncio
import json
import os
from sys import exit
from datetime import datetime
from time import time

import ssl
import websockets

from bot import Bot
import logger_conf



# GroupMe account specific environment variables
GM_TK = os.getenv("GM_TK")
USER_ID = os.getenv("USER_ID")
GROUP_ID = os.getenv("GROUP_ID")
BOT_ID = os.getenv("BOT_ID")



async def new_signature(websocket) -> None:
    """
    Creates a new signature with the GroupMe push service for the account on behalf of the API token.
    This signature will be subscribed to recive push events from the user channel.
    These signatures according to the documentation must be refreshed every hour.

    Creates two global variables: client_id, call_id

    client_id -> id used to represent the signature
    call_id -> numeric value that represents the ith call to the server

    NOTE: If signature fails, program will exit with exit code 1.
    """

    # Handshake
    global call_id
    call_id = 1

    payload = [
      {
        "channel":"/meta/handshake",
        "version":"1.0",
        "supportedConnectionTypes":["websocket"],
        "id":f"{call_id}"
      }
    ]

    await websocket.send(json.dumps(payload))
    
    # Initialize returned clientId for the signature
    global client_id
    client_id = json.loads(await websocket.recv())[0]["clientId"]

    # Update call_id
    call_id += 1

    # Subscribe to the user channel
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

    # Log subscription status
    subscription = json.loads(await websocket.recv())[0]["successful"]

    if subscription:
      websocket.logger.info("New Signature Successful")
      return
    else:
      websocket.logger.fatal("New Signature Failed")
      exit(1)



async def poll_events(websocket):
  """
  Polls the GroupMe push service for events that you are subscribed to recieve.
  Poll times out after 600000 ms (10 minutes).
  """

  global client_id
  global call_id

  payload = [
    {
      "channel":"/meta/connect",
      "clientId":f"{client_id}",
      "connectionType":"websocket",
      "id":f"{call_id}"
    }
  ]

  await websocket.send(json.dumps(payload))
  
  # Update call_id
  call_id += 1



async def main():
    # Initialize wocc_bot
    wocc_bot = Bot(GM_TK, USER_ID, GROUP_ID, BOT_ID, logger_conf.bot_logger)

    # Logger used to log all real GroupMe app notifications
    notifications_logger = logger_conf.notifications_logger

    # Ensure a TLS context is made, otherwise system will exit with exit code 1
    context = ssl.create_default_context()

    if not isinstance(context, ssl.SSLContext):
        logger_conf.websocket_logger.fatal("Failed to create TLS context")
        exit(1)

    # Open websocket connection to GroupMe's push service
    async with websockets.connect("wss://push.groupme.com/faye", ssl=context, logger=logger_conf.websocket_logger) as websocket:    
        # Obtain new signature that is able to poll for push events
        await new_signature(websocket)
        signature_time= time()

        # Poll for push events
        await poll_events(websocket)

        # Infinite asynchronous iterations through incoming push messages 
        async for message in websocket:
          # Handle incoming push event data   

          try: 
            push_data = json.loads(message)
          except UnicodeEncodeError: # Ignore all pictures, gifs, etc.
            continue

          # Check for any needed network reconnections
          try:
            # Check if signature needs to be refreshed (after 1hr)
            if (time() - signature_time) >= 3600:
              await new_signature(websocket)
              signature_time = time()
            # Check if current poll is about to timeout
            elif push_data[0]["advice"]["reconnect"] == "retry":
              await poll_events(websocket)
          except (KeyError, IndexError):
            pass
          else:
            continue
          
          # Check if new push event was a text message from a group chat
          try:
            user_message = push_data[0]["data"]["subject"]["text"]
            user_message_group_id = push_data[0]["data"]["subject"]["group_id"]
          except (KeyError, IndexError):
            continue

          notifications_logger.info(push_data[0]["data"]["alert"])

          # Check if that text message was a Bot command and was from the valid group chat
          if user_message.strip().casefold() in wocc_bot.commands.keys() and user_message_group_id == wocc_bot.group_id:
            # Create coroutine for the following Bot command
            asyncio.create_task(wocc_bot.commands[user_message.strip().casefold()]())



if __name__ == "__main__":
    asyncio.run(main())
    exit(0)