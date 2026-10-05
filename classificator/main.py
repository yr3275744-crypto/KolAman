import kafka_client
import elastic_logger

def main():
    elastic_logger.create_index()
    kafka_client.consume_loop()

if __name__ == "__main__":
    main()