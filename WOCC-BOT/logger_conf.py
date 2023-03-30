import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler



# Websocket Logger

class LoggerAdapter(logging.LoggerAdapter):
   """Add connection ID and client IP address to websockets logs."""
   def process(self, msg, kwargs):
       try:
           websocket = kwargs["extra"]["websocket"]
       except KeyError:
           return msg, kwargs
       xff = websocket.request_headers.get("X-Forwarded-For")
       return f"{websocket.id} {xff} {msg}", kwargs


TRFH = TimedRotatingFileHandler(
       "./Logs/websocket.log", 
       when="H",
       interval=1,
       backupCount=5,
       encoding='utf-8',
   )


formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%m/%d/%Y %I:%M:%S %p")
TRFH.setFormatter(formatter)


websocket_logger = logging.getLogger("websockets.client")
websocket_logger.addHandler(TRFH)
websocket_logger.setLevel(logging.INFO)
websocket_logger = LoggerAdapter(websocket_logger, None)


# Notification logger

notifications_RFH = RotatingFileHandler(
       "./Logs/notifications.log", 
       mode="a",
       maxBytes=10_000,
       backupCount=5,
       encoding='utf-8',
   )


formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%m/%d/%Y %I:%M:%S %p")
notifications_RFH.setFormatter(formatter)


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