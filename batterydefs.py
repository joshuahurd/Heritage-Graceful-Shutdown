#This file is necessary for on and off battery scripts and defines all functions.

import smtplib, sys, syslog, time, paramiko, datetime, io, os
from email.mime.text import MIMEText
from apcaccess import status as apc
from contextlib import redirect_stdout
from wakeonlan import send_magic_packet as wakeywakey


#################General functions#################
ssh = paramiko.SSHClient()

#Logs events to system.
def log(msg):
    syslog.syslog(str(msg))
    
#Pauses the script for (Period) seconds.
def wait(period):
    time.sleep(period)

#Adds timestamp as HH:MM:SS
def short_timestamp():
    date_time = datetime.datetime.now()
    timestamp = date_time.strftime("%H:%M:%S")
    return timestamp

#Adds timestamp as HH:MM:SS, Day - Month:Day:Year
def long_timestamp():
    date_time = datetime.datetime.now()
    now = date_time.strftime("%H:%M:%S, %a - %m/%d/%Y")
    return now

#Sends the host a ping packet. If the host responds, returns 1. If no response, returns 0.
def pingCheck(sshHost):
    response = os.system("ping -c 1 " + sshHost)
    if response == 0:
        return 1
    else:
        return 0

#Same as pingCheck, but to a different defined variable.
def voipCheck(VOIPAddress):
    response = os.system("ping -c 1 " + VOIPAddress)
    if response == 0:
        return 1
    else:
        return 0

#Send an email to defined variables. Recommend use "f" variable in conjuction with "msg_subject" to email a history of events.
def email(msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD):
    from_email = GMAIL_ADDRESS
    log(msg_subject)
    printLog = "{0}".format(f.getvalue())
    msg = MIMEText(printLog)
    msg['Subject'] = msg_subject
    msg['From'] = from_email
    msg['To'] = ", ".join(to_emails)
    s = smtplib.SMTP_SSL('smtp.gmail.com', '465')
    s.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
    s.sendmail(from_email, to_emails, msg.as_string())
    s.quit()


#Checks if the battery is receiving power. Returns 0 if yes, 1 if no. 
def statusCheck():
    access = apc.get(host="localhost")
    check = apc.parse(access)
    if check['STATUS'] == 'ONLINE':
        return 0
    if check['STATUS'] == 'CHARGING':
        return 0
    else:
        return 1

#Connects to defined SSH host using key.
def sshConnect(sshHost,sshUser,sshKey):
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(sshHost, username=sshUser, key_filename=sshKey)

#Sends an SSH command from variable.
def sshCommand(Command):
    global ssh_stdin, ssh_stdout, ssh_stderr
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(Command)

#Checks if any VM's are still running on the host. Returns 1 if yes, returns 0 if no.
def VMStatus():
    sshCommand('xe vm-list')
    commandRead = ssh_stdout.read()
    commandList = commandRead.split()
    if commandList.count('running') > 1:
        return 1
    else:
        return 0


#################Protection Functions#################

#Checks if protection mode should be activated.
def autostop(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,
            host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time):
    print("{}: Checking if script is already running...".format(short_timestamp()))
    if protCheck() == 1:
        protMode(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,
            host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
    else:
        print("{}: Nope! Continuing...".format(short_timestamp()))

#Opens the onbattery script protection and prevents the script from running more than one instance.
##THIS MUST BE USED TO START THE SCRIPT##
def open_onbattery():
    scriptCheck = open('/tmp/onbatteryrunning', "w+")
    scriptCheck.write("This file will only exist if the APCUPSD onbattery script is running or exited badly.")
    scriptCheck.close()

#Opens the offbattery script protection and prevents the script from running more than one instance.
##THIS MUST BE USED TO START THE SCRIPT##
def open_offbattery():
    scriptCheck = open('/tmp/offbatteryrunning', "w+")
    scriptCheck.write("This file will only exist if the APCUPSD offbattery script is running or exited badly.")
    scriptCheck.close()

#Closes the onbattery script and removes the file preventing the script from running in more than one instance.
##THIS MUST BE USED TO END THE SCRIPT##
def close_onbattery():
    os.remove('/tmp/onbatteryrunning')
    exit()

#Closes the offbattery script and removes the file preventing the script from running in more than one instance.
##THIS MUST BE USED TO END THE SCRIPT##
def close_offbattery():
    os.remove('/tmp/offbatteryrunning')
    exit()

#Checks if the protection mode is active.
def protCheck():
    if os.path.exists('/tmp/protection_mode') == True:
        return 2
    if os.path.exists('/tmp/onbatteryrunning') == True:
        if os.path.exists('/tmp/offbatteryrunning') == True:
            print("{}: Both scripts are running.".format(short_timestamp()))
            return 1
    if os.path.exists('/tmp/offbatteryrunning') == True:
        if os.path.exists('/tmp/onbatteryrunning') == True:
            print("{}: Both scripts are running.".format(short_timestamp()))
            return 1
    else:
        return 0
            
#Activates protection mode
def protMode(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,
            host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time):
    scriptCheck = open('/tmp/protection_mode', "w+")
    scriptCheck.write("This file will only exist if the APCUSPD script detected power flapping or exited badly.")
    scriptCheck.close()
    os.remove('/tmp/onbatteryrunning')
    os.remove('/tmp/offbatteryrunning')
    if pingCheck(sshHost) == 1:
        print("{}: Server is online, initiating shutdown sequence.".format(short_timestamp()))
        shutdownProt(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,host_shutdown_time,
                vm_additional_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
    else:
        print("{}: Server doesn't appear to have started yet.".format(short_timestamp()))
    print("{}: Entering protection mode. Server will not attempt to boot for 30 minutes.".format(short_timestamp()))
    wait(1800)
    os.remove('/tmp/protection_mode')
    if statusCheck() == 0:
        print("{}: Protection mode has ended, and the UPS is reporting that it has power. Running offbattery script.".format(short_timestamp()))
        os.system("python3 /etc/apcupsd/offbattery")
        email(msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
        exit()
    elif statusCheck() == 1:
        print("{}: Protection mode has ended, and the UPS is reporting that the power is out. Waiting for power to return.".format(short_timestamp()))
        email(msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
        exit()

#Stop protection mode from running twice.
def protectionHalt(msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD):
    print("{}: Another power outage was detected, but the server is currently in protection mode, so no action was taken.".format(short_timestamp()))
    email(msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
    exit()

#Shutdown sequence for protection mode.
def shutdownProt(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,host_shutdown_time,
                vm_additional_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD):
    #Check if VM's are running.
    if pingCheck(sshHost) == 1:
        shutdown_logic_sequence(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,host_shutdown_time,
                            vm_additional_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
    else:
        print("{}: Host is not responding to pings. Assuming it's already shut down and continuing to protection mode.".format(short_timestamp()))


#################Shutdown Functions#################

#Soft shutdown for VM's.
def VM_Shutdown(vmShutdown,vm_shutdown_time,sshHost,sshUser,sshKey,battery_off_time,vmForcedown,vm_force_time,hostDisable,
                hostShutdown,host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time):
    print("{}: Sending VM shutdown commands...".format(short_timestamp()))
    sshCommand(vmShutdown)
    wait(vm_shutdown_time)
    autostop(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,
            host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)

#To wait additional time for soft shutdown of VM's.
def VM_Shutdown_Wait(vm_additional_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,
                hostDisable,hostShutdown,host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD):
    print("{}: VM's still running? Waiting ".format(short_timestamp()) + str(vm_additional_time) + " seconds for soft shutdown.")
    wait(vm_additional_time)
    autostop(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,
            host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)

#Forcefully closes VM's.
def VM_Force_Shutdown(vmForcedown,vm_force_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,hostDisable,hostShutdown,
                host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time):
    print("{}: VM's still running. Forcing shut down.".format(short_timestamp()))
    sshCommand(vmForcedown)
    wait(vm_force_time)
    autostop(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,
            host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)

#Shuts down the host.
def Host_Shutdown(hostDisable,hostShutdown,host_shutdown_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,
                vm_force_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time):
    print("{}: Sending shutdown commands to host.".format(short_timestamp()))
    sshCommand(hostDisable)
    sshCommand(hostShutdown)
    wait(host_shutdown_time)
    autostop(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,
            host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)

#Confirms that the host has shut down.
def shutdownConfirm(hostDisable,hostShutdown,host_shutdown_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,
                vmForcedown,vm_force_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time):
    print("{}: Host is still responding. Trying shutdown commands again.".format(short_timestamp()))
    Host_Shutdown(hostDisable,hostShutdown,host_shutdown_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,
                vm_force_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
    if pingCheck(sshHost) == 0:
        print("{}: Unable to confirm host shutdown. VM's are stopped but server is still online.".format(short_timestamp()))
    else:
        print("{}: Host is shutdown.".format(short_timestamp()))


#################Start Functions#################

#Starts the host.
def Host_Startup(sshHost,host_startup_time,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,
                hostDisable,hostShutdown,host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time,MACAddress):
    print("{}: Sending startup commands to host.".format(short_timestamp()))
    wakeywakey(MACAddress)
    wait(host_startup_time)
    autostop(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,
            host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)

#Startup for VM's.
def VM_Startup(vmStart,vm_startup_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_additional_time,
                vm_force_time,hostDisable,hostShutdown,host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD):
    print("{}: Sending VM start commands...".format(short_timestamp()))
    sshCommand(vmStart)
    wait(vm_startup_time)
    autostop(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,
            host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)

#Confirm VM's have started.
def VM_Confirm(vmStart,vm_startup_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,
                hostDisable,hostShutdown,host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time):
    if VMStatus() == 0:
        print("{}: VM's don't appear to be running, trying again.".format(short_timestamp()))
        VM_Startup(vmStart,vm_startup_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_additional_time,
                vm_force_time,hostDisable,hostShutdown,host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
        if VMStatus() == 0:
            print("{}: VM's still don't appear to be running. Server is started but VM's are not.".format(short_timestamp()))
        else:
            print("{}: VM's are started!".format(short_timestamp()))
    else:
        print("{}: VM's are started!".format(short_timestamp()))

#Sequence to perform VOIP start.
def voipStart(VOIPAddress,VOIP_startup_time,host_startup_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,
                hostDisable,hostShutdown,host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time):
    print("{}: Sending startup command to VOIP server.".format(short_timestamp()))
    wakeywakey(VOIPAddress)
    wait(VOIP_startup_time)
    autostop(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,
            host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)

#Checks to make sure VOIP server has started.
def voipConfirm(VOIPAddress,host_startup_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,
                hostDisable,hostShutdown,host_shutdown_time,VOIP_startup_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time):
    if voipCheck == 0:
        voipStart(VOIPAddress,VOIP_startup_time,host_startup_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,
                hostDisable,hostShutdown,host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
        if voipCheck == 0:
            print("{}: VOIP Server is not responding. Unable to start VOIP Server.".format(short_timestamp()))
    else:
        print("{}: VOIP Server has successfully started!".format(short_timestamp()))


#################Logic Sequences#################

#This is a long sequence of actions and checks to ensure a graceful shutdown.
def sequence_on_bat(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,host_shutdown_time,
                    msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time):
    if protCheck() == 2:
        protectionHalt(msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
    print("{}: Waiting ".format(short_timestamp()) + str(battery_off_time) + " seconds to confirm power failure.")
    wait(battery_off_time)
    autostop(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,
            host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
    print("{}: Power outage detected. Running onbattery script.".format(short_timestamp()))
    open_onbattery()
    if statusCheck() == 1:
        shutdown_logic_sequence(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,host_shutdown_time,
                            vm_additional_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
    else:
        print("{}: UPS is reporting power was restored, so exiting script.".format(short_timestamp()))

#This is a long sequence of actions and checks to ensure a full restoration of servers.
def sequence_off_bat(msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,battery_on_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_additional_time,
                    vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,host_shutdown_time,host_startup_time,VOIPAddress,VOIP_startup_time,vmStart,vm_startup_time,MACAddress):
    if protCheck() == 2:
        protectionHalt(msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
    print("{}: Waiting ".format(short_timestamp()) + str(battery_off_time) + " seconds to confirm power restoration.")
    wait(battery_on_time)
    autostop(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,
            host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
    print("{}: Power restoration detected. Running offbattery script.".format(short_timestamp()))
    open_offbattery()
    if statusCheck() == 0:
        startup_logic_sequence(sshHost,host_startup_time,VOIPAddress,VOIP_startup_time,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,
                hostDisable,hostShutdown,host_shutdown_time,msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vmStart,vm_startup_time,f,vm_additional_time,MACAddress)
    else:
        print("{}: UPS is reporting power went out again, so exiting script.".format(short_timestamp()))
    
#Sequence to perform a graceful shutdown with checks for additional needed time.
def shutdown_logic_sequence(sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,hostDisable,hostShutdown,host_shutdown_time,
                            vm_additional_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD):
    sshConnect(sshHost,sshUser,sshKey)
    #If VM's are running, send shutdown command over SSH.
    if VMStatus() == 1:
        VM_Shutdown(vmShutdown,vm_shutdown_time,sshHost,sshUser,sshKey,battery_off_time,vmForcedown,vm_force_time,hostDisable,
                hostShutdown,host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
        #If VM's are still running, wait a bit longer for them to stop.
        if VMStatus() == 1:
            VM_Shutdown_Wait(vm_additional_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,
                            hostDisable,hostShutdown,host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
            #If VM's are still running, forcibly close them.
            if VMStatus() == 1:
                VM_Force_Shutdown(vmForcedown,vm_force_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,hostDisable,hostShutdown,
                                host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
                Host_Shutdown(hostDisable,hostShutdown,host_shutdown_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,
                                vm_force_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
                #If host is still online, try shutdown commands.
                if pingCheck(sshHost) == 0:
                    shutdownConfirm(hostDisable,hostShutdown,host_shutdown_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,
                                    vmForcedown,vm_force_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
                else:
                    print("{}: Host is shutdown.".format(short_timestamp()))
            else:
                Host_Shutdown(hostDisable,hostShutdown,host_shutdown_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,
                vm_force_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
                if pingCheck(sshHost) == 0:
                    shutdownConfirm(hostDisable,hostShutdown,host_shutdown_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,
                                    vmForcedown,vm_force_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
        else:
            Host_Shutdown(hostDisable,hostShutdown,host_shutdown_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,
                        vm_force_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
            if pingCheck(sshHost) == 0:
                shutdownConfirm(hostDisable,hostShutdown,host_shutdown_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,
                                vmForcedown,vm_force_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
    else:
        Host_Shutdown(hostDisable,hostShutdown,host_shutdown_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,
                    vm_force_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
        if pingCheck(sshHost) == 0:
            shutdownConfirm(hostDisable,hostShutdown,host_shutdown_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,
                            vmForcedown,vm_force_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
    ssh.close()

#Sequence to perform full startup with checks for additional time if needed.
def startup_logic_sequence(sshHost,host_startup_time,VOIPAddress,VOIP_startup_time,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,
                hostDisable,hostShutdown,host_shutdown_time,msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vmStart,vm_startup_time,f,vm_additional_time,MACAddress):
    voipStart(VOIPAddress,VOIP_startup_time,host_startup_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,
                hostDisable,hostShutdown,host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
    voipConfirm(VOIPAddress,host_startup_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,
                hostDisable,hostShutdown,host_shutdown_time,VOIP_startup_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
    Host_Startup(sshHost,host_startup_time,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,
                hostDisable,hostShutdown,host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time,MACAddress)
    if pingCheck(sshHost) == 0:
        print("{}: Host is not responding, trying again.".format(short_timestamp()))
        Host_Startup(sshHost,host_startup_time,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,
                hostDisable,hostShutdown,host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time,MACAddress)
        if pingCheck(sshHost) == 0:
            print("{}: Host is still not responding. Cannot continue with startup.".format(short_timestamp()))
        else:
            sshConnect(sshHost,sshUser,sshKey)
        VM_Startup(vmStart,vm_startup_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_additional_time,
                vm_force_time,hostDisable,hostShutdown,host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
        VM_Confirm(vmStart,vm_startup_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,
                hostDisable,hostShutdown,host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
        ssh.close()
    if pingCheck(sshHost) == 1:
        sshConnect(sshHost,sshUser,sshKey)
        VM_Startup(vmStart,vm_startup_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_additional_time,
                vm_force_time,hostDisable,hostShutdown,host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
        VM_Confirm(vmStart,vm_startup_time,sshHost,sshUser,sshKey,battery_off_time,vmShutdown,vm_shutdown_time,vmForcedown,vm_force_time,
                hostDisable,hostShutdown,host_shutdown_time,msg_subject,f,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,vm_additional_time)
        ssh.close()