import asyncio
import json
import requests
import os
import datetime

import training_schedule


class Bot:
    

    API_URL = "https://api.groupme.com/v3"


    def __init__(self, token: str, user_id: str, group_id: str, id: str, logger: object):
        """
        Parameters:

        token -> The GroupMe API token this bot will use in order to authenticate requests
        user_id -> The GroupMe userid this bot will represent
        group_id -> The GroupMe groupid that this bot chat too
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
            "$schedule link": self.schedule_link,
            "$help": self.help
        }

        return commands
    

    @property 
    def admin_commands(self):
        """All of the user interactive Bot commands available only to admins of the groupchat."""

        admin_commands = {
            "$schedule post": self.schedule_post,
            "$schedule clear": self.schedule_clear,
            "$smsgs on": self.smsgs_on,
            "$smsgs off": self.smsgs_off,
        }

        return admin_commands


    async def post(self, text: str) -> None:
        """Sends a textual post to the bots group chat with the given text."""

        payload = {
            "bot_id": self.id,
            "text": text
        }

        # Hit API with request to post a message to the bots group chat
        r = requests.post(f"{self.API_URL}/bots/post?token={self.token}", json=payload)
        self.log.info("Bot posted a message")
    

    async def status(self):
        """Returns the status of which systems are operational  or not. If no response is returned, then all systems are offline."""

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
        
        # Start message out with the link to the day one guide online
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
        """Returns the stores policy manual."""

        self.log.info("[ $policy manual ] command ran")

        # Post link to the policy manual
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
        
        # Let the chat know that the google sheets api call may take a minute
        await self.post("Getting the schedule, this may take a minute...")
        
        # Obtain schedule data
        schedule_data = await training_schedule.gather_data()
        messages = [] # Contaisns all the schedule messages that will be posted
        MAX_MSG_LEN = 1000
        curr_msg = ""

        # Add heading to msg
        curr_msg += "\U0001F4E2 Training for the week \U0001F4E2"

        # Function used to determine if a new message should be created and eventually appended to messages if curr_msg exceeds MAX_MSG_LEN
        exceeds_msg_limit = lambda new_section, msg: True if len(msg) + len(new_section) > MAX_MSG_LEN else False

        for location in schedule_data:
            # Sub heading in msg for FOH, BOH, GTS
            sub_heading = f"\n\n~ {location[:3]} ~"

            # Section for coaches in msg
            coach_sections = []
            for coach_schedule in schedule_data[location]:
                coach_section = ""

                # Disregard adding new section to msg if coach isn't training anyone that week
                if len(coach_schedule) <= 1:
                    continue
                
                # Title coach section
                coach_section += f"\n\n{coach_schedule[0]}"

                # Add schedule for coach to coach section
                schedule = iter(coach_schedule[1:])
                try:
                    for day in ["Mon.", "Tue.", "Wed.", "Thu.", "Fri.", "Sat."]:
                        trainee, st, et = next(schedule), next(schedule), next(schedule)

                        # Continue if coach is not training anybody for that day but is sometime in the rest of the week
                        if not all([trainee, st, et]):
                            continue

                        coach_section += f"\n| {day} - {trainee.title()} ({st}-{et})"
                except StopIteration:
                    pass
                
                # Add coach section to list of sections for the location
                coach_sections.append(coach_section)
            
            # Don't add subheading or any coach sections if no real data for that location is present
            if not any(coach_sections):
                continue
            
            # Add sub heading to msg
            if exceeds_msg_limit(sub_heading, curr_msg):
                messages.append(curr_msg)
                curr_msg = ""
            
            curr_msg += sub_heading
            
            # Add all coach sections right under sub heading to msg
            for section in coach_sections:

                if exceeds_msg_limit(section, curr_msg):
                    messages.append(curr_msg)
                    curr_msg = ""
                
                curr_msg += section


        messages.append(curr_msg)
        self.log.info("[ $schedule post ] command ran")

        # Post formulated message
        for msg in messages:
            asyncio.create_task(self.post(msg))

    
    async def schedule_clear(self):
        """Completely clears all weekly training schedule data inside of the tables in the google sheet."""
        
        # Let the chat know that the google sheets api call may take a minute
        await self.post("Clearing the schedule, this may take a minute...")
        
        # Clear training schedule
        await training_schedule.clear()
        
        self.log.info("[ $schedule clear ] command ran")
        asyncio.create_task(self.post("Successfully cleared training schedule."))

    async def smsgs_on(self):
        """Activates scheduled reminders to be posted within the chat every (Mon., Wed., and Fri.) for coaches to update their tracker (This is turned on by default when the bot comes online)."""
        # Note: Scheduled messages of reminders for coaches to update their tracker will be set to occur every Mon., Wed., and Fri. at 8PM EST.

        self.log.info("Scheduled messages was turned on")
        AUTOMATED_MSG = "THIS IS AN AUTOMATED MSG:\n\nHey coaches! remember to update the coaching tracker for any trainee that you trained today.\n\nThanks :)"
        

        # Infinite loop to keep posting these scheduled messages so long as the coroutine exists
        while (True):            
            today = datetime.datetime.today()
            monday = today - datetime.timedelta(days=today.weekday())
            wednesday = monday + datetime.timedelta(days=2)
            friday = wednesday + datetime.timedelta(days=2)

            # Check for if all sheduled messages for the week would have already been posted
            last_smsg_time = datetime.datetime(friday.year, friday.month, friday.day, hour=20)
            curr_time = datetime.datetime.now()
            if (curr_time - last_smsg_time).total_seconds() > 0:
                # Wait till next monday rolls around, then start new iteration in while loop
                self.log.info("All weekly smsgs times have passed, awaiting until next monday")
                next_monday = monday + datetime.timedelta(days=7)
                await asyncio.sleep((next_monday - curr_time).total_seconds())
                continue


            # Get the string representation of the current week (ie. 6/22 - 6/26)
            week_repr = f"{monday.month}/{monday.day} - {friday.month}/{friday.day}"
            self.log.info(f"Starting scheduled messsages for the week of {week_repr}")

            
            # Fill queue with the difference in seconds between today and each of the scheduled dates
            smsgs_queue = []
            for date in (monday, wednesday, friday):
                # Difference between now and the date @ 8PM in total seconds
                diff = (datetime.datetime(date.year, date.month, date.day, hour = 20) - curr_time).total_seconds()

                # Don't add scheduled time if it has already passed
                if diff < 0:
                    continue
                else:
                    smsgs_queue.append(diff)
            smsgs_queue.sort()
    
            # Post AUTOMATED_MSG at all scheduled times in smsgs_queue
            for i, time in enumerate(smsgs_queue):
                if i == 0:
                    await asyncio.sleep(time)
                else:
                    # Accounts for the time already awaited/passed from the previous scheduled time, when awaiting the next time
                    await asyncio.sleep(time - sum(smsgs_queue[:i]))

                asyncio.create_task(self.post(AUTOMATED_MSG))

            # Finished all automated messages for the week
            self.log.info("Week of scheduled messages has finished")
            
         
    async def smsgs_off(self):
        """Turns off scheduled reminder messages if turned on."""
        tasks = asyncio.all_tasks()
        for task in tasks:
            if task.get_name() == "smsgs":
                task.cancel()
                asyncio.create_task(self.post("Scheduled messages turned off"))
                self.log.info("Scheduled messages task was canceled")
                return
        
        asyncio.create_task(self.post("Scheduled messages have already been turned off"))
