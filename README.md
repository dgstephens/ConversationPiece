# ConversationPiece
A simple client/server (MQTT) framework for synchronized video using Raspi 3/4 devices

Based on:
Conversation Piece - a simple discussion about opening a door  
Daniel G. Stephens  

/introduction/  
I originally wrote this simple MQTT client/server system in order to sychronize video playback across a small multitude of Raspi 3/4 devices. The code is all Python3 and, before you read it and gasp, it does not emply general coding best practices. It does make use of expedient, intuitive coding and has lots of comments to make following the (mostly) linear logic simpler. 

The software assumes you wish to play video (via VLC) from a Raspberry Pi 3 or 4 to an HDMI or Composite SD monitor and that you wish these video streams to be synchronized. Meaning, you wish all the video files to start playing at the same time.

This is accomplished by having one Raspi run the "main_master.py" script while all others run the "main_screen.py" script. Both scripts require minimal modification to accomplish their life's goal of synchronously streaming videos of your choice to multiple monitors (preferably CRTs).

/components/  
You will need at least two video clips, they can be of the same lenth, or different lengths. If they are of different lengths, they will go out of sync when they loop. But perhaps this is what you want. NOTE: if you have only one video clip that you wish to play on one monitor, you don't need this software. 

You will need at least two Raspberry Pi's, either version 3B or 4. It likely works on a Raspi 5, but I've not tested it on one as yet.

You will need at least 2 monitors, with either HDMI or Composite video inputs.

/version control/  
This version of Conversation Piece[CP] is based on an “upgrade” of a different work originally titled Talking Heads [TH]

The TH version was similar in that it showed substantially similar conversations between these same characters. However, the two differ in the following ways:

TH: Only two of the video controllers are able to “speak” with each other and synchronize their video to each other - these are both the 2001 characters.   
TH: Physical cable between the two “talking” controllers.  
TH: Multiple audio issues with playing audio through the Raspberry Pi’s TRRS AV connector.  
TH: Generally slow performance due to unnecessary software occupying memory.  
TH: Video edits of the four characters lacked polish. The 2001 and Rushmore characters’ video was not all the same length, so drifted out of sync with each other over time.  
TH: Python timing loops for polling video information and synchronization was marginally effective and created additional processor loading.  

CP: All four video controllers speak with each other continually using the MQTT protocol. One controller acts as the “master” controller starting/stopping and pausing clips on all controllers as necessary.  
CP: All four video controllers communicate without a physical connection via WiFi.  
CP: The TH audio issues have been resolved. Fixes came from more refined audio setup and the addition of an external speaker for one of the CRTs.  
CP: Much faster performance for all video controllers due to the removal of unnecessary software and the streamlining of the controllers’ boot process.  
CP: Re-edited all character videos to improve synchronization and “commentary” from the Rushmore characters.  
CP: Python timing loops were removed and replaced with threaded timers to simplify the code and increase efficiency considerably. This also resulted in much more closely synchronized video on all controllers.  

/hardware/  
(3) Raspberry Pi 4B single board computers  
(1) Raspberry Pi 3B single board computer  
(4) CRT monitors - all late 1980s era  

/software/  
Python server and client software. Server and client software both stream locally hosted standard definition h.264 video files via the Raspi’s component video output using VLC player. Server and client devices “talk” with each other via the MQTT protocol over WiFi. Server software waits for all clients to be ready and then instructs them all to play their video at the same time. The video on all 4 Raspberry Pi devices then runs continuously in a two-minute twelve second loop until they are turned off, or the eventual heat death of the universe.



