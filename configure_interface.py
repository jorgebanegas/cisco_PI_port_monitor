#!/usr/bin/env python
from __future__ import print_function
import requests
import json
import time
requests.packages.urllib3.disable_warnings()
import logging
logger = logging.getLogger(__name__)
from pi_config import PI, USER, PASSWORD

BASE="https://%s:%s@%s/webacs/api/v1/" %(USER,PASSWORD,PI)


CLI_TEMPLATE = {
  "cliTemplateCommand" : {
    "targetDevices" : {
      "targetDevice" : {
        "targetDeviceID" : "629636",
        "variableValues" : {
          "variableValue": [
            {
              "name": "InterfaceName",
              "value": "GigabitEthernet3/43"
            },
            {
              "name": "Description",
              "value": "api testing"
            },
            {
              "name": "StaticAccessVLan",
              "value": ""
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
    "templateName" : "Configure Interface"
  }
}


def get_job_status(base, jobname):
    url = base + 'data/JobSummary.json?jobName=%s' %jobname
    jobresult = requests.get(url, verify=False)
    jobresult.raise_for_status()
    return jobresult.json()

def get_job_detail(base, jobnumber):
    url = base + 'data/JobSummary/%s.json' %jobnumber
    jobresult = requests.get(url, verify=False)
    jobresult.raise_for_status()
    return jobresult.json()

def get_full_history(base, jobname):
    url = base + 'op/jobService/runhistory.json?jobName=%s' %jobname
    jobresult = requests.get(url, verify=False)
    jobresult.raise_for_status()
    return jobresult.json()

def wait_for_job(base, jobname):
    result = get_job_status(base, jobname)
    jobnumber = result['queryResponse']['entityId'][0]['$']
    total =0
    while True:

        jobdetail = get_job_detail(base, jobnumber)
        logger.debug(json.dumps(jobdetail, indent=2))
        status = jobdetail['queryResponse']['entity'][0]['jobSummaryDTO']

        if status['jobStatus'] != "COMPLETED":
            logger.info("Job Status: {status}... sleeping 5 (total {total})".format(status=status['jobStatus'], total=total))
            time.sleep(5)
            total += 5
        elif 'runStatus' in status and status['runStatus'] != "COMPLETED":
            logger.info("Run Status: {status}... sleeping 5 (total {total})".format(status=status['runStatus'],total=total))
            time.sleep(5)
            total += 5
        else:
            logger.debug(json.dumps(jobdetail, indent=2))
            return jobdetail

def submit_template_job(base, cli_template):
    headers={"Content-Type" : "application/json"}
    result = requests.put(base + "op/cliTemplateConfiguration/deployTemplateThroughJob.json", headers=headers,
                        data=json.dumps(cli_template), verify=False)
    result.raise_for_status()
    return result.json()

def main():
    job_result = submit_template_job(BASE, CLI_TEMPLATE)

    print(json.dumps(job_result, indent=2))

    jobname = job_result['mgmtResponse']['cliTemplateCommandJobResult']['jobName']
    jobresponse = wait_for_job(BASE, jobname)
    print(json.dumps(jobresponse, indent=2))

    history = get_full_history(BASE, jobname)
    print(json.dumps(history, indent=2))

if __name__ == "__main__":
    main()