# WOCC-BOT #
A Chatbot made for the GroupMe mobile messaging app to be used within my workplace. More specifically, this bot was made as a helpful utility tool for the coaches to help train and grow new team members into excellence. 

https://github.com/Khendricks16/WOCC-BOT/assets/105130972/343cc56d-d4ce-4ff3-bf63-3d567d3b173b

# Functionalities #
* Interactive commands for coaches to return helpful links and information
* Formulates and posts a text-based version of the training schedule found on google sheets
* Posts scheduled messages and reminders for coaches


# I'm a Coach, How Do I Use it?
This bot within the group chat is just like any other group chat member, with the only difference being its programmatic responses to the group's messages. It should be on 24/7 and can be used at any time throughout the day or night unless there is scheduled maintenance. The username of the bot should be WOCC BOT with its profile picture being [this](https://github.com/Khendricks16/GroupMe-Chatbot/blob/master/WOCC-BOT/avatar.jpg?raw=true).




## *Using The Bot* ##
To interact and use this bot, type any one of its commands starting with the "$" character.


For example to see if the bot is running type into the chat:
```txt
$status
```
<img src="./Example-Photos/[ $status ] Command.PNG" alt="[ $status ] Example" style="display: block; margin-left: auto; margin-right: auto; width: 50%; height: auto;">


## *Types Of Commands* ##
There are two types of commands that can be used, admin commands and commands accessible to everyone. Permission to use admin commands is available to those who are NOT ADMIN OF THE GROUP CHAT but on a private admin whitelist instead. To ask to be on this list please email me at (<a href="mailto:k1raspberrypi@gmail.com?">k1raspberrypi@gmail.com</a>) or contact me directly.


To see all of the commands available and their descriptions use the following command:
```txt
$help
```

<img src="./Example-Photos/[ $help ] Command.PNG" alt="[ $help ] Example" style="display: block; margin-left: auto; margin-right: auto; width: 50%; height: auto;">


The most up-to-date list of commands is as follows:
* $status
* $day1
* $store #
* $policy manual
* $schedule link
* $help


_(Admin Only)_


* $schedule post
* $schedule clear
* $smgs on
* $smgs off


# How Does the Program Work? #
A Websocket connection is established to the GroupMe's push service in order to receive real-time push notifications of messages or other alerts on the User Channel of said user account. This incoming data is then compared against a list of string commands that do different things. If the incoming message is validated as a bot command, then a corresponding HTTP Post request is sent to GroupMe's [Public Rest API](https://dev.groupme.com/docs/v3) and the bot responds to the command in some way.


# Software Architecture #


## *logger_conf.py* ##
Establishes different logger objects used to keep a record of different types of activity from the real notifications received, when different Bot commands are run, and to any type of websocket activity.


## *push_service_helpers.py* ##
Contains functions that are used to interact and subscribe to GroupMe's push service with the given websocket connection and extra credentials.


## *bot.py* ##
Defines the Bot class which is initialized with all the important keys and other data needed for the GroupMe bot that is going to be used. This class contains multiple methods which make up the code used to perform the different actions of either the admin commands or the commands accessible to everyone.


## *main.py* ##
This is the file to be run when turning the bot online. When ran, a bot class instance will be constructed and a websocket connection to the GroupMe Push Service will be made. From here the program will indefinitely listen to incoming notifications from the push service and will handle the data accordingly in the handle_new_data function. Within this function, the program will make any type of reconnectivity needed to the push service, or handle any inputted commands/text within the group chat. 



Here is a general visual sketch of what these files are doing:
<img src="./Example-Photos/Architecture Sketch.jpg" alt="Architecture Sketch" style="display: block; margin-left: auto; margin-right: auto; width: 50%; height: auto;">

# Design Choices #

## *Bot Class* ##
I thought that the idea of putting all the work that the chatbot does in an object would fit nicely for multiple reasons. Firstly, it allows you to easily plug in different credentials for different bots or different GroupMe accounts by changing what you initialize the class with it being able to then do all the same work. Secondly, all of the actual different actions that the bot performs are organized as methods under one large class. Finally, each of the methods can be mapped to the string representation of what will trigger it in the group chat under an elegant class property method using a dictionary.


## *Using Asynchronous Functions* ## 
A few things had to be asynchronous  within this program as the [websocket library](https://websockets.readthedocs.io/en/stable/) required it along with the ability for scheduled messages to be possible. The scheduled message function that will post reminder messages to the group chat needed to "sleep" in the background between the scheduled times, and come back to life after said time has passed, which made asynchronous programming come in handy.


