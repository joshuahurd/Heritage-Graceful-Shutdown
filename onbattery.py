#!/usr/bin/env python3
print("Power outage detected. Running onbattery script!")
import subprocess, os, config
from batterydefs import *
print("On battery functions imported.")

#If you manually run this file and close it early or it crashes, check to make sure there is no file /tmp/onbattery before running again.
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