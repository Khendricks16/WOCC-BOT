import asyncio
import json
import requests
import os
import time

import training_schedule


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
    

    @property 
    def admin_commands(self):
        """All of the user interactive Bot commands available only to admins of the groupchat."""

        admin_commands = {
            "$schedule post": self.schedule_post,
            "$schedule clear": self.schedule_clear
        }

        return admin_commands


    async def post(self, text: str) -> None:
        """Sends textual post to the bots group chat with the given text."""

        payload = {
            "bot_id": self.id,
            "text": text
        }

        # Hit API with request to post a message to the bots group chat
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

        message = ""
        
        # Add both the list of commands with its following function doc string to the message
        for command, func in self.commands.items():
            message += f"[ {command} ]: {func.__doc__}\n\n"
        
        message += f"\n\nADMIN ONLY:\n{'-' * 35}\n\n"

        for command, func in self.admin_commands.items():
            message += f"[ {command} ]: {func.__doc__}\n\n"

        self.log.info("[ $help ] command ran")

        # Post message with commands and their descriptions
        asyncio.create_task(self.post(message))
    
    async def schedule_link(self):
        """Posts the link to the Google Sheets on where the weekly schedule can be found."""
        
        # Post link to group chat
        asyncio.create_task(self.post(os.getenv("SPREADSHEET_LINK")))

    async def schedule_post(self):
        """Posts the weekly training schedule inside the group chat in a prettiful format."""
        message_data = await training_schedule.gather_data()
        messages = [] # Contains all schedule messages that will be posted
        MAX_MSG_LEN = 1000
        curr_msg = ""

        # Add heading to msg
        curr_msg += "*Training for the week*"
        curr_msg += f"\n{'-' * len(curr_msg)}"

        # New line style for body of message
        nl = "\n|"

        # Function used to determine if a new message should be created and eventually appended to messages if curr_msg exceeds MAX_MSG_LEN
        exceeds_msg_limit = lambda new_section, msg: True if len(msg) + len(new_section) > MAX_MSG_LEN else False

        for location in message_data:
            # Sub heading in msg for FOH, BOH, GTS
            sub_heading = f"{nl} {nl}+----+{nl} {location} |{nl}+----+{nl}"
            
            # Add subheading to msg
            if exceeds_msg_limit(sub_heading, curr_msg):
                messages.append(curr_msg)
                curr_msg = ""
            
            curr_msg += sub_heading

            # Section for coaches in msg
            for coach_schedule in message_data[location]:
                coach_section = ""

                # Disregard adding new section to msg if coach isn't training anyone that week
                if len(coach_schedule) <= 1:
                    continue
                
                # Add a divider for section
                coach_section +=  f"{nl}{'_' * 22}"
                # Title coach section
                coach_section += f"{nl} ({coach_schedule[0]}){nl}"

                # Add schedule for coach to coach section
                schedule = iter(coach_schedule[1:])
                try:
                    for day in ["Mon.", "Tue.", "Wed.", "Thu.", "Fri.", "Sat."]:
                        trainee, st, et = next(schedule), next(schedule), next(schedule)

                        # Continue if coach is not training anybody for that day but is sometime in the rest of the week
                        if not all([trainee, st, et]):
                            continue

                        coach_section += f"{nl} {day} -> {trainee} ({st}-{et})"
                except StopIteration:
                    pass
                
                # Add coach section to 
                if exceeds_msg_limit(coach_section, curr_msg):
                    messages.append(curr_msg)
                    curr_msg = ""
                
                curr_msg += coach_section


        messages.append(curr_msg)
        self.log.info("[ $schedule post ] command ran")

        # Post formulated message
        for msg in messages:
            asyncio.create_task(self.post(msg))

    
    async def schedule_clear(self):
        """Completely clears all weekly training schedule data inside of the tables in the google sheet."""
        
        # Clear training schedule
        asyncio.create_task(training_schedule.clear())
        
        self.log.info("[ $schedule clear ] command ran")
        asyncio.create_task(self.post("Successfully cleared training schedule."))

