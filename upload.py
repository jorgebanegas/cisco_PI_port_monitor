import requests
import json
import pymongo
import csv
from datetime import datetime
from requests.auth import HTTPBasicAuth
from pi_config import PI, USER, PASSWORD

# reading device file containing list of hostnames

with open('devices.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        device_names = row

myclient = pymongo.MongoClient("mongodb://localhost:27017/")

mydb = myclient["ports"]
collection = mydb["devices_ports"]              

base_url = 'https://' + PI + '/webacs/api/v3/data'

url = base_url + '/Devices.json'

payload = {}
headers = {
}

response = requests.request('GET', url,auth=HTTPBasicAuth(USER, PASSWORD), headers=headers, data = payload)

response = json.loads(response.text)
devices_info = []

for device in response['queryResponse']['entityId']:
    url = base_url + '/InventoryDetails/' + device['$'] + '.json'

    response = requests.request('GET', url,auth=HTTPBasicAuth(USER, PASSWORD), headers=headers, data = payload)
    response = json.loads(response.text)
    print('----------------------------')
    try:
      if (response['queryResponse']['entity'][0]['inventoryDetailsDTO']['summary']['deviceName'] in device_names):
        print("Found device! ","Device Name: ",response['queryResponse']['entity'][0]['inventoryDetailsDTO']['summary']['deviceName'])
        print('----------------------------')

        device_info = {}
        device_info['name'] = response['queryResponse']['entity'][0]['inventoryDetailsDTO']['summary']['deviceName']
        device_info['ip'] = response['queryResponse']['entity'][0]['inventoryDetailsDTO']['summary']['ipAddress']
        device_info['id'] = response['queryResponse']['entity'][0]['inventoryDetailsDTO']['summary']['deviceId']
        device_info['type'] = response['queryResponse']['entity'][0]['inventoryDetailsDTO']['summary']['deviceType']
        device_info['ports'] = response['queryResponse']['entity'][0]['inventoryDetailsDTO']['ethernetInterfaces']['ethernetInterface']
        devices_info.append(device_info)

      else:
        print("Device name not found in provided file")
    except KeyError:
        print("No device name")

for device_info in devices_info:
  for port in device_info['ports']:
    if port['adminStatus'] == 'UP' and port['operationalStatus'] == 'DOWN':
        db_entry = {}
        db_entry['device_name'] = str(device_info['name'])
        db_entry['device_id'] =  str(device_info['id'])
        db_entry['device_ip'] = str(device_info['ip'])
        db_entry['port_name'] =  str(port['name'])
        db_entry['time'] = str(datetime.now())

        query = collection.find_one(filter={'device_id':db_entry['device_id'], "port_name":db_entry['port_name']})
        # checking if database entry already exist for the given device id and port
        # if the query returns None, upload port info onto the database
        if query == None:
            print("database entry not found, uploading to db")
            print(collection.insert_one(db_entry))
        else:
            print("database entry already stored")

        print("Inactive port found")
        print("Device name : ", device_info['name'], " Port number : ", port['name'])
        print("Timestamp : ",datetime.now())
        print('-----------------------------------')