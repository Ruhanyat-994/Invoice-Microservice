import pika, sys, os, time, json
from pymongo import MongoClient
import gridfs
from generator import pdf_gen, excel_gen
from bson.objectid import ObjectId

def main():
    # MongoDB connection
    client = MongoClient(os.environ.get('MONGODB_URI'))
    db = client.get_default_database()
    
    # Use matching collections with Gateway
    fs_raw = gridfs.GridFS(db, collection="raw")
    fs_processed = gridfs.GridFS(db, collection="processed")

    # RabbitMQ connection with retry
    creds = pika.PlainCredentials(os.environ.get("RABBITMQ_USER"), os.environ.get("RABBITMQ_PASSWORD"))
    
    print("Connecting to RabbitMQ...")
    for i in range(10):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=os.environ.get('RABBITMQ_HOST'), credentials=creds, heartbeat=0)
            )
            break
        except pika.exceptions.AMQPConnectionError:
            print(f"Connection failed, retrying ({i+1}/10)...")
            time.sleep(5)
    else:
        print("Could not connect to RabbitMQ. Exiting.")
        sys.exit(1)

    channel = connection.channel()
    channel.queue_declare(queue=os.environ.get("INVOICE_QUEUE"), durable=True)
    channel.queue_declare(queue=os.environ.get("NOTIFICATION_QUEUE"), durable=True)

    def callback(ch, method, properties, body):
        message = json.loads(body)
        print(f"Received message: {message}")
        output_format = message.get("format", "pdf")

        # Get raw data (JSON file) from GridFS
        try:
            raw_file = fs_raw.get(ObjectId(message["invoice_fid"]))
            invoice_data = json.loads(raw_file.read())
        except Exception as e:
            print(f"Error reading raw data: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)
            return

        # Multi-format generation
        temp_path = f"/tmp/{message['invoice_fid']}.{output_format}"
        try:
            if output_format == "pdf":
                pdf_gen.generate(invoice_data, temp_path)
            elif output_format == "excel":
                temp_path = f"/tmp/{message['invoice_fid']}.xlsx"
                excel_gen.generate(invoice_data, temp_path)
            elif output_format == "csv":
                from generator import csv_gen
                csv_gen.generate(invoice_data, temp_path)
            else:
                print(f"Unsupported format: {output_format}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            with open(temp_path, "rb") as f:
                extension = "xlsx" if output_format == "excel" else output_format
                processed_fid = fs_processed.put(f, filename=f"invoice_{message['invoice_fid']}.{extension}")
            os.remove(temp_path)
        except Exception as e:
            print(f"Error generating {output_format}: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)
            return

        message["processed_fid"] = str(processed_fid)
        message["output_extension"] = output_format if output_format != "excel" else "xlsx"

        # Notify via RabbitMQ (next step in pipeline)
        try:
            channel.basic_publish(
                exchange="",
                routing_key=os.environ.get("NOTIFICATION_QUEUE"),
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                ),
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(f"Successfully processed and published: {message}")
        except Exception as e:
            print(f"Error publishing to notification queue: {e}")
            fs_processed.delete(processed_fid)
            ch.basic_nack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=os.environ.get("INVOICE_QUEUE"), on_message_callback=callback
    )

    print("Worker waiting for messages. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(0)
