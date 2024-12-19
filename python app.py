# Main frameworks and tools used:
# - Flask for backend API
# - Firebase or SQLite for user and ride data storage
# - React Native (or Flutter) for mobile front-end (to be built separately)

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database setup (use SQLite for simplicity)
db_file = 'rapido_clone.db'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_file}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Disable debug mode to avoid issues in some environments
app.config['DEBUG'] = False

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    user_type = db.Column(db.String(10), nullable=False)  # 'rider' or 'driver'
    password = db.Column(db.String(100), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

# Ride model
class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rider_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    pickup_location = db.Column(db.String(200), nullable=False)
    dropoff_location = db.Column(db.String(200), nullable=False)
    fare = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='requested')  # requested, ongoing, completed
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize database if not exists
if not os.path.exists(db_file):
    with app.app_context():
        db.create_all()
        print("Database initialized.")

# User registration endpoint
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data['name']
    phone = data['phone']
    user_type = data['user_type']  # 'rider' or 'driver'
    password = data['password']

    # Check if user already exists
    if User.query.filter_by(phone=phone).first():
        return jsonify({'message': 'Phone number already registered'}), 400

    new_user = User(name=name, phone=phone, user_type=user_type, password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'})

# User login endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    phone = data['phone']
    password = data['password']

    user = User.query.filter_by(phone=phone, password=password).first()

    if not user:
        return jsonify({'message': 'Invalid credentials'}), 401

    return jsonify({'message': 'Login successful', 'user_id': user.id, 'user_type': user.user_type})

# Request ride endpoint
@app.route('/ride/request', methods=['POST'])
def request_ride():
    data = request.json
    rider_id = data['rider_id']
    pickup_location = data['pickup_location']
    dropoff_location = data['dropoff_location']
    fare = data['fare']

    new_ride = Ride(rider_id=rider_id, driver_id=None, pickup_location=pickup_location,
                    dropoff_location=dropoff_location, fare=fare, status='requested')
    db.session.add(new_ride)
    db.session.commit()

    return jsonify({'message': 'Ride requested successfully', 'ride_id': new_ride.id})

# Driver accepts ride endpoint
@app.route('/ride/accept', methods=['POST'])
def accept_ride():
    data = request.json
    ride_id = data['ride_id']
    driver_id = data['driver_id']

    ride = Ride.query.get(ride_id)
    if not ride or ride.status != 'requested':
        return jsonify({'message': 'Ride not available'}), 400

    ride.driver_id = driver_id
    ride.status = 'ongoing'
    db.session.commit()

    return jsonify({'message': 'Ride accepted successfully'})

# Complete ride endpoint
@app.route('/ride/complete', methods=['POST'])
def complete_ride():
    data = request.json
    ride_id = data['ride_id']

    ride = Ride.query.get(ride_id)
    if not ride or ride.status != 'ongoing':
        return jsonify({'message': 'Invalid ride'}), 400

    ride.status = 'completed'
    db.session.commit()

    return jsonify({'message': 'Ride completed successfully'})

# Fetch rides for driver or rider
@app.route('/rides', methods=['GET'])
def get_rides():
    user_id = request.args.get('user_id')
    user_type = request.args.get('user_type')  # 'rider' or 'driver'

    if user_type == 'rider':
        rides = Ride.query.filter_by(rider_id=user_id).all()
    elif user_type == 'driver':
        rides = Ride.query.filter_by(driver_id=user_id).all()
    else:
        return jsonify({'message': 'Invalid user type'}), 400

    rides_list = [
        {
            'ride_id': ride.id,
            'pickup_location': ride.pickup_location,
            'dropoff_location': ride.dropoff_location,
            'fare': ride.fare,
            'status': ride.status
        } for ride in rides
    ]

    return jsonify({'rides': rides_list})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=False)
