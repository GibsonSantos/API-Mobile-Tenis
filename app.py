# app.py
from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

##########################################################
## DATABASE ACCESS
##########################################################

def db_connection():
    db = psycopg2.connect(user = "rqhyeuzdbcvmqq",
                            password = "41c503572ace0b116fc4a9406208e61892a4113fdc9476c6054f8b35620ce002",
                            host = "ec2-54-155-226-153.eu-west-1.compute.amazonaws.com",
                            port = "5432",
                            database = "d68dqm1q7a4oj6")
    return db


@app.route('/getmsg/', methods=['GET'])
def respond():
    # Retrieve the name from url parameter
    name = request.args.get("name", None)

    # For debugging
    print(f"got name {name}")

    response = {}

    # Check if user sent a name at all
    if not name:
        response["ERROR"] = "no name found, please send a name."
    # Check if the user entered a number not a name
    elif str(name).isdigit():
        response["ERROR"] = "name can't be numeric."
    # Now the user entered a valid name
    else:
        response["MESSAGE"] = f"Welcome {name} to our awesome platform!!"

    # Return the response in json format
    return jsonify(response)

@app.route('/post/', methods=['POST'])
def post_something():
    param = request.form.get('name')
    print(param)
    # You can add the test cases you made in the previous function, but in our case here you are just testing the POST functionality
    if param:
        return jsonify({
            "Message": f"Welcome {name} to our awesome platform!!",
            # Add this option to distinct the POST request
            "METHOD" : "POST"
        })
    else:
        return jsonify({
            "ERROR": "no name found, please send a name."
        })

# A welcome message to test our server
@app.route('/')
def index():
    return "<h1>Welcome to our server !!</h1>"


# Database check
@app.route('/database/')
def database_check():
    conn = db_connection()
    cur = conn.cursor()
    cur.execute("SELECT version()")
    rows = cur.fetchall()

    row = rows[0]
    content = {'database': row[0]}

    conn.close ()
    return jsonify(content)

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
