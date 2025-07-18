"""
Professional Quiz Platform in Python Flask
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

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

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

# Store active quiz sessions - Global dictionary
quiz_sessions = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    try:
        # Generate a 6-character access code
        access_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        session_data = {
            'access_code': access_code,
            'start_time': datetime.now(),
            'questions': QUIZ_DATA['questions'].copy(),
            'current_question': 0,
            'answers': {},
            'completed': False
        }
        
        # Shuffle questions for security
        random.shuffle(session_data['questions'])
        
        # Store in global sessions dictionary
        global quiz_sessions
        quiz_sessions[access_code] = session_data
        
        # Debug logging
        print(f"Created quiz session with code: {access_code}")
        print(f"Total active sessions: {len(quiz_sessions)}")
        print(f"Session stored successfully: {access_code in quiz_sessions}")
        
        return jsonify({
            'success': True,
            'access_code': access_code,
            'quiz_url': request.url_root + 'quiz/' + access_code
        })
        
    except Exception as e:
        print(f"Error creating quiz session: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to create quiz session: {str(e)}'
        })

@app.route('/quiz/<access_code>')
def quiz(access_code):
    global quiz_sessions
    
    print(f"Quiz access attempt - Code: {access_code}")
    print(f"Available sessions: {list(quiz_sessions.keys())}")
    
    if access_code not in quiz_sessions:
        error_msg = f"Invalid access code: {access_code}"
        if quiz_sessions:
            error_msg += f". Available codes: {list(quiz_sessions.keys())}"
        else:
            error_msg += ". No active quiz sessions found."
        print(error_msg)
        return error_msg, 404
    
    session_data = quiz_sessions[access_code]
    
    # Check if time expired
    elapsed = datetime.now() - session_data['start_time']
    if elapsed.total_seconds() > QUIZ_DATA['time_limit']:
        session_data['completed'] = True
        print(f"Quiz session {access_code} has expired")
        return f"Quiz session {access_code} has expired. Time limit: {QUIZ_DATA['time_limit']/60} minutes", 410
    
    print(f"Loading quiz for session: {access_code}")
    return render_template('quiz.html', 
                         quiz_data=QUIZ_DATA,
                         questions=session_data['questions'],
                         access_code=access_code)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    try:
        data = request.json
        access_code = data.get('access_code')
        question_id = data.get('question_id')
        answer = data.get('answer')
        
        global quiz_sessions
        
        if access_code in quiz_sessions:
            quiz_sessions[access_code]['answers'][question_id] = answer
            print(f"Answer saved for session {access_code}, question {question_id}: {answer}")
            return jsonify({'success': True})
        else:
            print(f"Invalid session for answer submission: {access_code}")
            return jsonify({'success': False, 'error': 'Invalid session'})
            
    except Exception as e:
        print(f"Error submitting answer: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    try:
        data = request.json
        access_code = data.get('access_code')
        
        global quiz_sessions
        
        if access_code in quiz_sessions:
            session_data = quiz_sessions[access_code]
            session_data['completed'] = True
            session_data['end_time'] = datetime.now()
            
            score = calculate_score(session_data)
            total = len(session_data['questions'])
            
            print(f"Quiz completed for session {access_code}. Score: {score}/{total}")
            
            return jsonify({
                'success': True,
                'score': score,
                'total': total,
                'percentage': round((score/total)*100, 1)
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid session'})
            
    except Exception as e:
        print(f"Error submitting quiz: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin')
def admin():
    """Admin dashboard to monitor quiz sessions"""
    try:
        global quiz_sessions
        active_sessions = []
        
        for code, session in quiz_sessions.items():
            if not session['completed']:
                elapsed = datetime.now() - session['start_time']
                time_remaining = QUIZ_DATA['time_limit'] - elapsed.total_seconds()
                
                active_sessions.append({
                    'access_code': code,
                    'start_time': session['start_time'].strftime('%H:%M:%S'),
                    'time_remaining': max(0, int(time_remaining)),
                    'questions_answered': len(session['answers'])
                })
        
        return render_template('admin.html', sessions=active_sessions)
        
    except Exception as e:
        print(f"Error loading admin dashboard: {str(e)}")
        return f"Error loading admin dashboard: {str(e)}", 500

def calculate_score(session_data):
    """Calculate quiz score"""
    try:
        score = 0
        for question in session_data['questions']:
            question_id = question['id']
            if question_id in session_data['answers']:
                if session_data['answers'][question_id] == question['correct']:
                    score += 1
        return score
    except Exception as e:
        print(f"Error calculating score: {str(e)}")
        return 0

@app.route('/get_time_remaining/<access_code>')
def get_time_remaining(access_code):
    """API endpoint for timer updates"""
    try:
        global quiz_sessions
        
        if access_code in quiz_sessions:
            session_data = quiz_sessions[access_code]
            elapsed = datetime.now() - session_data['start_time']
            time_remaining = QUIZ_DATA['time_limit'] - elapsed.total_seconds()
            
            return jsonify({
                'time_remaining': max(0, int(time_remaining)),
                'expired': time_remaining <= 0
            })
        else:
            return jsonify({'error': 'Invalid session'})
            
    except Exception as e:
        print(f"Error getting time remaining: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/test')
def test():
    """Test route to verify Flask is working"""
    return f"Flask app is working on Heroku! Time: {datetime.now()}"

@app.route('/debug_sessions')
def debug_sessions():
    """Debug route to check active sessions"""
    global quiz_sessions
    return {
        'total_sessions': len(quiz_sessions),
        'session_codes': list(quiz_sessions.keys()),
        'timestamp': datetime.now().isoformat()
    }

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
