from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime, date
import calendar
import os

app = Flask(__name__)

# Database configuration
DATABASE = 'calendar.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize SQLite database
def init_db():
    if not os.path.exists(DATABASE):
        print(f"Creating new database: {DATABASE}")
        conn = get_db()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS meetings
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      title TEXT NOT NULL,
                      date TEXT NOT NULL,
                      time TEXT NOT NULL,
                      description TEXT,
                      type TEXT NOT NULL)''')
        conn.commit()
        conn.close()
        print("Database created successfully")
    else:
        print(f"Database {DATABASE} already exists")

# Create database on startup
init_db()

# Static CSS
app.static_folder = 'static'

def get_calendar_data(year, month):
    cal = calendar.monthcalendar(year, month)
    return cal

def get_type_color(type_name):
    colors = {
        'ensaio': 'bg-blue-500',
        'dia_ocupado': 'bg-red-500',
        'apresentacao': 'bg-green-500'
    }
    return colors.get(type_name, 'bg-gray-500')

# Add custom Jinja2 filter
@app.template_filter('month_name')
def month_name(month_number):
    return calendar.month_name[month_number]

@app.route('/')
def index():
    # Get current date or use query parameters for navigation
    current_date = request.args.get('date')
    if current_date:
        current_date = datetime.strptime(current_date, '%Y-%m')
    else:
        current_date = datetime.now()
    
    year = current_date.year
    month = current_date.month
    
    # Get calendar data
    cal = get_calendar_data(year, month)
    
    # Get meetings for the current month
    conn = get_db()
    c = conn.cursor()
    month_str = f"{year:04d}-{month:02d}"
    print(f"Fetching meetings for month: {month_str}")
    
    c.execute('SELECT * FROM meetings WHERE strftime("%Y-%m", date) = ? ORDER BY date, time',
             (month_str,))
    meetings = c.fetchall()
    print(f"Found {len(meetings)} meetings")
    
    # Debug: Print all meetings
    for meeting in meetings:
        print(f"Meeting: {meeting['title']} on {meeting['date']} at {meeting['time']} type: {meeting['type']}")
    
    conn.close()
    
    # Calculate previous and next month
    if month == 1:
        prev_month = f"{year-1}-12"
        next_month = f"{year}-{month+1:02d}"
    elif month == 12:
        prev_month = f"{year}-{month-1:02d}"
        next_month = f"{year+1}-01"
    else:
        prev_month = f"{year}-{month-1:02d}"
        next_month = f"{year}-{month+1:02d}"
    
    return render_template('index.html', 
                         meetings=meetings,
                         calendar=cal,
                         current_month=month,
                         current_year=year,
                         prev_month=prev_month,
                         next_month=next_month,
                         get_type_color=get_type_color)

@app.route('/add_meeting', methods=['GET', 'POST'])
def add_meeting():
    if request.method == 'POST':
        title = request.form['title']
        date = request.form['date']
        time = request.form['time']
        description = request.form['description']
        type_name = request.form['type']
        
        print(f"Adding new meeting: {title} on {date} at {time} type: {type_name}")
        
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute('INSERT INTO meetings (title, date, time, description, type) VALUES (?, ?, ?, ?, ?)',
                     (title, date, time, description, type_name))
            conn.commit()
            print("Meeting added successfully")
        except sqlite3.Error as e:
            print(f"Error adding meeting: {e}")
        finally:
            conn.close()
        
        return redirect(url_for('index'))
    return render_template('add_meeting.html')

@app.route('/edit_meeting/<int:id>', methods=['GET', 'POST'])
def edit_meeting(id):
    conn = get_db()
    c = conn.cursor()
    
    if request.method == 'POST':
        title = request.form['title']
        date = request.form['date']
        time = request.form['time']
        description = request.form['description']
        type_name = request.form['type']
        
        try:
            c.execute('''UPDATE meetings 
                        SET title = ?, date = ?, time = ?, description = ?, type = ?
                        WHERE id = ?''',
                     (title, date, time, description, type_name, id))
            conn.commit()
            print("Meeting updated successfully")
        except sqlite3.Error as e:
            print(f"Error updating meeting: {e}")
        finally:
            conn.close()
        
        return redirect(url_for('index'))
    
    # Get meeting data for the form
    c.execute('SELECT * FROM meetings WHERE id = ?', (id,))
    meeting = c.fetchone()
    conn.close()
    
    if meeting is None:
        return redirect(url_for('index'))
    
    return render_template('edit_meeting.html', meeting=meeting)

@app.route('/delete_meeting/<int:id>', methods=['POST'])
def delete_meeting(id):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('DELETE FROM meetings WHERE id = ?', (id,))
        conn.commit()
        print("Meeting deleted successfully")
    except sqlite3.Error as e:
        print(f"Error deleting meeting: {e}")
    finally:
        conn.close()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
