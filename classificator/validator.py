from datetime import datetime
from pydantic import BaseModel, ValidationError
import constants
import elastic_logger

class Notification(BaseModel):
    alert_id: str
    source: str
    title: str
    content: str
    priority: str
    classification: str
    lat: float
    lon: float
    timestamp: datetime
    status: str

def validate_notification(message:str) -> dict | None:
    try:
        notification = Notification.model_validate_json(message)
        notification_dict = notification.model_dump(mode="json")
        if (notification_dict["lat"] > 90) or (notification_dict["lat"] < -90):
            raise ValidationError("invalid lat")
        if (notification_dict["lon"] > 180) or (notification_dict["lon"] < -180):
            raise ValidationError("invalid lon")
        if notification_dict["priority"] not in constants.priority_values:
            raise ValidationError("invalid priority")
        if notification_dict["classification"] not in constants.classification_values:
            raise ValidationError("invalid classification")
        if notification_dict["status"] not in constants.status_values:
            raise ValidationError("invalid status")
        return notification_dict
    except ValidationError as err:
        elastic_logger.log("ERROR", f"invlid object: {err}")
        print("invalid notification, ", err)
        return None