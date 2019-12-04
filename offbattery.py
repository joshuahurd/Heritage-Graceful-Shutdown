#!/usr/bin/env python3
print("Power restoration detected. Running offbattery script!")

import subprocess, os
from batterydefs import *
print("Off battery functions imported.")

#Stop script if it's already running
print("Checking if script is already running...")
if os.path.exists('/tmp/offbatteryrunning') == True:
    print("Script is already running so stopping here!!")
    exit()
print("Nope! Continuing script.")
scriptCheck = open("/tmp/offbatteryrunning", "w+")
scriptCheck.write("This file will only exist if the offbattery script is running.")
scriptCheck.close()

##### CONFIG #####

#Login Information (Currently HAVM31 - Laveen)
GMAIL_ADDRESS = '<Email to send from (Must be existing account)>'
GMAIL_PASSWORD = '<Email password>'
sshHost = '<Host IP>'
sshUser = '<Host user>'
sshKey = '/etc/apcupsd/<Private key>'
MACAddress = '<Host MAC>'

#Email Contents
to_emails = ["<Email to notify>"]
msg_subject = "STATUS OKAY: <Location> UPS is back on normal power. {}".format(long_timestamp())

#SSH Commands (If not logged in as root, add sudo)
vmStart = 'xe vm-start --multiple'

#Seconds to wait before each step
battery_on_time = 60
host_startup_time = 300
host_additional_time = 60
vm_startup_time = 60



##### Script sequence, do not change! #####

syslog.openlog('[UPS]')
f = io.StringIO()
printLog = "{0}".format(f.getvalue())
print("{}: Beginning sequence...".format(short_timestamp()))
with redirect_stdout(f):
    print("{}: Waiting ".format(short_timestamp()) + str(battery_on_time) + " seconds to confirm power restoration.")
    wait(battery_on_time)
    autostop_startup(msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f)
    print("{}: Power restoration confirmed. Sending automated startup commands to XenServer...".format(short_timestamp()))
    wakeywakey(MACAddress)
    wait(host_startup_time)
    autostop_startup(msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f)
    startupConfirm(host_additional_time,MACAddress,vm_startup_time,sshHost,msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f)
    startup(sshHost,sshUser,sshKey,vm_startup_time,vmStart,msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f)
email(msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
print("Email notification sent.")
close_offbattery()