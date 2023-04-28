import logging
from logging.handlers import RotatingFileHandler



# Websocket Logger

websocket_RFH = RotatingFileHandler(
       "./Logs/websocket.log", 
       mode="a",
       maxBytes=10_000,
       backupCount=5,
       encoding='utf-8',
   )


formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%m/%d/%Y %I:%M:%S %p")
websocket_RFH.setFormatter(formatter)


websocket_logger = logging.getLogger("websockets.client")
websocket_logger.addHandler(websocket_RFH)
websocket_logger.setLevel(logging.INFO)

# Notification logger

notifications_RFH = RotatingFileHandler(
       "./Logs/notifications.log", 
       mode="a",
       maxBytes=10_000,
       backupCount=5,
       encoding='utf-8',
   )

notifications_RFH.setFormatter(formatter) # Use the same formatter as the websocket_logger


notifications_logger = logging.getLogger("notifications")
notifications_logger.setLevel(logging.DEBUG)
notifications_logger.addHandler(notifications_RFH)


# Bot logger

Bot_RFH = RotatingFileHandler(
       "./Logs/bot_actions.log", 
       mode="a",
       maxBytes=10_000,
       backupCount=5,
       encoding='utf-8',
   )


formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(funcName)s | %(message)s", "%m/%d/%Y %I:%M:%S %p")
Bot_RFH.setFormatter(formatter)


bot_logger = logging.getLogger("bot")
bot_logger.setLevel(logging.DEBUG)
bot_logger.addHandler(Bot_RFH)