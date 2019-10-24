#This file is necessary for on and off battery scripts and defines all functions.

import smtplib, sys, syslog, time, paramiko, datetime, io, os
from email.mime.text import MIMEText
from apcaccess import status as apc
from contextlib import redirect_stdout
from wakeonlan import send_magic_packet as wakeywakey

def log(msg):
    syslog.syslog(str(msg))

def wait(period):
    time.sleep(period)

def close_onbattery():
    os.remove('/tmp/onbatteryrunning')
    exit()

def close_offbattery():
    os.remove('/tmp/offbatteryrunning')
    exit()

def short_timestamp():
    date_time = datetime.datetime.now()
    timestamp = date_time.strftime("%H:%M:%S")
    return timestamp

def long_timestamp():
    date_time = datetime.datetime.now()
    now = date_time.strftime("%H:%M:%S, %a - %m/%d/%Y")
    return now

def statusCheck():
    access = apc.get(host="localhost")
    check = apc.parse(access)
    if check['STATUS'] == 'ONLINE':
        return 1
    else:
        return 0

def email(msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD):
    from_email = GMAIL_ADDRESS
    log(msg_subject)
    msg = MIMEText(printLog)
    msg['Subject'] = msg_subject
    msg['From'] = from_email
    msg['To'] = ", ".join(to_emails)
    s = smtplib.SMTP_SSL('smtp.gmail.com', '465')
    s.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
    s.sendmail(from_email, to_emails, msg.as_string())
    s.quit()

def shutdown(sshHost,sshUser,sshKey,vmShutdown,vmForcedown,hostDisable,hostShutdown,vm_shutdown_time,vm_additional_time,host_shutdown_time,msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(sshHost, username=sshUser, key_filename=sshKey)
    print("{}: VM's are shutting down...".format(short_timestamp()))
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(vmShutdown)
    wait(vm_shutdown_time)
    autostop_shutdown(msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("xe vm-list")
    commandRead = ssh_stdout.read()
    commandList = commandRead.split()
    if commandList.count('running') > 1:
        print("{}: VM's still running, waiting ".format(short_timestamp()) + str(vm_additional_time) + " more seconds...")
        wait(vm_additional_time)
        autostop_shutdown(msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f)
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(vmForcedown)
        print("{}: Force shutdown command sent. Waiting ".format(short_timestamp()) + str(host_shutdown_time) + " seconds...")
        wait(host_shutdown_time)
        autostop_shutdown(msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f)
        print("{}: VM's stopped. Shutting down host...".format(short_timestamp()))
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(hostDisable)
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(hostShutdown)
    else:
        print("{}: VM's stopped. Shutting down host...".format(short_timestamp()))
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(hostDisable)
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(hostShutdown)
    ssh.close()

def pingCheck(sshHost):
    response = os.system("ping -c 1 " + sshHost)
    if response == 0:
        return 1
    else:
        return 0

def shutdownConfirm(sshHost,sshUser,sshKey,vmShutdown,vmForcedown,hostDisable,hostShutdown,vm_shutdown_time,vm_additional_time,host_shutdown_time,msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f):
    if pingCheck(sshHost) == 0:
        print("{}: Host is shut down!".format(short_timestamp()))
    if pingCheck(sshHost) == 1:
        print("{}: Host is still responding? Trying again...".format(short_timestamp()))
        shutdown(sshHost,sshUser,sshKey,vmShutdown,vmForcedown,hostDisable,hostShutdown,vm_shutdown_time,vm_additional_time,host_shutdown_time,msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f)
        wait(vm_shutdown_time)
        autostop_shutdown(msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f)
        if pingCheck(sshHost) == 0:
            print("{}: Host is shut down!".format(short_timestamp()))
        else:
            print("{}: Host shutdown failed, unable to stop the host. It is still on battery power!!".format(short_timestamp()))

def statusCheck_off():
    access = apc.get(host="localhost")
    check = apc.parse(access)
    if check['STATUS'] == 'ONLINE':
        return 0
    if check['STATUS'] == 'CHARGING':
        return 0
    else:
        return 1

def autostop_shutdown(msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f):
    if statusCheck() == 1:
        print("{}: Power has returned! Stopping script.".format(short_timestamp())), 
        printLog = "{0}".format(f.getvalue()) 
        email(msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
        close_onbattery()

def autostop_startup(msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f):
    if statusCheck_off() == 1:
        print("{}: Power went out again. Stopping script.".format(short_timestamp())), 
        printLog = "{0}".format(f.getvalue()) 
        email(msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
        close_offbattery()

def startup(sshHost,sshUser,sshKey,vm_startup_time,vmStart,msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(sshHost, username=sshUser, key_filename=sshKey)
    print("{}: VM's are starting...".format(short_timestamp()))
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(vmStart)
    wait(vm_startup_time)
    autostop_startup(msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("xe vm-list")
    commandRead = ssh_stdout.read()
    commandList = commandRead.split()
    if commandList.count('running') > 1:
        print("{}: VM's appear to be running!".format(short_timestamp()))
    else:
        print("{}: VM's aren't started? Trying again.".format(short_timestamp()))
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(vmStart)
        wait(vm_startup_time)
        autostop_startup(msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f)
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("xe vm-list")
        commandRead2 = ssh_stdout.read()
        commandList2 = commandRead2.split()
        if commandList2.count('running') > 1:
            print("{}: VM's appear to be running!".format(short_timestamp()))
        else:
            print("{}: VM's still aren't started, host is awake but unable to start VM's.".format(short_timestamp()))
            printLog = "{0}".format(f.getvalue())
            email(msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
            print("Email notification sent.")
            close_offbattery()
    ssh.close()

def startupConfirm(host_additional_time,MACAddress,vm_startup_time,sshHost,msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f):
    if pingCheck(sshHost) == 1:
        print("{}: Host is started!".format(short_timestamp()))
    if pingCheck(sshHost) == 0:
        print("{}: Host isn't responding, waiting an additional " + str(host_additional_time) + " seconds...")
        wait(host_additional_time)
        autostop_startup(msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f)
        if pingCheck(sshHost) == 0:
            print("{}: Host still isn't responding? Trying again...".format(short_timestamp()))
            wakeywakey(MACAddress)
            wait(vm_startup_time)
            autostop_startup(msg_subject,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD,f)
            if pingCheck(sshHost) == 1:
                print("{}: Host is started!".format(short_timestamp()))
            else:
                print("{}: Host isn't responding, can't continue with automated startup.".format(short_timestamp()))
                printLog = "{0}".format(f.getvalue())
                email(msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
                print("Email notification sent.")
                close_offbattery()
        else:
                print("{}: Host isn't responding, can't continue with automated startup.".format(short_timestamp()))
                printLog = "{0}".format(f.getvalue())
                email(msg_subject,printLog,to_emails,GMAIL_ADDRESS,GMAIL_PASSWORD)
                print("Email notification sent.")
                close_offbattery()