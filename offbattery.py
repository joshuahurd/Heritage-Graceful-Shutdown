#!/usr/bin/env python3
print("Power restoration detected. Running offbattery script!")

import subprocess, os, config
from batterydefs import *
print("Off battery functions imported.")

#If you manually run this file and close it early or it crashes, check to make sure there is no file /tmp/offbattery before running again.
##### Start script sequence. DO NOT ERASE OR SCRIPT WON'T WORK #####
print("Beginning sequence...")
syslog.openlog('[UPS]')
f = io.StringIO()
printLog = "{0}".format(f.getvalue())
with redirect_stdout(f):
    autostop(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,
            host_shutdown_time,msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
    sequence_off_bat(msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,battery_on_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_additional_time,
                    vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,host_shutdown_time,host_startup_time,VOIPAddress,VOIP_startup_time,vmStart,vm_startup_time,MACAddress)
email(msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
print("Email notification sent.")
close_offbattery()