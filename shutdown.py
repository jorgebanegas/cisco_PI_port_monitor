import requests
import json
import pymongo
import csv
from datetime import datetime
from requests.auth import HTTPBasicAuth
from pi_config import PI, USER, PASSWORD


myclient = pymongo.MongoClient("mongodb://localhost:27017/")

mydb = myclient["ports"]
collection = mydb["devices_ports"]


base_url = 'https://primeinfrasandbox.cisco.com/webacs/api/v1/op'

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
            print("shutting down port")

        print("-----------------------")

    if oper_status == 'Up':
        collection.delete_one({'device_id':document['device_id'], "port_name":document['port_name']})