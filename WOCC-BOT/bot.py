import asyncio
import json
import requests
import os
import time
import datetime

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
            "$schedule clear": self.schedule_clear,
            "$smgs on": self.smgs_on,
            "$smgs off": self.smgs_off,
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
        schedule_data = await training_schedule.gather_data()
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

        for location in schedule_data:
            # Sub heading in msg for FOH, BOH, GTS
            sub_heading = f"{nl} {nl}+----+{nl} {location} |{nl}+----+{nl}"

            # Section for coaches in msg
            coach_sections = []
            for coach_schedule in schedule_data[location]:
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

                        coach_section += f"{nl} {day} -> {trainee.title()} ({st}-{et})"
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
        
        # Clear training schedule
        asyncio.create_task(training_schedule.clear())
        
        self.log.info("[ $schedule clear ] command ran")
        asyncio.create_task(self.post("Successfully cleared training schedule."))

    async def smgs_on(self):
        """Activates scheduled reminders to be posted within the chat for coaches to update their tracker for the day. (This is turned on by default when the bot comes online)."""
        
        self.log.info("Scheduled messages was turned on")
        
        schedule_data = await training_schedule.gather_data()
       
        AUTOMATED_MSG = "THIS IS AN AUTOMATED MSG:\n\nHey coaches! remember to update the coaching tracker for any trainee that you trained today.\n\nThanks :)"

        # Get which days coaches are coaching
        training_days = {i: False for i in range(7)} # 0 (Monday) - 6 (Saturday)

        for data in schedule_data.values():
            for coach_schedule in data:
                iter_data = iter(coach_schedule[1:])
                try:
                    for day in range(7):
                        trainee, st, et = next(iter_data), next(iter_data), next(iter_data)

                        # If any coach is training someone during the week day, then set that day as a "training day"
                        if all([trainee, st, et]):
                            training_days[day] = True
                        else:
                            continue

                except StopIteration:
                    pass

        today = datetime.datetime.now()

        # Set the values of training days to a tuple of datetimes as to when a scheduled message should occur that day
        for day in training_days:
            if not training_days[day]:
                continue
            
            # Get the day of the month for day
            day_of_month = today.day + (day - today.weekday())
            
            # Scheduled times are 3:00PM & 9:00PM for Mon-Thur
            # but 3:00PM & 10:00PM for Fri-Sat
            if day == 4 or day == 5:
                training_days[day] = (datetime.datetime(today.year, today.month, day_of_month, 15),
                                    datetime.datetime(today.year, today.month, day_of_month, 22) 
                )
            else:
                training_days[day] = (datetime.datetime(today.year, today.month, day_of_month, 15),
                                    datetime.datetime(today.year, today.month, day_of_month, 21) 
                )

        # Fill queue of await times of seconds between scheduled messages
        await_queue = []
        for day in training_days:
            if training_days[day]:
                schedule_time = training_days[day]
                delay_duration1 = (schedule_time[0] - today).total_seconds()
                delay_duration2 = (schedule_time[1] - today).total_seconds()
                

                for delay in [delay_duration1, delay_duration2]:
                    if delay > 0: # Any times that have already passed, don't add to queue
                        await_queue.append(delay)

    
        await_queue.sort()
        # Post AUTOMATED_MSG at all scheduled times
        for i, time in enumerate(await_queue):
            if i == 0:
                await asyncio.sleep(time)
            else:
                await asyncio.sleep(time - sum(await_queue[:i]))

            asyncio.create_task(self.post(AUTOMATED_MSG))


        # Finished all automated messages for the week
        self.log.info("All scheduled messages has finished")
        return
         
    async def smgs_off(self):
        """Turns off scheduled reminders messages if turned on."""
        tasks = asyncio.all_tasks()
        for task in tasks:
            if task.get_name() == "smgs":
                task.cancel()
                asyncio.create_task(self.post("Scheduled messages turned off"))
                self.log.info("Scheduled messages task was canceled")

