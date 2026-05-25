import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL', 'rpsanjaypaul@gmail.com')
DATABASE = 'leads.db'

# Initialize database
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  phone TEXT NOT NULL,
                  purpose TEXT NOT NULL,
                  submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# Helper function to send email
def send_email(name, phone, purpose):
    try:
        subject = f"New Lead Submission - {name}"
        
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #2c3e50;">New Lead Submission</h2>
                <p>You have received a new lead submission:</p>
                
                <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                    <tr style="background-color: #ecf0f1;">
                        <td style="padding: 10px; border: 1px solid #bdc3c7; font-weight: bold;">Name:</td>
                        <td style="padding: 10px; border: 1px solid #bdc3c7;">{name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #bdc3c7; font-weight: bold;">Phone:</td>
                        <td style="padding: 10px; border: 1px solid #bdc3c7;">{phone}</td>
                    </tr>
                    <tr style="background-color: #ecf0f1;">
                        <td style="padding: 10px; border: 1px solid #bdc3c7; font-weight: bold;">Purpose of Contact:</td>
                        <td style="padding: 10px; border: 1px solid #bdc3c7;">{purpose}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #bdc3c7; font-weight: bold;">Submitted At:</td>
                        <td style="padding: 10px; border: 1px solid #bdc3c7;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                </table>
                
                <p style="color: #7f8c8d; font-size: 12px;">This is an automated email. Please do not reply directly to this email.</p>
            </body>
        </html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

# Save lead to database
def save_lead(name, phone, purpose):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('INSERT INTO leads (name, phone, purpose) VALUES (?, ?, ?)',
                  (name, phone, purpose))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving lead: {str(e)}")
        return False

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit-lead', methods=['POST'])
def submit_lead():
    try:
        data = request.get_json()
        
        # Validation
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        purpose = data.get('purpose', '').strip()
        
        if not name or not phone or not purpose:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        if len(name) < 2:
            return jsonify({'success': False, 'message': 'Name must be at least 2 characters'}), 400
        
        if len(phone) < 7:
            return jsonify({'success': False, 'message': 'Phone number must be at least 7 digits'}), 400
        
        if len(purpose) < 5:
            return jsonify({'success': False, 'message': 'Purpose must be at least 5 characters'}), 400
        
        # Save to database
        if not save_lead(name, phone, purpose):
            return jsonify({'success': False, 'message': 'Error saving lead'}), 500
        
        # Send email
        if not send_email(name, phone, purpose):
            return jsonify({'success': False, 'message': 'Lead saved but email notification failed'}), 500
        
        return jsonify({'success': True, 'message': 'Lead submitted successfully!'}), 200
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/leads', methods=['GET'])
def get_leads():
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM leads ORDER BY submitted_at DESC')
        leads = [dict(row) for row in c.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'data': leads}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)