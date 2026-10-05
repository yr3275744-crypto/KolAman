import pika
import constants

connection = pika.BlockingConnection(pika.ConnectionParameters(constants.rabbit_host))
channel = connection.channel()