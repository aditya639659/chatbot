from dotenv import load_dotenv
from langchain.agents import tool
import os
import sqlite3
import uuid
from datetime import datetime

# Load environment variables from a .env file
load_dotenv(dotenv_path=".env")

# Database file path
DATABASE_PATH = "complaints.db"

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

def setup_complaints_database():
    """Creates the 'complaints' table for storing complaint records."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Drop the 'complaints' table if it exists (for clean setup)
    cursor.execute("DROP TABLE IF EXISTS complaints")

    # Create the 'complaints' table with the necessary columns
    cursor.execute("""
        CREATE TABLE complaints (
            complaint_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            email TEXT NOT NULL,
            complaint_details TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
    """)

    # Insert sample complaints into the 'complaints' table for testing
    sample_data = [
        ('CMP001', 'John Doe', '1234567890', 'john@example.com', 'Delayed delivery of order #12345', '2025-06-25 10:30:00', 'pending'),
        ('CMP002', 'Jane Smith', '9876543210', 'jane@example.com', 'Received wrong item in my order', '2025-06-26 14:20:00', 'resolved'),
        ('CMP003', 'Mike Johnson', '5555555555', 'mike@example.com', 'Food quality was poor', '2025-06-27 09:15:00', 'pending')
    ]
    
    cursor.executemany("""
        INSERT INTO complaints (complaint_id, name, phone_number, email, complaint_details, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, sample_data)
    
    # Commit the changes to the database
    conn.commit()
    conn.close()

@tool
def create_complaint(name: str, phone_number: str, email: str, complaint_details: str):
    """Creates a new complaint record and returns the complaint ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Generate a unique complaint ID
        complaint_id = "CMP" + str(uuid.uuid4())[:8].upper()
        
        # Insert the new complaint
        cursor.execute("""
            INSERT INTO complaints (complaint_id, name, phone_number, email, complaint_details)
            VALUES (?, ?, ?, ?, ?)
        """, (complaint_id, name, phone_number, email, complaint_details))
        
        conn.commit()
        conn.close()
        
        return {
            "complaint_id": complaint_id,
            "message": "Complaint created successfully"
        }
    except Exception as e:
        conn.close()
        return f"Error creating complaint: {str(e)}"

@tool
def get_complaint_details(complaint_id: str):
    """Returns the complaint details based on the complaint ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch complaint details using the provided complaint_id
        cursor.execute("""
            SELECT complaint_id, name, phone_number, email, complaint_details, created_at 
            FROM complaints WHERE complaint_id = ?
        """, (complaint_id,))
        result = cursor.fetchone()

        if result:
            complaint_data = {
                "complaint_id": result[0],
                "name": result[1],
                "phone_number": result[2],
                "email": result[3],
                "complaint_details": result[4],
                "created_at": result[5]
            }
            conn.close()
            return complaint_data
        else:
            conn.close()
            return "Complaint not found"
    except Exception as e:
        conn.close()
        return f"Error retrieving complaint: {str(e)}"

@tool
def update_complaint_status(complaint_id: str, status: str):
    """Updates the status of a complaint."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE complaints SET status = ? WHERE complaint_id = ?", (status, complaint_id))
        conn.commit()
        conn.close()
        return f"Complaint status updated to {status}"
    except Exception as e:
        conn.close()
        return f"Error updating complaint status: {str(e)}"

# Initialize the database when this module is imported
def initialize_database():
    """Initialize the database with sample data."""
    setup_complaints_database()
    print("SQLite database setup completed successfully!")

if __name__ == "__main__":
    # Test the database setup
    initialize_database()