# TODO: check the redis ttl and if data enterd

from validator import validate_notification
from redis_client import is_exists, add_notification
import elastic_logger
def process(notification_string:str):
    notification_dict = validate_notification(notification_string)
    if notification_dict == None:
        return
    is_in_redis = is_exists(notification_dict)
    if (is_in_redis):
        print("the notification already in redis")
        return
    add_notification(notification_dict)
    print("is send validate:", is_exists(notification_dict))
    elastic_logger.log("INFO",f"notification {notification_dict["alert_id"]} send to redis")
    