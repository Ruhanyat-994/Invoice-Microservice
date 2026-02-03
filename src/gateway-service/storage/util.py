import os, pika, json

def upload(f, fs, channel, access, output_format="pdf"):
    try:
        fid = fs.put(f)
    except Exception as err:
        print(f"Error putting file in GridFS: {err}")
        return "internal server error, fs level", 500

    message = {
        "invoice_fid": str(fid),
        "processed_fid": None,
        "username": access["username"],
        "format": output_format,
    }

    try:
        channel.basic_publish(
            exchange="",
            routing_key=os.environ.get("INVOICE_QUEUE"),
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as err:
        print(f"Error publishing to RabbitMQ: {err}")
        fs.delete(fid)
        return f"internal server error rabbitmq issue, {err}", 500
