"""
Professional Quiz Platform in Python Flask with Postgres Database
Deploy directly to Heroku from PyCharm
"""

from flask import Flask, render_template, request, jsonify, session
import json
import time
from datetime import datetime, timedelta
import secrets
import os
import random
import string
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Database connection
def get_db_connection():
    """Get database connection using Heroku DATABASE_URL"""
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Parse the DATABASE_URL
        url = urllib.parse.urlparse(database_url)
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
            cursor_factory=RealDictCursor
        )
        return conn
    else:
        # For local development (fallback)
        return None

def init_database():
    """Initialize database tables"""
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            
            # Create quiz_sessions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS quiz_sessions (
                    access_code VARCHAR(10) PRIMARY KEY,
                    start_time TIMESTAMP NOT NULL,
                    questions_data TEXT NOT NULL,
                    answers_data TEXT DEFAULT '{}',
                    completed BOOLEAN DEFAULT FALSE,
                    end_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for faster queries
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_quiz_sessions_completed 
                ON quiz_sessions(completed, start_time)
            """)
            
            conn.commit()
            cur.close()
            conn.close()
            print("Database initialized successfully")
            return True
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        return False

# Initialize database on app start
init_database()

# Quiz data - your converted questions
QUIZ_DATA = {
    "title": "Accounting & Finance Assessment",
    "description": "Professional interview evaluation - 45 minutes",
    "time_limit": 2700,  # 45 minutes in seconds
    "questions": [
        {
            "id": 1,
            "question": "Out of following which is not capital item?",
            "options": [
                "(a) Computer set purchased",
                "(b) Freight charges incurred for purchase of machinery",
                "(c) Compensation paid to employees who are retrenched",
                "(d) Installed family planning center"
            ],
            "correct": 2
        },
        {
            "id": 2,
            "question": "Salary paid to Mohan is debited to Mohan A/c. This error is",
            "options": [
                "(a) Principle error",
                "(b) Compensation error",
                "(c) Omission error",
                "(d) No error at all"
            ],
            "correct": 0
        },
        {
            "id": 3,
            "question": "Which of the following is a current asset?",
            "options": [
                "(a) Building",
                "(b) Machinery",
                "(c) Inventory",
                "(d) Land"
            ],
            "correct": 2
        },
        {
            "id": 4,
            "question": "The accounting equation is:",
            "options": [
                "(a) Assets = Liabilities + Equity",
                "(b) Assets = Liabilities - Equity",
                "(c) Assets + Liabilities = Equity",
                "(d) Assets - Equity = Liabilities"
            ],
            "correct": 0
        },
        {
            "id": 5,
            "question": "Double entry bookkeeping means:",
            "options": [
                "(a) Recording transactions twice",
                "(b) Every debit has a corresponding credit",
                "(c) Using two sets of books",
                "(d) Recording in two different periods"
            ],
            "correct": 1
        },
        {
            "id": 16,
            "question": "Drawing decrease the assets and decrease the liability.\n\nEvaluate this statement as True or False.",
            "options": ["True", "False", "N/A", "N/A"],
            "correct": 1
        },
        {
            "id": 17,
            "question": "A, B, C started joint venture. A brought rs.10000, B Rs.20000, C Rs.30000 and opened joint bank account. Rs.10000 will be credited in joint bank a/c. on the name of A.\n\nEvaluate this statement as True or False.",
            "options": ["True", "False", "N/A", "N/A"],
            "correct": 0
        },
        {
            "id": 18,
            "question": "It is true receipts and payment is like a cash book.\n\nEvaluate this statement as True or False.",
            "options": ["True", "False", "N/A", "N/A"],
            "correct": 0
        },
        {
            "id": 19,
            "question": "Cash discount is never recorded in the books of accounts.\n\nEvaluate this statement as True or False.",
            "options": ["True", "False", "N/A", "N/A"],
            "correct": 1
        },
        {
            "id": 20,
            "question": "The software development expenses for a company engaging in software business is capital expenses if it is for sale.\n\nEvaluate this statement as True or False.",
            "options": ["True", "False", "N/A", "N/A"],
            "correct": 0
        },
        {
            "id": 21,
            "question": "It is not compulsory to record all the business transaction in the books of accounts.\n\nEvaluate this statement as True or False.",
            "options": ["True", "False", "N/A", "N/A"],
            "correct": 1
        },
        {
            "id": 25,
            "question": "Balance Sheet Data:\n• Equity Share: Rs. 500,000\n• Pref. Shares: Rs. 200,000\n• General Reserve: Rs. 300,000\n• Secured Loan: Rs. 500,000\n• Creditors: Rs. 500,000\n• Total Liabilities: Rs. 2,000,000\n• Fixed Assets: Rs. 1,000,000\n• Stock: Rs. 200,000\n• Debtors: Rs. 600,000\n• Cash: Rs. 200,000\n• Total Assets: Rs. 2,000,000\n\nWhat is the Proprietary Ratio?",
            "options": [
                "(a) 0.3 (30%)",
                "(b) 0.5 (50%)",
                "(c) 0.7 (70%)",
                "(d) 0.8 (80%)"
            ],
            "correct": 1
        }
    ]
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    try:
        # Generate a 6-character access code
        access_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Prepare questions (shuffle for security)
        questions = QUIZ_DATA['questions'].copy()
        random.shuffle(questions)
        
        # Store in database
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO quiz_sessions (access_code, start_time, questions_data)
                VALUES (%s, %s, %s)
            """, (access_code, datetime.now(), json.dumps(questions)))
            
            conn.commit()
            cur.close()
            conn.close()
            
            print(f"Created quiz session with code: {access_code}")
            
            return jsonify({
                'success': True,
                'access_code': access_code,
                'quiz_url': request.url_root + 'quiz/' + access_code
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            })
        
    except Exception as e:
        print(f"Error creating quiz session: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to create quiz session: {str(e)}'
        })

@app.route('/quiz/<access_code>')
def quiz(access_code):
    try:
        conn = get_db_connection()
        if not conn:
            return "Database connection failed", 500
            
        cur = conn.cursor()
        cur.execute("""
            SELECT access_code, start_time, questions_data, completed
            FROM quiz_sessions 
            WHERE access_code = %s
        """, (access_code,))
        
        session_data = cur.fetchone()
        cur.close()
        conn.close()
        
        if not session_data:
            return f"Invalid access code: {access_code}", 404
        
        # Check if quiz is completed
        if session_data['completed']:
            return f"Quiz session {access_code} has already been completed", 410
        
        # Check if time expired
        elapsed = datetime.now() - session_data['start_time']
        if elapsed.total_seconds() > QUIZ_DATA['time_limit']:
            # Mark as completed due to timeout
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE quiz_sessions 
                SET completed = TRUE, end_time = %s 
                WHERE access_code = %s
            """, (datetime.now(), access_code))
            conn.commit()
            cur.close()
            conn.close()
            
            return f"Quiz session {access_code} has expired. Time limit: {QUIZ_DATA['time_limit']/60} minutes", 410
        
        questions = json.loads(session_data['questions_data'])
        
        return render_template('quiz.html', 
                             quiz_data=QUIZ_DATA,
                             questions=questions,
                             access_code=access_code)
                             
    except Exception as e:
        print(f"Error loading quiz: {str(e)}")
        return f"Error loading quiz: {str(e)}", 500

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    try:
        data = request.json
        access_code = data.get('access_code')
        question_id = data.get('question_id')
        answer = data.get('answer')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'})
            
        cur = conn.cursor()
        
        # Get current answers
        cur.execute("""
            SELECT answers_data FROM quiz_sessions 
            WHERE access_code = %s AND completed = FALSE
        """, (access_code,))
        
        result = cur.fetchone()
        if not result:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Invalid session'})
        
        # Update answers
        current_answers = json.loads(result['answers_data'] or '{}')
        current_answers[str(question_id)] = answer
        
        cur.execute("""
            UPDATE quiz_sessions 
            SET answers_data = %s 
            WHERE access_code = %s
        """, (json.dumps(current_answers), access_code))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"Answer saved for session {access_code}, question {question_id}: {answer}")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error submitting answer: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    try:
        data = request.json
        access_code = data.get('access_code')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'})
            
        cur = conn.cursor()
        
        # Get session data
        cur.execute("""
            SELECT questions_data, answers_data, completed
            FROM quiz_sessions 
            WHERE access_code = %s
        """, (access_code,))
        
        result = cur.fetchone()
        if not result:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Invalid session'})
        
        if result['completed']:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Quiz already completed'})
        
        # Mark as completed
        cur.execute("""
            UPDATE quiz_sessions 
            SET completed = TRUE, end_time = %s 
            WHERE access_code = %s
        """, (datetime.now(), access_code))
        
        conn.commit()
        cur.close()
        conn.close()
        
        # Calculate score
        questions = json.loads(result['questions_data'])
        answers = json.loads(result['answers_data'] or '{}')
        
        score = 0
        for question in questions:
            question_id = str(question['id'])
            if question_id in answers:
                if answers[question_id] == question['correct']:
                    score += 1
        
        total = len(questions)
        
        print(f"Quiz completed for session {access_code}. Score: {score}/{total}")
        
        return jsonify({
            'success': True,
            'score': score,
            'total': total,
            'percentage': round((score/total)*100, 1)
        })
        
    except Exception as e:
        print(f"Error submitting quiz: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin')
def admin():
    """Admin dashboard to monitor quiz sessions"""
    try:
        conn = get_db_connection()
        if not conn:
            return "Database connection failed", 500
            
        cur = conn.cursor()
        
        # Get active sessions
        cur.execute("""
            SELECT access_code, start_time, answers_data
            FROM quiz_sessions 
            WHERE completed = FALSE 
            ORDER BY start_time DESC
        """)
        
        sessions = cur.fetchall()
        cur.close()
        conn.close()
        
        active_sessions = []
        for session in sessions:
            elapsed = datetime.now() - session['start_time']
            time_remaining = QUIZ_DATA['time_limit'] - elapsed.total_seconds()
            
            if time_remaining > 0:
                answers = json.loads(session['answers_data'] or '{}')
                active_sessions.append({
                    'access_code': session['access_code'],
                    'start_time': session['start_time'].strftime('%H:%M:%S'),
                    'time_remaining': max(0, int(time_remaining)),
                    'questions_answered': len(answers)
                })
        
        return render_template('admin.html', sessions=active_sessions)
        
    except Exception as e:
        print(f"Error loading admin dashboard: {str(e)}")
        return f"Error loading admin dashboard: {str(e)}", 500

@app.route('/get_time_remaining/<access_code>')
def get_time_remaining(access_code):
    """API endpoint for timer updates"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'})
            
        cur = conn.cursor()
        cur.execute("""
            SELECT start_time, completed
            FROM quiz_sessions 
            WHERE access_code = %s
        """, (access_code,))
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if not result:
            return jsonify({'error': 'Invalid session'})
        
        if result['completed']:
            return jsonify({'error': 'Quiz completed'})
        
        elapsed = datetime.now() - result['start_time']
        time_remaining = QUIZ_DATA['time_limit'] - elapsed.total_seconds()
        
        return jsonify({
            'time_remaining': max(0, int(time_remaining)),
            'expired': time_remaining <= 0
        })
        
    except Exception as e:
        print(f"Error getting time remaining: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/test')
def test():
    """Test route to verify Flask and database are working"""
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as session_count FROM quiz_sessions")
            result = cur.fetchone()
            cur.close()
            conn.close()
            return f"Flask app is working on Heroku! Time: {datetime.now()}, Sessions in DB: {result['session_count']}"
        else:
            return f"Flask app is working but database connection failed! Time: {datetime.now()}"
    except Exception as e:
        return f"Flask app is working but database error: {str(e)}. Time: {datetime.now()}"

@app.route('/debug_sessions')
def debug_sessions():
    """Debug route to check active sessions in database"""
    try:
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}
            
        cur = conn.cursor()
        cur.execute("""
            SELECT access_code, start_time, completed, 
                   (EXTRACT(EPOCH FROM (NOW() - start_time))) as elapsed_seconds
            FROM quiz_sessions 
            ORDER BY start_time DESC 
            LIMIT 10
        """)
        
        sessions = cur.fetchall()
        cur.close()
        conn.close()
        
        return {
            'total_sessions': len(sessions),
            'sessions': [dict(session) for session in sessions],
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': str(e)}

# Cleanup old sessions (optional background task)
@app.route('/cleanup_old_sessions')
def cleanup_old_sessions():
    """Remove sessions older than 24 hours"""
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            
            # Delete sessions older than 24 hours
            cur.execute("""
                DELETE FROM quiz_sessions 
                WHERE start_time < NOW() - INTERVAL '24 hours'
            """)
            
            deleted_count = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()
            
            return f"Cleaned up {deleted_count} old sessions"
        else:
            return "Database connection failed"
            
    except Exception as e:
        return f"Cleanup error: {str(e)}"

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return f"Page not found: {request.url}", 404

@app.errorhandler(500)
def internal_error(error):
    return f"Internal server error: {str(error)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
