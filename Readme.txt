This is a readme for the Heritage Graceful Shutdown scripts for APCUPSD. Until an installer is made, the process for getting these scripts to work is somewhat complicated.

To run these scripts it is assumed you already have an APC UPS, you are running virtual machines on a XenServer based host, and you have a linux machine running these scripts.
It is possible to run these scripts without XenServer, but modification to the language and SSH commands will be necessary. We use a Raspberry Pi to run these scripts.

Installation:
Download APCUPSD for Linux. (This is the software that APC provides for free and monitors the UPS)
-Add file path to execute onbattery and offbattery scripts in the apccontrol file under /etc/apcupsd/
-Add onbattery, offbattery, and batterydefs scripts to the same folder.
-Change config titled config.py to match your specific build and network.
-Edit apcupsd.conf to match your installation (USB, Network, Serial, etc.). You will probably need to exercise some Google-fu here.
Install Postfix Mail utility for Linux and configure it for your notifier email address (Note: This is email you're sending FROM)
Install Python3
Install Paramiko, APCAccess, and WakeOnLan modules for Python3 using PIP command.

If configured correctly, these scripts will issue automatic shutdown commands and send a notification email to the desired address in the event of a power outage.
Note that your networking hardware will need to be running through the UPS for the email notification to be succesfully sent.


Breakdown:
    Onbattery
        Upon detection of a power outage, the APC Daemon will execute the onbattery script.
        The script will wait for a period of time to confirm that the power is still out.
        If the power is still out, the Pi will then connect to Host server via SSH
        Linux machine will tell Host to shutdown ALL virtual machines.
        Linux machine will check after a period of time to ensure all VM’s have gracefully shut down.
        If the VM’s are not shut down, it will wait a bht longer.
        If the VM’s are still not shut down, it will issue a forceful shutdown command.
        After a period of time, Linux machine will then issue a host shutdown command.
        After another period of time, Linux machine will ping the host to see if it’s shut down.
        If host is not shut down, it will try one more time.
        Linux machine will then email a log of the events.

    Offbattery
        Upon detection of a power restoration (assuming the Linux machine hasn't lost power, we use a Raspberry Pi), APC Daemon will execute the offbattery script.
        The script will wait for a period of time to confirm that the power is still on. After every period of waiting time, the Linux machine will re-check to make sure the power is still back on. If at any point during recovery it detects that the power has gone out, it will exit the script at that point. This should prevent a scenario where both scripts are running trying to both start and stop the server.
        Linux machine will issue a magic packet to wake up the host.
        Linux machine will wait a period of time for host to boot (during testing this was about 5 minutes)
        Linux machine will check if the host is responding to a ping.
        If host does not respond, Linux machine will try again.
        If host still does not respond, host will send an email.
        If host does respond, Pi will then connect to host via SSH.
        Linux machine will tell host to start ALL virtual machines.
        After a period of time linux machine will check if the VM’s are running.
        Linux machine will email a log of events.

