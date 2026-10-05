# TODO: check the redis ttl and if data enterd
import pyogrio.errors
from validator import validate_notification
from redis_client import is_exists, add_notification
import elastic_logger
import clasificate
import constants

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
    try:
        e = clasificate.get_region_with_geopandas(constants.data_file_path,notification_dict["lon"], notification_dict["lat"])
        print(e)
    except (pyogrio.errors.DataSourceError) as ex:
        print(ex)
    