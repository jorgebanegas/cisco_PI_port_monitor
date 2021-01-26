# https://pynet.twb-tech.com/blog/automation/netmiko.html

from netmiko import ConnectHandler
import subprocess

Network_Device = {"host":"", "username":"","password":"", "device_type":"Cisco"}

connect_to_device = ConnectHandler(**Network_Device)

connect_to_device.enable()

list_of_commands = ["interface gi 1/42","shut","end"]

execute_command = connect_to_device.send_cofig_set(list_of_commands)

print(execute_command)