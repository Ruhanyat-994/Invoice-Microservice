import jwt, datetime, os
import psycopg2
from flask import Flask, request

server = Flask(__name__)

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DATABASE_HOST'),
            database=os.getenv('DATABASE_NAME'),
            user=os.getenv('DATABASE_USER'),
            password=os.getenv('DATABASE_PASSWORD'),
            port=5432
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

@server.route('/login', methods=['POST'])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return 'Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'}

    conn = get_db_connection()
    if not conn:
        return 'Database connection error', 500

    cur = conn.cursor()
    query = "SELECT email, password FROM users WHERE email = %s"
    cur.execute(query, (auth.username,))
    user_row = cur.fetchone()
    cur.close()
    conn.close()

    if user_row:
        email, password = user_row
        if auth.username == email and auth.password == password:
            return CreateJWT(auth.username, os.environ['JWT_SECRET'], True)

    return 'Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'}

def CreateJWT(username, secret, authz):
    return jwt.encode(
        {
            "username": username,
            "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1),
            "iat": datetime.datetime.now(tz=datetime.timezone.utc),
            "admin": authz,
        },
        secret,
        algorithm="HS256",
    )

@server.route('/validate', methods=['POST'])
def validate():
    encoded_jwt = request.headers.get('Authorization')
    
    if not encoded_jwt:
        return 'Unauthorized', 401

    try:
        token = encoded_jwt.split(' ')[1]
        decoded_jwt = jwt.decode(token, os.environ['JWT_SECRET'], algorithms=["HS256"])
        return decoded_jwt, 200
    except Exception as e:
        print(f"JWT validation error: {e}")
        return 'Unauthorized', 401

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=5000)
