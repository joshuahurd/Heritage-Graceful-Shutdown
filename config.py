#!/usr/bin/env python3
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
to_emails = ["<Email to notify"]
msg_subject = "ALERT: <Location> UPS detected a power failure! {}".format(long_timestamp())

#SSH Commands (If not logged in as root, add sudo)
vmShutdown = 'xe vm-shutdown --multiple'
vmForcedown = 'xe vm-shutdown --multiple --force'
hostDisable = 'xe host-disable'
hostShutdown = 'xe host-shutdown'

vmStart = 'xe vm-start --multiple'

#Seconds to wait before each step
battery_off_time = 60
vm_shutdown_time = 120
vm_additional_time = 60
vm_force_time = 60
host_shutdown_time = 60

battery_on_time = 60
host_startup_time = 300
host_additional_time = 60
vm_startup_time = 60
VOIP_startup_time = 60