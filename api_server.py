from flask import Flask, request, jsonify, abort
import uuid
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv
import re
import json

# Load environment variables
load_dotenv(dotenv_path=".env")

# Initialize Flask app
app = Flask(__name__)

# Database file path
DATABASE_PATH = "complaints.db"

# Database connection function
def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

# Initialize database
def init_database():
    """Create the complaints table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            email TEXT NOT NULL,
            complaint_details TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
    """)
    
    # Insert sample data if table is empty
    cursor.execute("SELECT COUNT(*) FROM complaints")
    if cursor.fetchone()[0] == 0:
        sample_data = [
            ('CMP001', 'John Doe', '1234567890', 'john@example.com', 'Delayed delivery of order #12345', '2025-06-25 10:30:00', 'pending'),
            ('CMP002', 'Jane Smith', '9876543210', 'jane@example.com', 'Received wrong item in my order', '2025-06-26 14:20:00', 'resolved'),
            ('CMP003', 'Mike Johnson', '5555555555', 'mike@example.com', 'Food quality was poor', '2025-06-27 09:15:00', 'pending')
        ]
        
        cursor.executemany("""
            INSERT INTO complaints (complaint_id, name, phone_number, email, complaint_details, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_data)
    
    conn.commit()
    conn.close()

# Initialize database at startup
init_database()

# Validation functions
def validate_phone_number(phone: str) -> bool:
    """Validate phone number format."""
    pattern = r'^[\+]?[1-9]?[0-9]{7,15}$'
    return re.match(pattern, phone) is not None

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# API Endpoints
@app.route("/complaints", methods=["POST"])
def create_complaint():
    """Create a new complaint record."""
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            abort(400, description="Invalid JSON data")

        # Validate required fields
        required_fields = ["name", "phone_number", "email", "complaint_details"]
        for field in required_fields:
            if field not in data or not data[field]:
                abort(400, description=f"Missing or empty field: {field}")

        # Validate phone number
        if not validate_phone_number(data["phone_number"]):
            abort(400, description="Invalid phone number format")

        # Validate email
        if not validate_email(data["email"]):
            abort(400, description="Invalid email format")

        # Validate name and complaint details
        if not data["name"].strip() or not data["complaint_details"].strip():
            abort(400, description="Name and complaint details are required")

        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Generate a unique complaint ID
            complaint_id = "CMP" + str(uuid.uuid4())[:8].upper()
            
            # Insert the new complaint
            cursor.execute("""
                INSERT INTO complaints (complaint_id, name, phone_number, email, complaint_details)
                VALUES (?, ?, ?, ?, ?)
            """, (complaint_id, data["name"], data["phone_number"], 
                  data["email"], data["complaint_details"]))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                "complaint_id": complaint_id,
                "message": "Complaint created successfully"
            }), 200
            
        except Exception as e:
            conn.close()
            abort(500, description=f"Error creating complaint: {str(e)}")

    except ValueError as e:
        abort(400, description=str(e))

@app.route("/complaints/<complaint_id>", methods=["GET"])
def get_complaint(complaint_id):
    """Retrieve complaint details by complaint ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Fetch complaint details
        cursor.execute("""
            SELECT complaint_id, name, phone_number, email, complaint_details, created_at 
            FROM complaints WHERE complaint_id = ?
        """, (complaint_id,))
        
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            abort(404, description="Complaint not found")
        
        complaint_data = {
            "complaint_id": result["complaint_id"],
            "name": result["name"],
            "phone_number": result["phone_number"],
            "email": result["email"],
            "complaint_details": result["complaint_details"],
            "created_at": result["created_at"]
        }
        
        conn.close()
        return jsonify(complaint_data), 200
        
    except Exception as e:
        conn.close()
        abort(500, description=f"Error retrieving complaint: {str(e)}")

@app.route("/")
def root():
    """Root endpoint."""
    return jsonify({"message": "Complaint Management API is running"}), 200

@app.route("/health")
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)