import redis
import constants

r_client = redis.Redis(host=constants.host, port=constants.port, decode_responses=True)

