from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

def some_job():
    print ("TIMEE 1 min" ,datetime.now())

def some_other_job():
    print ("TIMEE 5 min" ,datetime.now())

scheduler = BlockingScheduler()
scheduler.add_job(some_job, 'interval', minutes=1)
scheduler.add_job(some_other_job, 'interval', minutes=5)
scheduler.start()