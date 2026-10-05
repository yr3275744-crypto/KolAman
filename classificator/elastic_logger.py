import os
import constants
from datetime import datetime
from elasticsearch import Elasticsearch, BadRequestError

client = Elasticsearch(constants.elastic_host)

def create_index():
    mappings = {
        "properties": {
            "level": {"type": "keyword"},
            "message": { "type": "text"},
            "@timestamp": {"type": "date"}
        }
    }
    try:
        client.indices.create(index=constants.index_name, mappings=mappings)
    except (BadRequestError) as e:
        print(e)

def log(level:str, message:str):
    if level not in constants.level_values:
        print("invalid log level")
        return
    try:
        client.index(
            index=constants.index_name,
            document= {
                "level": level,
                "message": message,
                "@timestamp": datetime.now()
            }
        )
    except (BadRequestError) as e:
        print("fail to index:", e)
