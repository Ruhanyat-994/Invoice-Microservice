import pika, sys, os, time
from send import email

def main():
    # rabbitmq connection with retry
    creds = pika.PlainCredentials(os.environ.get("RABBITMQ_USER"), os.environ.get("RABBITMQ_PASSWORD"))
    
    print("Connecting to RabbitMQ...")
    for i in range(10):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=os.environ.get("RABBITMQ_HOST"), credentials=creds, heartbeat=0)
            )
            break
        except pika.exceptions.AMQPConnectionError:
            print(f"Connection failed, retrying ({i+1}/10)...")
            time.sleep(5)
    else:
        print("Could not connect to RabbitMQ. Exiting.")
        sys.exit(1)

    channel = connection.channel()
    channel.queue_declare(queue=os.environ.get("NOTIFICATION_QUEUE"), durable=True)

    def callback(ch, method, properties, body):
        err = email.notification(body)
        if err:
            time.sleep(5)
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=os.environ.get("NOTIFICATION_QUEUE"), on_message_callback=callback
    )

    print("Notification Service waiting for messages. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(0)
