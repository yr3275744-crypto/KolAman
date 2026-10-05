from validator import validate_notification
from redis_client import is_exists, add_notification

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
    print("send to redis")
    