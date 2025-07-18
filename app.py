"""
Professional Quiz Platform in Python Flask with Postgres Database
Deploy directly to Heroku from PyCharm - FINAL VERSION WITH TEXT INPUT
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
import re

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
                    score INTEGER DEFAULT 0,
                    total_questions INTEGER DEFAULT 0,
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

# Helper function to check text answers
def check_text_answer(user_answer, correct_answers):
    """Check if user's text answer matches any of the correct answers"""
    if not user_answer:
        return False
    
    user_answer = str(user_answer).strip().lower()
    
    for correct in correct_answers:
        correct = str(correct).strip().lower()
        
        # Exact match
        if user_answer == correct:
            return True
        
        # Remove common formatting
        user_clean = re.sub(r'[%\s]', '', user_answer)
        correct_clean = re.sub(r'[%\s]', '', correct)
        
        if user_clean == correct_clean:
            return True
    
    return False

# Quiz data - All 25 questions with text input support
QUIZ_DATA = {
    "title": "Accounting & Finance Assessment",
    "description": "Professional interview evaluation - 45 minutes",
    "time_limit": 2700,  # 45 minutes in seconds
    "questions": [
        {
            "id": 1,
            "type": "multiple_choice",
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
            "type": "multiple_choice",
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
            "type": "multiple_choice",
            "question": "XYZ Co. failed to agree and the difference was put into suspense account. Pass the rectifying entry:",
            "options": [
                "(a) Dr. Suspense A/c. 3000, Cr. Discount received A/c. 2000, Cr. Discount allowed a/c. 1000",
                "(b) Dr. Discount received A/c. 2000, Dr. Discount allowed a/c. 1000, Cr. Suspense A/c. 3000",
                "(c) No entry is required",
                "(d) Any entry a or b"
            ],
            "correct": 0
        },
        {
            "id": 4,
            "type": "multiple_choice",
            "question": "Calculate the operating profit: Sales Rs. 10,00,000, Opening stock Rs. 1,00,000, Purchases Rs. 6,50,000, Closing stock Rs. 1,50,000, Office rent Rs. 45,000, Salaries Rs. 90,000",
            "options": [
                "(a) Rs. 4,65,000",
                "(b) Rs. 5,50,000",
                "(c) Rs. 4,30,000",
                "(d) Rs. 4,75,000"
            ],
            "correct": 0
        },
        {
            "id": 5,
            "type": "multiple_choice",
            "question": "Salaries due for the month of March will appear",
            "options": [
                "(a) On the receipt side of the cash book",
                "(b) On the payment side of the cash book",
                "(c) As a contra entry",
                "(d) Nowhere in cash book"
            ],
            "correct": 3
        },
        {
            "id": 6,
            "type": "multiple_choice",
            "question": "From the following information, determine amounts to be transferred to Income & Expenditure A/c: Subscription received Rs. 5,000, Subscription outstanding Rs. 2,500",
            "options": [
                "(a) Rs. 2,500",
                "(b) Rs. 2,000",
                "(c) Rs. 500",
                "(d) Rs. 3,000"
            ],
            "correct": 0
        },
        {
            "id": 7,
            "type": "multiple_choice",
            "question": "Opening balance: Proprietor's A/c. Rs. 50,000, Current year profit Rs. 4,50,000, Drawings Rs. 1,00,000. Calculate closing balance of Proprietor's A/c.",
            "options": [
                "(a) Rs. 5,00,000",
                "(b) Rs. 4,00,000",
                "(c) Rs. 6,00,000",
                "(d) Rs. 7,00,000"
            ],
            "correct": 0
        },
        {
            "id": 8,
            "type": "multiple_choice",
            "question": "Goods worth Rs.18,800 are destroyed by fire and the insurance company admits the claim for Rs.15,000. Loss by fire account will be",
            "options": [
                "(a) debited by Rs.18,800",
                "(b) debited by Rs.3,800",
                "(c) credited by Rs.18,800",
                "(d) credited by Rs.3,800"
            ],
            "correct": 1
        },
        {
            "id": 9,
            "type": "multiple_choice",
            "question": "Which one is correct?",
            "options": [
                "(a) Assets + Liabilities = Owner's equity",
                "(b) Assets – Liabilities = Owner's equity",
                "(c) Owner's equity + Assets = Liability",
                "(d) None of the above"
            ],
            "correct": 1
        },
        {
            "id": 10,
            "type": "multiple_choice",
            "question": "Advances given to Govt. Authority is shown as",
            "options": [
                "(a) Current assets",
                "(b) Fixed assets",
                "(c) Liability",
                "(d) Capital"
            ],
            "correct": 0
        },
        {
            "id": 11,
            "type": "multiple_choice",
            "question": "Health Club has 1,000 members. Annual fees for each member Rs.1,000. Rs.2 L received in advance, Rs.1 L in arrears. Amount to be credited to Income & Expenditure A/c:",
            "options": [
                "(a) Rs.8 L",
                "(b) Rs.6 L",
                "(c) Rs.10 L",
                "(d) Rs.12 L"
            ],
            "correct": 1
        },
        {
            "id": 12,
            "type": "multiple_choice",
            "question": "When sales Rs.300000, Purchase Rs.200000, Opening stock Rs.10000, Closing stock Rs.40000, what is gross profit?",
            "options": [
                "(a) Rs. 50,000",
                "(b) Rs. 20,000",
                "(c) Rs. 36,000",
                "(d) Rs. 60,000"
            ],
            "correct": 0
        },
        {
            "id": 13,
            "type": "multiple_choice",
            "question": "From the information, Vimal Ltd received from its branch: Goods sent to branch Rs. 5,00,000, Cash received from branch Rs. 2,00,000, Expenses of branch Rs. 1,00,000, Closing stock at branch Rs. 1,00,000. Branch adjustment account will show:",
            "options": [
                "(a) Rs. 3,00,000",
                "(b) Rs. 2,00,000",
                "(c) Rs. 1,00,000",
                "(d) Rs. 4,00,000"
            ],
            "correct": 0
        },
        {
            "id": 14,
            "type": "multiple_choice",
            "question": "What amount will be credited in income expenditure account for subscription: Subscription received Rs.10 L, Subscription due for previous year Rs.1 L, Subscription due for current year Rs.3 L, Subscription received in advance Rs.1 L",
            "options": [
                "(a) Rs. 10 L",
                "(b) Rs. 12 L",
                "(c) Rs. 14 L",
                "(d) Rs. 11 L"
            ],
            "correct": 3
        },
        {
            "id": 15,
            "type": "multiple_choice",
            "question": "Following information provided by ABC Club: Subscription received current year Rs.5 L, Subscription outstanding beginning Rs.2 L, Subscription outstanding end Rs.1 L, Subscription received in advance beginning Rs.1 L, Subscription received in advance end Rs.2 L. Amount to be credited:",
            "options": [
                "(a) Rs. 4 L",
                "(b) Rs. 5 L",
                "(c) Rs. 3 L",
                "(d) Rs. 9 L"
            ],
            "correct": 0
        },
        {
            "id": 16,
            "type": "true_false",
            "question": "Drawing decrease the assets and decrease the liability.\n\nEvaluate this statement as True or False.",
            "options": ["True", "False", "N/A", "N/A"],
            "correct": 1
        },
        {
            "id": 17,
            "type": "true_false",
            "question": "A, B, C started joint venture. A brought rs.10000, B Rs.20000, C Rs.30000 and opened joint bank account. Rs.10000 will be credited in joint bank a/c. on the name of A.\n\nEvaluate this statement as True or False.",
            "options": ["True", "False", "N/A", "N/A"],
            "correct": 0
        },
        {
            "id": 18,
            "type": "true_false",
            "question": "It is true receipts and payment is like a cash book.\n\nEvaluate this statement as True or False.",
            "options": ["True", "False", "N/A", "N/A"],
            "correct": 0
        },
        {
            "id": 19,
            "type": "true_false",
            "question": "Cash discount is never recorded in the books of accounts.\n\nEvaluate this statement as True or False.",
            "options": ["True", "False", "N/A", "N/A"],
            "correct": 1
        },
        {
            "id": 20,
            "type": "true_false",
            "question": "The software development expenses for a company engaging in software business is capital expenses if it is for sale.\n\nEvaluate this statement as True or False.",
            "options": ["True", "False", "N/A", "N/A"],
            "correct": 1
        },
        {
            "id": 21,
            "type": "true_false",
            "question": "It is not compulsory to record all the business transaction in the books of accounts.\n\nEvaluate this statement as True or False.",
            "options": ["True", "False", "N/A", "N/A"],
            "correct": 1
        },
        {
            "id": 22,
            "type": "multiple_choice",
            "question": "If person invest Rs.2,00,000 in our investment which pays 12% compounded annually. What will be the future value after 10 years?",
            "options": [
                "(a) Rs. 6,21,200",
                "(b) Rs. 5,00,000",
                "(c) Rs. 6,42,200",
                "(d) Rs. 8,10,500"
            ],
            "correct": 0
        },
        {
            "id": 23,
            "type": "multiple_choice",
            "question": "PAT of the project is Rs.50 Lac, initial investment is Rs.500 Lac. What is the accounting rate of return (ARR)?",
            "options": [
                "(a) 5%",
                "(b) 20%",
                "(c) 10%",
                "(d) 2%"
            ],
            "correct": 2
        },
        {
            "id": 24,
            "type": "multiple_choice",
            "question": "Which of the following is a solvency ratio?",
            "options": [
                "(a) Liquidity Ratio",
                "(b) Operating Ratio",
                "(c) Capital Gearing Ratio",
                "(d) Net Profit Ratio"
            ],
            "correct": 2
        },
        {
            "id": 25,
            "type": "text_input",
            "question": "Calculate the Proprietary Ratio from the following Balance Sheet Data:\n\n• Equity Share: Rs. 500,000\n• Pref. Shares: Rs. 200,000\n• General Reserve: Rs. 300,000\n• Secured Loan: Rs. 500,000\n• Creditors: Rs. 500,000\n• Total Liabilities: Rs. 2,000,000\n• Fixed Assets: Rs. 1,000,000\n• Stock: Rs. 200,000\n• Debtors: Rs. 600,000\n• Cash: Rs. 200,000\n• Total Assets: Rs. 2,000,000\n\nEnter your answer as a decimal (e.g., 0.5) or percentage (e.g., 50%):",
            "correct_answers": ["0.5", "50%", "50", "0.50", "50.0%", "50.0"],
            "explanation": "Proprietary Ratio = Owner's Equity / Total Assets = (500,000 + 200,000 + 300,000) / 2,000,000 = 1,000,000 / 2,000,000 = 0.5 or 50%"
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
                INSERT INTO quiz_sessions (access_code, start_time, questions_data, total_questions)
                VALUES (%s, %s, %s, %s)
            """, (access_code, datetime.now(), json.dumps(questions), len(questions)))
            
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
        
        return jsonify({'success': True})
        
    except Exception as e:
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
        
        # Calculate score
        questions = json.loads(result['questions_data'])
        answers = json.loads(result['answers_data'] or '{}')
        
        score = 0
        for question in questions:
            question_id = str(question['id'])
            if question_id in answers:
                user_answer = answers[question_id]
                
                # Handle different question types
                if question.get('type') == 'text_input':
                    # Check text input answers
                    if check_text_answer(user_answer, question.get('correct_answers', [])):
                        score += 1
                else:
                    # Handle multiple choice and true/false
                    if user_answer == question['correct']:
                        score += 1
        
        total = len(questions)
        
        # Mark as completed and store score
        cur.execute("""
            UPDATE quiz_sessions 
            SET completed = TRUE, end_time = %s, score = %s, total_questions = %s
            WHERE access_code = %s
        """, (datetime.now(), score, total, access_code))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"Quiz completed for session {access_code}. Score: {score}/{total}")
        
        return jsonify({
            'success': True,
            'score': score,
            'total': total,
            'percentage': round((score/total)*100, 1)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin')
def admin():
    """Admin dashboard to monitor quiz sessions and view results"""
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
        
        active_sessions_data = cur.fetchall()
        
        # Get completed sessions with results
        cur.execute("""
            SELECT access_code, start_time, end_time, score, total_questions, 
                   questions_data, answers_data
            FROM quiz_sessions 
            WHERE completed = TRUE 
            ORDER BY end_time DESC
            LIMIT 20
        """)
        
        completed_sessions_data = cur.fetchall()
        cur.close()
        conn.close()
        
        # Process active sessions
        active_sessions = []
        for session in active_sessions_data:
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
        
        # Process completed sessions
        completed_sessions = []
        for session in completed_sessions_data:
            duration = 'N/A'
            if session['end_time'] and session['start_time']:
                duration_seconds = (session['end_time'] - session['start_time']).total_seconds()
                duration_minutes = int(duration_seconds // 60)
                duration = f"{duration_minutes} min"
            
            percentage = 0
            if session['total_questions'] and session['total_questions'] > 0:
                percentage = round((session['score'] / session['total_questions']) * 100, 1)
            
            completed_sessions.append({
                'access_code': session['access_code'],
                'start_time': session['start_time'].strftime('%Y-%m-%d %H:%M'),
                'end_time': session['end_time'].strftime('%Y-%m-%d %H:%M') if session['end_time'] else 'N/A',
                'duration': duration,
                'score': session['score'] or 0,
                'total': session['total_questions'] or 0,
                'percentage': percentage
            })
        
        return render_template('admin.html', 
                             active_sessions=active_sessions, 
                             completed_sessions=completed_sessions)
        
    except Exception as e:
        print(f"Error loading admin dashboard: {str(e)}")
        return f"Error loading admin dashboard: {str(e)}", 500

@app.route('/quiz_details/<access_code>')
def quiz_details(access_code):
    """View detailed results for a specific quiz session"""
    try:
        conn = get_db_connection()
        if not conn:
            return "Database connection failed", 500
            
        cur = conn.cursor()
        cur.execute("""
            SELECT access_code, start_time, end_time, score, total_questions, 
                   questions_data, answers_data, completed
            FROM quiz_sessions 
            WHERE access_code = %s
        """, (access_code,))
        
        session = cur.fetchone()
        cur.close()
        conn.close()
        
        if not session:
            return f"Quiz session {access_code} not found", 404
        
        if not session['completed']:
            return f"Quiz session {access_code} is still active", 400
        
        # Parse data
        questions = json.loads(session['questions_data'])
        answers = json.loads(session['answers_data'] or '{}')
        
        # Create detailed results
        question_results = []
        for i, question in enumerate(questions):
            question_id = str(question['id'])
            user_answer = answers.get(question_id, -1)
            
            # Handle different question types
            if question.get('type') == 'text_input':
                # Text input question
                correct_answers = question.get('correct_answers', [])
                is_correct = check_text_answer(user_answer, correct_answers)
                user_answer_text = str(user_answer) if user_answer != -1 else "Not answered"
                correct_answer_text = " or ".join(correct_answers[:3])  # Show first 3 correct answers
                
                question_results.append({
                    'question_number': i + 1,
                    'question_text': question['question'],
                    'question_type': 'text_input',
                    'user_answer': user_answer,
                    'user_answer_text': user_answer_text,
                    'correct_answer_text': correct_answer_text,
                    'is_correct': is_correct,
                    'explanation': question.get('explanation', '')
                })
            else:
                # Multiple choice or true/false
                correct_answer = question['correct']
                is_correct = user_answer == correct_answer
                
                user_answer_text = "Not answered"
                correct_answer_text = "N/A"
                
                if user_answer >= 0 and user_answer < len(question['options']):
                    user_answer_text = question['options'][user_answer]
                
                if correct_answer >= 0 and correct_answer < len(question['options']):
                    correct_answer_text = question['options'][correct_answer]
                
                question_results.append({
                    'question_number': i + 1,
                    'question_text': question['question'],
                    'question_type': question.get('type', 'multiple_choice'),
                    'options': question['options'],
                    'user_answer': user_answer,
                    'user_answer_text': user_answer_text,
                    'correct_answer': correct_answer,
                    'correct_answer_text': correct_answer_text,
                    'is_correct': is_correct
                })
        
        return render_template('quiz_details.html', 
                             session=session, 
                             question_results=question_results)
        
    except Exception as e:
        return f"Error loading quiz details: {str(e)}", 500

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
            return f"Flask app is working on Heroku! Time: {datetime.now()}, Sessions in DB: {result['session_count']}, Total Questions: {len(QUIZ_DATA['questions'])}"
        else:
            return f"Flask app is working but database connection failed! Time: {datetime.now()}, Total Questions: {len(QUIZ_DATA['questions'])}"
    except Exception as e:
        return f"Flask app is working but database error: {str(e)}. Time: {datetime.now()}, Total Questions: {len(QUIZ_DATA['questions'])}"

@app.route('/debug_sessions')
def debug_sessions():
    """Debug route to check active sessions in database"""
    try:
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}
            
        cur = conn.cursor()
        cur.execute("""
            SELECT access_code, start_time, completed, score, total_questions,
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
            'total_questions': len(QUIZ_DATA['questions']),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': str(e)}

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
