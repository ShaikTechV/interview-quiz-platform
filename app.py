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
            "id": 16,
            "question": "Drawing decrease the assets and decrease the liability.\n\nEvaluate this statement as True or False.",
            "options": ["True", "False", "N/A", "N/A"],
            "correct": 1
        },
        # Add your remaining 22 questions here...
    ]
}

# Store active quiz sessions
quiz_sessions = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    access_code = secrets.token_hex(3).upper()  # 6-digit hex code
    
    session_data = {
        'access_code': access_code,
        'start_time': datetime.now(),
        'questions': QUIZ_DATA['questions'].copy(),
        'current_question': 0,
        'answers': {},
        'completed': False
    }
    
    # Shuffle questions for security
    import random
    random.shuffle(session_data['questions'])
    
    quiz_sessions[access_code] = session_data
    
    return jsonify({
        'success': True,
        'access_code': access_code,
        'quiz_url': request.url_root + 'quiz/' + access_code
    })

@app.route('/quiz/<access_code>')
def quiz(access_code):
    if access_code not in quiz_sessions:
        return "Invalid access code", 404
    
    session_data = quiz_sessions[access_code]
    
    # Check if time expired
    elapsed = datetime.now() - session_data['start_time']
    if elapsed.total_seconds() > QUIZ_DATA['time_limit']:
        session_data['completed'] = True
        return render_template('results.html', 
                             score=calculate_score(session_data),
                             total=len(session_data['questions']))
    
    return render_template('quiz.html', 
                         quiz_data=QUIZ_DATA,
                         questions=session_data['questions'],
                         access_code=access_code)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    access_code = data.get('access_code')
    question_id = data.get('question_id')
    answer = data.get('answer')
    
    if access_code in quiz_sessions:
        quiz_sessions[access_code]['answers'][question_id] = answer
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid session'})

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    data = request.json
    access_code = data.get('access_code')
    
    if access_code in quiz_sessions:
        session_data = quiz_sessions[access_code]
        session_data['completed'] = True
        session_data['end_time'] = datetime.now()
        
        score = calculate_score(session_data)
        total = len(session_data['questions'])
        
        return jsonify({
            'success': True,
            'score': score,
            'total': total,
            'percentage': round((score/total)*100, 1)
        })
    
    return jsonify({'success': False})

@app.route('/admin')
def admin():
    """Admin dashboard to monitor quiz sessions"""
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

def calculate_score(session_data):
    """Calculate quiz score"""
    score = 0
    for question in session_data['questions']:
        question_id = question['id']
        if question_id in session_data['answers']:
            if session_data['answers'][question_id] == question['correct']:
                score += 1
    return score

@app.route('/get_time_remaining/<access_code>')
def get_time_remaining(access_code):
    """API endpoint for timer updates"""
    if access_code in quiz_sessions:
        session_data = quiz_sessions[access_code]
        elapsed = datetime.now() - session_data['start_time']
        time_remaining = QUIZ_DATA['time_limit'] - elapsed.total_seconds()
        
        return jsonify({
            'time_remaining': max(0, int(time_remaining)),
            'expired': time_remaining <= 0
        })
    
    return jsonify({'error': 'Invalid session'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
