import asyncio
import json
import requests
import os
import time


class Bot:
    

    API_URL = "https://api.groupme.com/v3"


    def __init__(self, token: str, user_id: str, group_id: str, id: str, logger: object):
        """
        Parameters:

        token -> The GroupMe API token this bot will use in order to authenticate requests
        user_id -> The GroupMe userid this bot will repersent
        group_id -> the GroupMe groupid that this bot chat to
        id -> The GroupMe botid identifying which bot to use
        logger -> Logging object used to create log messages
        """

        self.token = token
        self.user_id = user_id 
        self.group_id = group_id
        self.id = id

        self.log = logger

    
    @property
    def commands(self):
        """All of the user interactive Bot commands"""
        commands = { 
            "$status": self.status,
            "$day1": self.day_one,
            "$store #": self.store_number,
            "$policy manual": self.policy_manual,
            "$help": self.help
        }

        return commands


    async def post(self, text: str) -> None:
        """Sends textual post to the bots group chat with the given text."""

        payload = {
            "bot_id": self.id,
            "text": text
        }

        # Hit API with request to post a message to the group chat
        r = requests.post(f"{self.API_URL}/bots/post?token={self.token}", json=payload)
        self.log.info("Bot posted a message")
    

    async def status(self):
        """Returns the status of which systems are opertaional or not. If no response is returned, then all systems are offline."""

        self.log.info("[ $status ] command ran")

        # Post message notifying that systems are online.
        asyncio.create_task(self.post("All systems operational \U0001F7E2"))
        
    
    async def store_number(self):
        """Returns the store number for the store location."""

        message = f"Store Number: {os.getenv('STORE_NUMBER')}"
        
        self.log.info("[ $store # ] command ran")
        
        # Post store number message
        asyncio.create_task(self.post(message))
        
    
    async def day_one(self):
        """Returns helpful links for day one coaching."""

        self.log.info("[ $day1 ] command ran")
        
        # Start message out with the link to the day one guide
        # THIS WILL MAKE THE AUTOMATIC INTEGRATED MESSAGE POPUP THIS URL
        message = os.getenv("DAY1_URL")

        # Add other helpful links to message 
        GroupMe_app_link = "https://apps.apple.com/us/app/groupme/id392796698"
        HSTeam_app_link = "https://apps.apple.com/us/app/hs-team-app/id1195686320"

        message += f"\n\nGroupMe -> {GroupMe_app_link}"
        message += f"\n\nHotSchedules -> {HSTeam_app_link}"

        # Post message
        asyncio.create_task(self.post(message))


    async def policy_manual(self):
        """Returns store's policy manual."""

        self.log.info("[ $policy manual ] command ran")

        # Post link to policy manual
        asyncio.create_task(self.post(os.getenv("POLICY_MANUAL_URL")))


    async def help(self):
        """Displays all of the available Bot commands.""" 

        message = str()
        
        # Add both the list of commands with its following function doc string to the message
        for command, func in self.commands.items():
            message += f"[ {command} ]: {func.__doc__}\n\n"
            
        self.log.info("[ $help ] command ran")

        # Post message with commands and their descriptions
        asyncio.create_task(self.post(message))