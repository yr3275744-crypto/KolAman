import pika
import constants

connection = pika.BlockingConnection(pika.ConnectionParameters(constants.rabbit_host))
channel = connection.channel()

channel.queue_declare(queue=constants.north_queue, durable=True, arguments=None)
channel.queue_declare(queue=constants.center_queue, durable=True, arguments=None)
channel.queue_declare(queue=constants.south_queue, durable=True, arguments=None)
channel.queue_declare(queue=constants.depth_queue, durable=True, arguments=None)


def send(routing_key, body):
    # try:
    channel.basic_publish(exchange='',
                          routing_key=routing_key,
                          body=body)