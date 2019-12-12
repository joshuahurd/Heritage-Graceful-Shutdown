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

#Login Information (Currently <Host> - <Campus>)
GMAIL_ADDRESS = '<Email to send from (Must be existing account)>'
GMAIL_PASSWORD = '<Email password>'
sshHost = '<Host IP>'
sshUser = '<Host user>'
sshKey = '/etc/apcupsd/<Private key>'
MACAddress = '<Host MAC>' #Use #.#.#.#.#.#
VOIPAddress = '<VOIP MAC>' #Use #.#.#.#.#.#

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
VOIP_startup_time = 60


##### Start script sequence. DO NOT ERASE OR SCRIPT WON'T WORK #####
print("Beginning sequence...")
syslog.openlog('[UPS]')
f = io.StringIO()
printLog = "{0}".format(f.getvalue())
with redirect_stdout(f):
    try:
        autostop(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,
            host_shutdown_time,msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
        open_offbattery()
        sequence_off_bat(msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,battery_on_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_additional_time,
                    vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,host_shutdown_time,host_startup_time,VOIPAddress,VOIP_startup_time,vmStart,vm_startup_time)
    except:
        print("{}: Power restoration was detected but there was an unexpected error with startup, server is likely not running!!".format(short_timestamp()))
email(msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
print("Email notification sent.")
close_offbattery()