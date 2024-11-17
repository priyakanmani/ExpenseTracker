import os
from flask import Flask, jsonify, request,session
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import plotly.express as px  # Plotly Express for creating charts
import plotly.io as pio      # Plotly I/O for rendering charts
import sqlite3


# Load environment variables from a .env file (if present)
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for the app

# MySQL connection configuration using environment variables
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'Kanmanipriya@123'),
    'database': os.getenv('DB_NAME', 'my_expense_tracker'),
    # 'secret_key':os.getenv('DB_NAME', 'my_expense_tracker'),
}
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'kanmanipriya')
# Establish a connection to MySQL
def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Create database and tables if they do not exist
def create_database_and_table():
    conn = get_db_connection()
    if conn is None:
        print("Failed to connect to the database.")
        return

    cursor = conn.cursor()

    cursor.execute("SHOW DATABASES LIKE 'my_expense_tracker'")
    result = cursor.fetchone()
    if not result:
        cursor.execute("CREATE DATABASE my_expense_tracker")
        print("Database 'my_expense_tracker' created successfully.")
    
    conn.commit()

    # Switch to the my_expense_tracker database
    cursor.execute("USE my_expense_tracker")

    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            amount FLOAT NOT NULL,
            date DATE NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incomes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            amount FLOAT NOT NULL,
            date DATE NOT NULL
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("Tables 'users' and 'expenses' are ready.")

# Initialize the database and table when the app starts
create_database_and_table()

# Route to signup (create a new user)
@app.route('/signup', methods=['POST'])
def signup():
    print("signup")
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Hash the password before saving it
    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Failed to connect to the database."}), 500

    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Signup successful. Please login."}), 201
    except mysql.connector.IntegrityError:
        cursor.close()
        conn.close()
        return jsonify({"message": "Username already exists."}), 400

# Route to login (check user credentials)
@app.route('/login', methods=['POST'])
def login():
    # print("login")
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Failed to connect to the database."}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    # print(user)
    cursor.close()

    if user and check_password_hash(user['password'], password):
        session['username']=username
        print(session['username'])
        return jsonify({"message": "Login successful", "username": user['username']}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401



# Initialize the database and table when the app starts
create_database_and_table()

# Route to fetch all expenses
@app.route('/expenses', methods=['GET'])
def get_expenses():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Failed to connect to the database."}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(expenses)

# Route to add a new expense
@app.route('/expenses', methods=['POST'])
def add_expense():
    new_expense = request.get_json()
    name = new_expense.get('username')
    amount = new_expense.get('amount')
    date = new_expense.get('date')

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Failed to connect to the database."}), 500

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO expenses (username, amount, date)
        VALUES (%s, %s, %s)
    """, (name, amount, date))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Expense added successfully"}), 201

# Route to update an existing expense
@app.route('/expenses/<int:id>', methods=['PUT'])
def update_expense(id):
    updated_expense = request.get_json()
    name = updated_expense.get('username')
    amount = updated_expense.get('amount')
    date = updated_expense.get('date')

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Failed to connect to the database."}), 500

    cursor = conn.cursor()
    cursor.execute("""
        UPDATE expenses 
        SET username = %s, amount = %s, date = %s
        WHERE id = %s
    """, (name, amount, date, id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Expense updated successfully"})

# Route to delete an expense
@app.route('/expenses/<int:id>', methods=['DELETE'])
def delete_expense(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Failed to connect to the database."}), 500

    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Expense deleted successfully"})



@app.route('/expense_bar_chart', methods=['GET'])
def expense_bar_chart():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT date, SUM(amount) as total_amount FROM expenses GROUP BY date ORDER BY date")
    data = cursor.fetchall()
    cursor.close()

    if not data:
        return jsonify({"message": "No data available for chart."}), 404

    # Data preparation for Plotly
    dates = [item['date'] for item in data]
    amounts = [item['total_amount'] for item in data]

    # Return the data in a format Plotly can use
    return jsonify({
        'data': [{
            'x': dates,
            'y': amounts,
            'type': 'bar',
            'name': 'Expenses by Date'
        }],
        'layout': {
            'title': 'Expenses by Date',
            'xaxis': {'title': 'Date'},
            'yaxis': {'title': 'Total Amount'}
        }
    })

@app.route('/expenses_line', methods=['GET'])
def get_expenses_line():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        query = "SELECT DATE_FORMAT(date, '%Y-%m-%d') AS date, amount FROM expenses ORDER BY date"
        cursor.execute(query)
        expenses = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(expenses)
    except mysql.connector.Error as err:
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as e:
        return jsonify({"message": f"Error: {e}"}), 500




@app.route('/incomes_line', methods=['GET'])
def get_incomes_line():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        query = "SELECT DATE_FORMAT(date, '%Y-%m-%d') AS date, amount FROM incomes ORDER BY date"
        cursor.execute(query)
        incomes = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(incomes)
    except mysql.connector.Error as err:
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as e:
        return jsonify({"message": f"Error: {e}"}), 500




# Initialize the database and table when the app starts
create_database_and_table()

# Route to fetch all expenses
@app.route('/incomes', methods=['GET'])
def get_incomes():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Failed to connect to the database."}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM incomes")
    incomes = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(incomes)

# Route to add a new expense
@app.route('/incomes', methods=['POST'])
def add_income():
    new_income = request.get_json()
    name = new_income.get('username')
    amount = new_income.get('amount')
    date = new_income.get('date')

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Failed to connect to the database."}), 500

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO incomes (username, amount, date)
        VALUES (%s, %s, %s)
    """, (name, amount, date))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Income added successfully"}), 201

# Route to update an existing expense
@app.route('/incomes/<int:id>', methods=['PUT'])
def update_income(id):
    updated_income = request.get_json()
    name = updated_income.get('username')
    amount = updated_income.get('amount')
    date = updated_income.get('date')

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Failed to connect to the database."}), 500

    cursor = conn.cursor()
    cursor.execute("""
        UPDATE incomes 
        SET username = %s, amount = %s, date = %s
        WHERE id = %s
    """, (name, amount, date, id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Income updated successfully"})

# Route to delete an expense
@app.route('/incomes/<int:id>', methods=['DELETE'])
def delete_income(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Failed to connect to the database."}), 500

    cursor = conn.cursor()
    cursor.execute("DELETE FROM incomes WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Income deleted successfully"})




@app.route('/income_bar_chart', methods=['GET'])
def income_bar_chart():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT date, SUM(amount) as total_amount FROM incomes GROUP BY date ORDER BY date")
    data = cursor.fetchall()
    cursor.close()

    if not data:
        return jsonify({"message": "No data available for chart."}), 404

    # Data preparation for Plotly
    dates = [item['date'] for item in data]
    amounts = [item['total_amount'] for item in data]

    # Return the data in a format Plotly can use
    return jsonify({
        'data': [{
            'x': dates,
            'y': amounts,
            'type': 'bar',
            'name': 'Incomes by Date'
        }],
        'layout': {
            'title': 'Incomes by Date',
            'xaxis': {'title': 'Date'},
            'yaxis': {'title': 'Total Amount'}
        }
    })




# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)



















