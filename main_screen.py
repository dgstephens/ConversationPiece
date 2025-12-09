# Copyright 2025 geekpower, Daniel G. Stephens
# Version 12/7/25 .66
# Screen Controller Version

import sys
import vlc, time
import RPi.GPIO as GPIO
import serial
from threading import Timer
import re
import paho.mqtt.client as paho
#import csv

#GPIO.setmode(GPIO.BCM)

master_controller = False
server_ip = "10.42.0.1"
me = "screen.2"
delay = .3 # The average delay when communicating with other players
count_loop = 0 # the counter used to determine how often to poll MQTT messages
feed = "conversation/players"
start_time = 0 # media_player start time in milliseconds
script_location = 0 # this is where we are in the media action script
video_file = "/home/pi/Videos/2001_Doors_HAL_v1.3.mov"
black_video_file = "/home/pi/Videos/2001_Doors_HAL_BLACK_v1.3.mov"
count = 0
status = 0
my_ready_status = "unknown" # can be "unknown" or "ready" or "error" or "acked"
my_play_status = "pause" # can be "pause" or "play"
my_screen_status = "image" # can be "image" or "black"
my_pause_duration = 0
my_wait_duration = 4 #seconds - to wait between sending status messages
ready = 0 # when ready is = binary addition of # screens tick marks, we play all video
pause_timer_status = 0 # used for pause timer
send_status_update_timer = 0

client = paho.Client() # MQTT clien

# setup how we "call" the other Raspis
# serves as simple state machine for all Raspis
# pos0 = device #
# pos1 = command sent (play, pause)
# pos2 = command ack (ack/noack)

metype, menumber = re.split(r"[.]", me)

player = vlc.Instance() #create vlc instance
media_player = player.media_player_new()
media_list = player.media_list_new()                 # create a media list
media_list.add_media( player.media_new( video_file ))
#media_list.add_media( player.media_new( black_video_file )) # when we need a blank screen but may need to play audio

media_list_player = player.media_list_player_new()   # create a player to play files from media list

media_list_player.set_media_list(media_list)         # assign the list of media to the multi media player
media_list_player.set_playback_mode( vlc.PlaybackMode().loop )
media_list_player.set_media_player(media_player)     # set the media list player to "media_player" defined above
media_player.set_fullscreen( True )

#print("media_player audio: ", media_player.audio_output_device_enum() )

def on_subscribe( client, userdata, topic, granted_qos):
    #print("inside subscribe handler")
    pass

# MESSAGES:
# always start with either "from" or "to".
# "from" = from follower screens
# "to" = from master screen
# from.screen.<#>.status.ready -> screen is ready to play
# from.screen.<#>.status.playing -> screen is playing video
# from.screen.<#>.status.time.<video_time> -> send master our current video time in millis
# to.screen.<#>.command.play.<millis> -> play your video from <millis> milliseconds
# to.screen.<#>.command.pause.<millis> -> pause for <millis> milliseconds
def message_handling(client, userdata, msg):
    global my_screen_status
    global ready
    print(f"{msg.topic}: {msg.payload.decode()}")
    tokenized_message = re.split(r"[.]", msg.payload.decode() ) 
    print("tokenized_message: " )
    print( tokenized_message )
    if tokenized_message[0] == "to":
        print( "got 0: to" )
        if tokenized_message[1] == metype:
            print( "got 1: metype (screen)" )
            if tokenized_message[2] == menumber or tokenized_message[2] == "0":
                print( "got 2: menumber" )
                if tokenized_message[3] == "command":
                    print( "got 3: command" )
                    if tokenized_message[4] == "play":
                        print( "got 4: play")
                        if len( tokenized_message) > 5: # we have a time component
                            millis = tokenized_message[5]
                            change_my_play_status( "play", millis )
                        else:
                            change_my_play_status( "play" )
                    elif tokenized_message[4] == "pause":
                        print( "got 4: pause" )
                        if len(tokenized_message) > 5: # we have a time component
                            # re.sub here converts the "/" character to a "." for decimal numbers
                            duration = re.sub(r'/', '.', tokenized_message[5])
                            change_my_play_status( "pause", duration)
                        else:
                            change_my_play_status( "pause" )

def change_my_play_status( command, options="0" ):
    global my_play_status
    global my_pause_duration
    global pause_timer_status
    if command == "play":
        print("change_my_play_status: play")
        # switch video to play
        if float(options) > 0:
            media_player.set_time(int(options))
            media_player.play()
        else:
            media_player.play()

        my_play_status = "play"
        pause_timer_status = 0
    elif command == "pause":
        if my_play_status == "pause":
            print("change_my_play_status: pause - already paused")
        else:
            print("change_my_play_status: pause")
            # switch video to pause
            media_player.pause()
            my_play_status = "pause"
            my_pause_duration = float(options)

def change_my_screen_status( make_status ):
    global my_screen_status
    if make_status == "image":
        print("status: video with image")
        current_vid_time = media_player.get_time()
        while current_vid_time == 0:
            current_vid_time = media_player.get_time()
            print( "ERROR: current_vid_time = 0" )
        media_list_player.play_item_at_index(0)
        media_player.set_time(current_vid_time)
        my_screen_status = "image"
    elif make_status == "black":
        print("status: video with black")
        current_vid_time = media_player.get_time()
        while current_vid_time == 0:
            current_vid_time = media_player.get_time()
            print( "ERROR: current_vid_time = 0" )
        media_list_player.play_item_at_index(1)
        media_player.set_time(current_vid_time)
        my_screen_status = "black"

def post_timer_play():
    print("End of Timer play command")
    change_my_play_status( "play" )

# tell_master tells the master controller the status of this device
# currently the "message" argument is unused
def tell_master( status, message="" ):
    if status == "ready":
        full_command = "from." + metype + "." + menumber + ".status." + status 
    elif status == "time":
        full_command = "from." + metype + "." + menumber + ".status.time." + message
    print( "command sent: " + full_command )
    client.publish( feed, full_command )

def call_status_timer():
    print("timer started")
    current_media_time = media_player.get_time()
    tell_master( "time", str(current_media_time))
    status_timer = Timer(my_wait_duration, call_status_timer)
    status_timer.start()

client.on_message = message_handling
client.on_subscribe = on_subscribe

if master_controller == True:
    if client.connecct( "localhost", 1883, 60 ) != 0:
        print( "Couldn't connect to the mqtt broker." )
        sys.exit(1)

else:
    if client.connect( server_ip, 1883, 60 ) != 0:
        print( "Couldn't connect to the mqtt broker." )
        sys.exit(1)
              

sub_return = client.subscribe( feed )
if sub_return != 0:
    print( "error subscribing: ")
    print( sub_return )

# PREP MEDIA FOR START
media_player.set_time( start_time )
media_list_player.play_item_at_index(0)
time.sleep(2)
media_player.pause()
media_player.audio_set_volume( 100 )
time.sleep(2) # wait for things to settle down a little

# start my timer for sending status messages
call_status_timer()

while True:
    pause_timer_status
    send_status_update_timer = 0 #using call_timer function instead
    count_loop += 1
    
    # listen for commands
    if count_loop == 10000:
        client.loop()
        count_loop = 0

    # ready_status can be used in future to keep master aware of how this
    # device is functioning. Currently this does very little
    if my_ready_status == "unknown":
        my_ready_status = "ready"
        tell_master( "ready" )

    if send_status_update_timer == 50000:
        current_media_time = media_player.get_time()
        tell_master( "time", str(current_media_time) )
        send_status_update_timer = 0

    if my_play_status == "pause" and my_pause_duration > 0 and pause_timer_status == 0:
        print("PAUSE + TIMER: " + str(my_pause_duration))
        pause_timer = Timer(my_pause_duration, post_timer_play)
        pause_timer_status = 1
        pause_timer.start()


        

