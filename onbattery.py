#!/usr/bin/env python3
print("Power outage detected. Running onbattery script!")
import subprocess, os
from batterydefs import *
print("On battery functions imported.")

#If you run this file and close it early or it crashes, check to make sure there is no file /tmp/onbattery before running again.

##### CONFIG #####

#Login Information (Currently <Host> - <Campus>)
GMAIL_ADDRESS = '<Email to send from (Must be existing account)>'
GMAIL_PASSWORD = '<Email password>'
sshHost = '<Host IP>'
sshUser = '<Host user>'
sshKey = '/etc/apcupsd/<Private key>'

#Email Contents
to_emails = ["<Email to notify"]
msg_subject = "ALERT: <Location> UPS detected a power failure! {}".format(long_timestamp())

#SSH Commands (If not logged in as root, add sudo)
vmShutdown = 'xe vm-shutdown --multiple'
vmForcedown = 'xe vm-shutdown --multiple --force'
hostDisable = 'xe host-disable'
hostShutdown = 'xe host-shutdown'

#Seconds to wait before each step
battery_off_time = 60
vm_shutdown_time = 120
vm_additional_time = 60
vm_force_time = 60
host_shutdown_time = 60


##### Start script sequence. DO NOT ERASE OR SCRIPT WON'T WORK #####
print("Beginning sequence...")
syslog.openlog('[UPS]')
f = io.StringIO()
with redirect_stdout(f):
    autostop(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,host_shutdown_time,msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
    sequence_on_bat(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,host_shutdown_time,
            msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
email(msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
print("Email notification sent.")
close_onbattery()