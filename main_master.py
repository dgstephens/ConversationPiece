# Copyright 2025 geekpower, Daniel G. Stephens
# Version 12/7/25 .66
# Master Controller Version
# this version is called "main_master.py" - previous versions were called "main.py"

import sys
import vlc, time
import RPi.GPIO as GPIO
import serial
from threading import Timer
from  pprint import pprint # Pretty Print 
import re
import paho.mqtt.client as paho
#import csv

#GPIO.setmode(GPIO.BCM)

master_controller = True
server_ip = "10.42.0.1"
me = "screen.1"
delay = .3 # The average delay when communicating with other players
count_loop = 0 # the counter used to determine how often to poll MQTT messages
feed = "conversation/players"
start_time = 0 # media_player start time in milliseconds
script_location = 0 # this is where we are in the media action script
video_file = "/home/pi/Videos/2001_Doors_Bowman_v1.3.mov"
black_video_file = "/home/pi/Videos/2001_Doors_Bowman_BLACK_v1.3.mov"
count = 0
status = 0
get_my_status_timer = 0
start_all = 0
my_play_status = "pause" # can be "pause" or "play"
my_screen_status = "image" # can be "image" or "black"
my_wait_duration = 4 #seconds - to wait between master controller's own status messages
screens = [] # a 2D array that contains screen # and screen # status
ready = 0 # when ready is = binary addition of # screens tick marks, we play all video
          # meaning 3 follower screens = 111 (tickmarks) which is 7 in binary.
          # when screen1 is ready, ready = 1 (0001)
          # when screen2 is ready, ready = 3 (0011)
          # when screen3 is ready, ready = 7 (0111)
          # when screen4 is ready, ready = 15 (1111)

client = paho.Client() # MQTT client

# setup how we "call" the other Raspis
# serves as simple state machine for all Raspis
# pos0 = device #
# pos1 = command sent (play, pause)
# pos2 = command ack (ack/noack)
screens = [[1, "unknown", "unknown" ],
           [2, "unknown", "unknown" ],
           [3, "unknown", "unknown" ],
           [4, "unknown", "unknown" ]]

player = vlc.Instance() #create vlc instance
media_player = player.media_player_new()
media_list = player.media_list_new()                 # create a media list
media_list.add_media( player.media_new( video_file ))
#media_list.add_media( player.media_new( black_video_file )) # when we need a blank screen but may need to play audio

media_list_player = player.media_list_player_new()   # create a player to play files from media list

media_list_player.set_media_list(media_list)         # assign the list of media to the multi media player
media_list_player.set_playback_mode(vlc.PlaybackMode().loop)
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
# from.screen.<#>.status.ready -> screen is ready to playa
# from.screen.<#>.status.playing -> screen is playing video
# from.screen.<#>.status.time.<millis> -> send master our current video time
# to.screen.<#>.command.play -> play your video
# to.screen.<#>.command.pause.<millis> -> pause for <millis> milliseconds
def message_handling(client, userdata, msg):
    global my_screen_status
    global ready
    #print(f"{msg.topic}: {msg.payload.decode()}")
    tokenized_message = re.split(r"[.]", msg.payload.decode() ) 
    print("tokenized_message: " )
    print( tokenized_message )
    device_number = int(tokenized_message[2])
    if tokenized_message[0] == "from":
        if tokenized_message[3] == "status":
            if tokenized_message[4] == "ready":
                if device_number == 2:
                    ready = ready + 2
                elif device_number == 3:
                    ready = ready + 4
                elif device_number == 4:
                    ready = ready + 8
                set_device_state( device_number, "ready", "ack" )
            if tokenized_message[4] == "playing":
                set_device_state( device_number, "play", "ack" )
            if tokenized_message[4] == "paused":
                set_device_state( device_number, "pause", "ack" )

        
# this method updates data in the screens list
def set_device_state( device_num, state, ack ):
    global screens
    if device_num == 0:
        # set state for all devices
        for entry in range(len(screens)):
            screens[entry][1] = state
            screens[entry][2] = ack
    else:
        # -1 to change from device number to list index number
        screens[device_num-1][1] = state
        screens[device_num-1][2] = ack
    print("SCREENS DATA")
    pprint( screens )

def tell_device( device_num, command, time="0", led="red", flashes="1", cycles="1" ):
    # led, flashes and cycles are here if we decide to add an LED panel to the monitor
    # at a later date for some reason.
    # we also refer "device_num" instead of "screen_num" b/c at some point we may
    # wish to incorporate other devices, like remote controls
    if command == "play":
        full_command = "to.screen." + str(device_num) + ".command." + command + "." + time
        print("command sent: " + full_command )
        client.publish( feed, full_command )
        set_device_state( device_num, "play", "noack")
    elif command == "pause":
        full_command = "to.screen." + str(device_num) + ".command." + command + "." + time
        print("command sent: " + full_command )
        client.publish( feed, full_command )
        set_device_state( device_num, "pause", "noack")
    elif command == "on":
        full_command = "to.screen." + device_num + "." + command + "." + time + ".led." + led 
        print("command sent: " + full_command)
        client.publish( feed, full_command )
        set_led_state( led, "on" )
    elif command == "off":
        full_command = "to.screen." + device_num + "." + command + "." + time + ".led." + led 
        print("command sent: " + full_command)
        client.publish( feed, full_command )
        set_led_state( led, "off")
    elif command == "flash":
        full_command = "to.remote." + device_num + ".led." + led + "." + command + "." + flashes
        print("command sent: " + full_command)
        client.publish( feed, full_command )
    elif command == "flash_knight_rider":
        full_command = "to.remote" + remote_num + ".led." + led + "." + command + "." + cycles
        print("command sent: " + full_command)
        client.publish( feed, full_command )

def change_my_play_status( command, options="0" ):
    global my_play_status
    if command == "play":
        print("change_my_play_status: play")
        # switch video to play
        if float(options) > 0:
            media_player.set_time(int(options))
            media_player.play()
        else:
            media_player.play()
            
        my_play_status = "play"
    elif command == "pause":
        # switch video to pause
        media_player.pause()
        my_play_status = "pause"

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

def call_status_timer():
    print("timer started")
    current_media_time = media_player.get_time()
    current_audio_volume = media_player.audio_get_volume()
    print("my media time: " + str(current_media_time))
    print("my audio volume: " + str(current_audio_volume))
    status_timer = Timer(my_wait_duration, call_status_timer)
    status_timer.start()

client.on_message = message_handling
client.on_subscribe = on_subscribe

if master_controller == True:
    if client.connect( "localhost", 1883, 60 ) != 0:
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

# PREP START MEDIA FOR START
media_player.set_time( start_time )
media_list_player.play_item_at_index(0)
time.sleep(2)
media_player.pause()
time.sleep(2) # wait for things to settle down a little
ready = 1 # this device is ready
set_device_state( 1, "ready", "ack" )
media_player.audio_set_volume( 100 )

# start my timer for my status messages
call_status_timer()

while True:
    count_loop += 1
    get_my_status_timer = 0
    
    # listen for status of devices
    if count_loop == 10000:
        client.loop()
        count_loop = 0

    # all screens ready (1 = first screen (this one), 2 = second screen, 4 = third screen, 8 = fourth screen))
    # all = 1+2+4+8 = 15
    if ready == 3 and start_all == 0: 
        tell_device( 0, "play", "1" ) # device 0 is all screens
        time.sleep(delay)
        change_my_play_status( "play", "1" )
        start_all = 1

    if get_my_status_timer == 50000:
        # ultimately we want to check all the players' media times to
        # ensure all devices are synced properly
        current_media_time = media_player.get_time()
        current_audio_volume = media_player.audio_get_volume()
        print("my media time: " + str(current_media_time))
        print("my audio volume: " + str(current_audio_volume))
        get_my_status_timer = 0

