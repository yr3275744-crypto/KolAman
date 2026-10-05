import pathlib
# data_file_path= pathlib.Path("data/regions.geojson")
# print(data_file_path)
data_file_path= "data/regions.geojson"
#enums
priority_values = ["CRITICAL" , "HIGH" , "MEDIUM" , "LOW"]
classification_values = ["UNCLASSIFIED" , "RESTRICTED" , "SECRET", "TOP_SECRET"]
status_values = ["WAITING"]

#kafka
bootstrap_servers = "localhost:9092"
raw_notifications_topic = "raw-notifications"
group_id = "group-1"

#redis
host="localhost"
port=6379

# elastic logger
elastic_host="http://localhost:9200"
index_name="classificator-logs"
level_values= ["INFO", "WARNING", "ERROR", "CRITICAL"]

#rabbit
rabbit_host="localhost"
