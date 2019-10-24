import paramiko

sshHost = '10.1.10.9'
sshUser = 'root'
sshKey = '/etc/apcupsd/raspL-priv.ppk'
vmCommand = 'xe vm-start --multiple'

ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(sshHost, username=sshUser, key_filename=sshKey)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(vmCommand)