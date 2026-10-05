from confluent_kafka import Consumer, KafkaException
import socket
import constants

conf = {'bootstrap.servers': constants.bootstrap_servers,
        'group.id': 'foo',
        'auto.offset.reset': 'earliest'}

consumer = Consumer(conf)

running = True

def consume_loop(consumer = consumer, topics = [constants.raw_notifications_topic]):
    try:
        consumer.subscribe(topics)

        while running:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                print("waiting..")
                continue
            elif msg.error():
               print("ERROR: %s".format(msg.error()))
            else:
               print("msg:", msg.value())
    finally:
        # Close down consumer to commit final offsets.
        consumer.close()

def shutdown():
    global running
    running = False