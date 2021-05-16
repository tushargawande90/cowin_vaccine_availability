import os
import requests
from datetime import date
import datetime
import json
import boto3

DISTRICT_ID = "389"
MIN_AGE = 18


def lambda_handler(event, context):

    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'}    
    data = ""
    today = date.today()
    account_id = boto3.client('sts').get_caller_identity().get('Account')
    region = os.environ['AWS_REGION']
    for week in [0,1,2,3,4,5]:
        dt = (today + datetime.timedelta(weeks = week)).strftime('%d-%m-%Y')
        url = f"http://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={DISTRICT_ID}&date={dt}"
        response = requests.request("GET", url, headers=header, data={})
        if response.status_code == 200:
            output = json.loads(response.text)
            for center in output["centers"]:
                for session in center["sessions"]:
                    if ((session["min_age_limit"] == MIN_AGE) & (session["available_capacity"] > 0)):
                        data = data + "\n" + ',\t'.join([session["date"], session["vaccine"], str(session["min_age_limit"]), str(session["available_capacity"]), center["fee_type"], center["name"], center["block_name"], center["address"]])
    if data:
        data = "Date,\tVaccine,\tMinAge,\tAvailability,\tFreeOrPaid,\tCenterName,\tCenterBlock,\tCenterAddress" + data
        res = boto3.client('sns').publish(
            TargetArn="arn:aws:sns:"+region+":"+account_id+":CowinVaccineAvailableTopic",
            Message=json.dumps({'default': data,
                            'email': str(data)}),
            Subject='Cowin Vaccination Slots Available',
            MessageStructure='json'
            )
        return 'Success'
    else:
        return 'Failure'