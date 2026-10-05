import redis
import json
import constants

client = redis.Redis(host=constants.host, port=constants.port, decode_responses=True)

def is_exists(notification:dict):
    if client.get(notification["alert_id"]):
        return True
    else:
        return False

def add_notification(notification:dict):
    value = json.dumps(notification)
    client.set(notification["alert_id"], value, ex= 60)