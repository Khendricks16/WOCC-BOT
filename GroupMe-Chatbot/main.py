import asyncio
import json
import os
from sys import exit

import ssl
import websockets

from push_service_helpers import new_signature, poll_events
from bot import Bot
import logger_conf



# GroupMe account specific environment variables
GM_TK = os.getenv("GM_TK")
USER_ID = os.getenv("USER_ID")
GROUP_ID = os.getenv("GROUP_ID")
BOT_ID = os.getenv("BOT_ID")



async def handle_new_data(message: str, websocket, wocc_bot, notifications_logger) -> None:
  """Handles incoming push event data.""" 
  
  # Load the JSON data from message
  push_data = json.loads(message)
  
  # Check for any type of reconnectivity to push service
  try:            
    if not push_data[0]["advice"]["reconnect"] == "retry":
      raise KeyError

    # If the call id is 8 meaning an hour has passed after the first poll for events
    # (first poll id starts after 2: 8 - 2 = 6 -> 60 minutes as polls timeout after 10 minutes each),
    # close the connection in order for a new signature to be accquired without the push service
    # forcing the connection closed as more than one signature is trying to be on one TCP connection.
    if push_data[0]["id"] == "8":
      await websocket.close()
    else:
      await poll_events(websocket)
  except (KeyError, IndexError):
    # Any of the above errors that may result, means no reconnectivity is needed
    pass
  else:
    return
  
  # Check if new push event was a text message from a group chat
  try:
    user_message = (push_data[0]["data"]["subject"]["text"]).strip().casefold()
    user_message_group_id = push_data[0]["data"]["subject"]["group_id"]
    user_id = push_data[0]["data"]["subject"]["user_id"] # For checking against admin whitelist
  except (KeyError, IndexError):
    return

  notifications_logger.info(push_data[0]["data"]["alert"])

  # Check if the text message was from the valid group chat
  if user_message_group_id != wocc_bot.group_id:
    return
  # Check for no text whatsoever inside of message
  elif not user_message:
    return
  
  # Check if the text message was a Bot command 
  if user_message in wocc_bot.commands.keys():
    # Create coroutine for the following Bot command
    asyncio.create_task(wocc_bot.commands[user_message]())
    return
  
  # Check if the text message was an Admin Bot command
  with open("admin_whitelist.json", "r") as file:  
    whitelist = json.load(file)

  if user_message in wocc_bot.admin_commands.keys() and user_id in whitelist:
    # Create coroutine for the following Admin Bot command
    
    if user_message == "$smgs on": # Names this task, so wocc_bot.smgs_off() can cancel it
      # Do nothing if scheduled messages are already turned on
      tasks = asyncio.all_tasks()
      for task in tasks:
          if task.get_name() == "smgs":
            return
            
      asyncio.create_task(wocc_bot.admin_commands[user_message](), name="smgs")
      asyncio.create_task(wocc_bot.post("Scheduled messages turned on")) # Done outside of acutal Bot method in order to not post message when the program starts
    else:
      asyncio.create_task(wocc_bot.admin_commands[user_message]())
    return 
  # Admin command was called from non-admin
  elif user_message in wocc_bot.admin_commands.keys():
    asyncio.create_task(wocc_bot.post("Permission denied"))
    return 

  # Respond in group chat with an invalid command message if what looks like a command isn't.
  if user_message[0] == "$" and user_message[1:4].isalpha():
    asyncio.create_task(wocc_bot.post("Unknown command"))


async def main():
    # Initialize wocc_bot
    wocc_bot = Bot(GM_TK, USER_ID, GROUP_ID, BOT_ID, logger_conf.bot_logger)
    
    # Turn on schedueld messages by default
    asyncio.create_task(wocc_bot.admin_commands["$smgs on"](), name="smgs")

    # Logger used to log all real GroupMe app notifications
    notifications_logger = logger_conf.notifications_logger

    # Ensure a TLS context is made for websocket, otherwise system will exit with exit code 1
    context = ssl.create_default_context()

    if not isinstance(context, ssl.SSLContext):
        logger_conf.websocket_logger.fatal("Failed to create TLS context")
        exit(1)


    # Open websocket connection to GroupMe's push service
    # Uses infinite asynchronous iterator to reconnect automatically on errors 
    async for websocket in websockets.connect("wss://push.groupme.com/faye", ssl=context, logger=logger_conf.websocket_logger):    
        try:
          #Obtain new signature that is able to poll for push events
          await new_signature(websocket, USER_ID, GM_TK)

          # Poll for push events
          await poll_events(websocket)

          # Asynchronous iterations through incoming push messages 
          async for message in websocket: 
            await handle_new_data(message, websocket, wocc_bot, notifications_logger)
        
        except websockets.ConnectionClosed:
          logger_conf.websocket_logger.warning("Websocket Connection was unexpectedly closed")
          continue
          


if __name__ == "__main__":
    asyncio.run(main())
    exit(0)