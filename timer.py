from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import requests
import json
import pymongo
import csv
from datetime import datetime
from requests.auth import HTTPBasicAuth
from pi_config import PI, USER, PASSWORD
import configure_interface as ci 

def upload():
    # reading device file containing list of hostnames
    with open('devices.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            device_names = row

    # connecting to local mongo database
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")

    # entering database and collection, creates them at first launch of the script
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
            if(response['queryResponse']['entity'][0]['inventoryDetailsDTO']['summary']['deviceName'] in device_names):
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

def shutdown():
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")

    mydb = myclient["ports"]
    collection = mydb["devices_ports"]

    base_url = 'https://' + PI + '/webacs/api/v1/op'

    url = base_url + '/statisticsService/interface/details.json'

    for document in collection.find():
        headers = {
            }
        
        payload = {
        }

        request_url = url + "?ipAddress=" + document["device_ip"] + "&ifName=" + document["port_name"]

        response = requests.request('GET', request_url,auth=HTTPBasicAuth(USER, PASSWORD), headers=headers, data = payload)
        response = json.loads(response.text)

        # verifying port status 

        admin_status = response["mgmtResponse"]["statisticsDTO"]["childStatistics"]["childStatistic"][11]["statisticEntries"]["statisticEntry"][0]["entryValue"]
        oper_status = response["mgmtResponse"]["statisticsDTO"]["childStatistics"]["childStatistic"][10]["statisticEntries"]["statisticEntry"][0]["entryValue"]

        if admin_status == 'Up' and oper_status == 'Down':
            print("Device name : ", document["device_name"],"Device ID: ", document["device_id"], " Device IP: ", document["device_ip"]," Port: ", document["port_name"] ,"Time: ",document["time"])
            date_time_obj = datetime.strptime(document["time"], '%Y-%m-%d %H:%M:%S.%f')

            delta = datetime.now() - date_time_obj
            print(delta.days ," days offline")

            if delta.days > 59:
                print("changing vlan")

                BASE="https://%s:%s@%s/webacs/api/v1/" %(USER,PASSWORD,PI)


                CLI_TEMPLATE = {
                "cliTemplateCommand" : {
                    "targetDevices" : {
                    "targetDevice" : {
                        "targetDeviceID" : document["device_id"],
                        "variableValues" : {
                        "variableValue": [
                            {
                            "name": "InterfaceName",
                            "value": document["port_name"]
                            },
                            {
                            "name": "Description",
                            "value": "api testing"
                            },
                            {
                            "name": "StaticAccessVLan",
                            "value": "5"
                            },
                            {
                            "name": "A1",
                            "value": ""
                            },
                            { "name": "NativeVLan", "value": ""},
                            { "name": "duplexField","value": ""},
                            { "name": "TrunkAllowedVLan","value": "" },
                            { "name": "spd","value": "" },
                            { "name": "VoiceVlan" ,"value": ""},
                            { "name": "PortFast","value": "" }
                        ]

                        }
                    }
                    },
                    "templateName" : "Configure Interface for device " + document["device_id"] + " " + document["port_name"]
                }
                }

                job_result = ci.submit_template_job(BASE, CLI_TEMPLATE)

                print(json.dumps(job_result, indent=2))

                jobname = job_result['mgmtResponse']['cliTemplateCommandJobResult']['jobName']
                jobresponse = ci.wait_for_job(BASE, jobname)
                print(json.dumps(jobresponse, indent=2))

                history = ci.get_full_history(BASE, jobname)
                print(json.dumps(history, indent=2))

            print("-----------------------")

        if oper_status == 'Up':
            collection.delete_one({'device_id':document['device_id'], "port_name":document['port_name']})

scheduler = BlockingScheduler()
scheduler.add_job(upload, 'interval', minutes=1)
scheduler.add_job(shutdown, 'interval', minutes=1)
scheduler.start()