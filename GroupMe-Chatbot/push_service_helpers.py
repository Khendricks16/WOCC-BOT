import asyncio
import json
from datetime import datetime
from sys import exit



async def new_signature(websocket, user_id, gm_tk) -> None:
    """
    Creates a new signature with the GroupMe push service for the account on behalf of the API token.
    This signature will be subscribed to receive push events from the user channel.

    Creates two global variables: client_id, call_id

    client_id -> id used to represent the signature
    call_id -> numeric value that represents the ith call to the server

    NOTE: The documentation says that the signature must refresh every hour.
          Also, if getting new signature fails, the program will exit with exit code 1.
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
        "subscription":f"/user/{user_id}",
        "id":f"{call_id}",
        "ext":
          {
            "access_token":f"{gm_tk}",
            "timestamp":int(datetime.now().timestamp())
          }
      }
    ]

    await websocket.send(json.dumps(payload))

    # Update call_id
    call_id += 1

    # Log subscription status
    subscription = json.loads(await websocket.recv())[0]["successful"]

    if subscription:
      websocket.logger.info("New Signature Successful")
      return
    else:
      websocket.logger.critical("New Signature Failed")
      exit(1)


async def poll_events(websocket) -> None:
  """
  Polls the GroupMe push service for events that you are subscribed to receive.
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