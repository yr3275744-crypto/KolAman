# TODO: check the redis ttl and if data enterd
import pyogrio.errors
import json
from validator import validate_notification
import redis_client
import elastic_logger
import clasificate
import constants
import rabbit_sender
import pika.exceptions

def process(notification_string:str):
    notification_dict = validate_notification(notification_string)
    if notification_dict == None:
        return
    is_in_redis = redis_client.is_exists(notification_dict)
    if (is_in_redis):
        print("the notification already in redis")
        return
    redis_client.add_notification(notification_dict)
    print("is send validate:", redis_client.is_exists(notification_dict))
    elastic_logger.log("INFO",f"notification {notification_dict["alert_id"]} send to redis")
    try:
        e = clasificate.get_region_with_geopandas(constants.data_file_path,notification_dict["lon"], notification_dict["lat"])
        print(e)
        if e == "OVERSEAS":
            rabbit_sender.send(constants.depth_queue, json.dumps(notification_dict))
            elastic_logger.log("INFO", 
                               f"notification {notification_dict["alert_id"]} send to {constants.depth_queue}", 
                               constants.depth_queue)
        else:
            rabbit_sender.send(e, json.dumps(notification_dict))
            elastic_logger.log("INFO", f"notification {notification_dict["alert_id"]} send to {e}", e)
        print("log send to elastic about rabbit send")
    except (pyogrio.errors.DataSourceError, pika.exceptions.StreamLostError) as ex:
        print(ex)
        elastic_logger.log("ERROR", str(ex))
    