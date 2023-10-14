from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from collections import Counter as PyCounter
from prometheus_client import start_http_server, Summary, Counter
import pika

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calculations.db'
db = SQLAlchemy(app)

REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
DB_QUERY_TIME = Summary('db_query_processing_seconds', 'Time spent processing database query')

# Initialize Counter metrics for operations
OPERATION_COUNTER = Counter('calculator_operations', 'Count of calculator operations', ['operation'])

# Initialize RabbitMQ connection
def send_message_to_queue(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='calculation_events')
    channel.basic_publish(exchange='', routing_key='calculation_events', body=message)
    print(f" [x] Sent {message}")
    connection.close()

class Calculation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    num1 = db.Column(db.Float, nullable=False)
    num2 = db.Column(db.Float, nullable=False)
    operation = db.Column(db.String(50), nullable=False)
    result = db.Column(db.Float, nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
@REQUEST_TIME.time()
def calculate():
    data = request.get_json()
    num1 = data['num1']
    num2 = data['num2']
    operation = data['operation']
    if operation == 'add':
        result = num1 + num2
    elif operation == 'subtract':
        result = num1 - num2
    elif operation == 'multiply':
        result = num1 * num2
    elif operation == 'divide':
        if num2 == 0:
            return jsonify({'error': 'Cannot divide by zero'})
        result = num1 / num2

    # Increment the counter for the specific operation
    OPERATION_COUNTER.labels(operation=operation).inc()

    @DB_QUERY_TIME.time()
    def add_calculation_to_db():
        new_calculation = Calculation(num1=num1, num2=num2, operation=operation, result=result)
        db.session.add(new_calculation)
        db.session.commit()

    add_calculation_to_db()
    send_message_to_queue(f"New calculation: {operation} Result: {result}")

    return jsonify({'result': result})

if __name__ == '__main__':
    start_http_server(8000)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
