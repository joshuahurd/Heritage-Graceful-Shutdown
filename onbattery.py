#!/usr/bin/env python3
print("Power outage detected. Running onbattery script!")

import subprocess, os
from batterydefs import *
print("On battery functions imported.")

#Stop script if it's already running
print("Checking if script is already running...)")
if os.path.exists('/tmp/onbatteryrunning') == True:
    print("Script is already running so stopping here!!")
    exit()
print("Nope! Continuing script.")
scriptCheck = open("/tmp/onbatteryrunning", "w+")
scriptCheck.write("This file will only exist if the onbattery script is running.")
scriptCheck.close()

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



##### Script sequence, do not change! #####

syslog.openlog('[UPS]')
f = io.StringIO()
printLog = "{0}".format(f.getvalue())
print("{}: Beginning sequence...".format(short_timestamp()))
with redirect_stdout(f):
    print("{}: Waiting ".format(short_timestamp()) + str(battery_off_time) + " seconds to confirm power failure.")
    wait(battery_off_time)
    autostop_shutdown(msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f)
    print("{}: Power failure confirmed. Sending automated shutdown commands to XenServer...".format(short_timestamp()))
    if shutdownCheck(sshHost,short_timestamp) == 0:
        shutdown(sshHost,sshUser,sshKey,vmShutdown,vmForcedown,hostDisable,hostShutdown,vm_shutdown_time,vm_additional_time,host_shutdown_time,msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f)
        wait(vm_shutdown_time)
        autostop_shutdown(msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f)
        shutdownConfirm(sshHost,sshUser,sshKey,vmShutdown,vmForcedown,hostDisable,hostShutdown,vm_shutdown_time,vm_additional_time,host_shutdown_time,msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f)
email(msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
print("Email notification sent.")
close_onbattery()