import os, gridfs, pika, json
from flask import Flask, request, send_file
from flask_pymongo import PyMongo
from auth import validate
from auth_svc import access
from storage import util
from bson.objectid import ObjectId

server = Flask(__name__)

# Use the same MongoDB for both input and output or separate ones? 
# To keep it simple and consistent with the pattern:
mongo_raw = PyMongo(server, uri=os.environ.get('MONGODB_RAW_URI'))
mongo_processed = PyMongo(server, uri=os.environ.get('MONGODB_PROCESSED_URI'))

# GridFS with separate collections
fs_raw = gridfs.GridFS(mongo_raw.db, collection="raw")
fs_processed = gridfs.GridFS(mongo_processed.db, collection="processed")

# RabbitMQ connection with retry
creds = pika.PlainCredentials(os.environ.get("RABBITMQ_USER"), os.environ.get("RABBITMQ_PASSWORD"))
print("Connecting to RabbitMQ...")
import time
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
    import sys
    sys.exit(1)

channel = connection.channel()
channel.queue_declare(queue=os.environ.get("INVOICE_QUEUE"), durable=True)

@server.route("/login", methods=["POST"])
def login():
    token, err = access.login(request)
    if not err:
        return token
    else:
        return err

@server.route("/upload", methods=["POST"])
def upload():
    access_token, err = validate.token(request)
    if err:
        return err

    access_dict = json.loads(access_token)

    if access_dict["admin"]:
        if len(request.files) != 1:
            return "exactly 1 file required", 400

        output_format = request.args.get("format", "pdf").lower()
        if output_format not in ["pdf", "excel", "csv"]:
            return "invalid format. supported: pdf, excel, csv", 400

        for _, f in request.files.items():
            err = util.upload(f, fs_raw, channel, access_dict, output_format)
            if err:
                return err

        return "success!", 200
    else:
        return "not authorized", 401

@server.route("/download", methods=["GET"])
def download():
    access_token, err = validate.token(request)
    if err:
        return err

    access_dict = json.loads(access_token)

    if access_dict["admin"]:
        fid_string = request.args.get("fid")
        if not fid_string:
            return "fid is required", 400

        try:
            out = fs_processed.get(ObjectId(fid_string))
            filename = out.filename or f"{fid_string}.pdf"
            if not filename.endswith((".pdf", ".xlsx", ".csv")):
                # Fallback if no filename in metadata
                filename = f"{fid_string}.pdf"
            return send_file(out, download_name=filename)
        except Exception as err:
            print(f"Error downloading file: {err}")
            return "internal server error", 500

    return "not authorized", 401

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)
