import asyncio
import json
import os
from sys import exit

import ssl
import websockets

from bot import Bot
import logger_conf
from push_service_helpers import new_signature, poll_events



# GroupMe account specific environment variables
GM_TK = os.getenv("GM_TK")
USER_ID = os.getenv("USER_ID")
GROUP_ID = os.getenv("GROUP_ID")
BOT_ID = os.getenv("BOT_ID")



async def handle_new_data(message: str, websocket, wocc_bot, notifications_logger) -> None:
  """Handles incoming push event data.""" 
  
  # Load the JSON data from message
  try: 
    push_data = json.loads(message)
  except UnicodeEncodeError: # Ignore all pictures, gifs, etc.
    return
  
  # Check if current poll is about to timeout
  try:            
    if push_data[0]["advice"]["reconnect"] == "retry":
      await poll_events(websocket)
  except (KeyError, IndexError):
    pass
  else:
    return
  
  # Check if new push event was a text message from a group chat
  try:
    user_message = (push_data[0]["data"]["subject"]["text"]).strip().casefold()
    user_message_group_id = push_data[0]["data"]["subject"]["group_id"]
  except (KeyError, IndexError):
    return

  notifications_logger.info(push_data[0]["data"]["alert"])

  # Check if that text message was a Bot command and was from the valid group chat
  if user_message in wocc_bot.commands.keys() and user_message_group_id == wocc_bot.group_id:
    # Create coroutine for the following Bot command
    asyncio.create_task(wocc_bot.commands[user_message.strip().casefold()]())
  # Respond in group chat with an invalid command message if what looks like a command isn't.
  elif user_message[0] == "$" and user_message[1:4].isalpha():
    asyncio.create_task(wocc_bot.post("Unknown command"))


async def main():
    # Initialize wocc_bot
    wocc_bot = Bot(GM_TK, USER_ID, GROUP_ID, BOT_ID, logger_conf.bot_logger)

    # Logger used to log all real GroupMe app notifications
    notifications_logger = logger_conf.notifications_logger

    # Ensure a TLS context is made for websocket, otherwise system will exit with exit code 1
    context = ssl.create_default_context()

    if not isinstance(context, ssl.SSLContext):
        logger_conf.websocket_logger.fatal("Failed to create TLS context")
        exit(1)

    # Open websocket connection to GroupMe's push service
    async with websockets.connect("wss://push.groupme.com/faye", ssl=context, logger=logger_conf.websocket_logger) as websocket:    
        # Obtain new signature that is able to poll for push events
        await new_signature(websocket, USER_ID, GM_TK)

        # Poll for push events
        await poll_events(websocket)

        # Infinite asynchronous iterations through incoming push messages 
        async for message in websocket: 
          await handle_new_data(message, websocket, wocc_bot, notifications_logger)
          


if __name__ == "__main__":
    asyncio.run(main())
    exit(0)