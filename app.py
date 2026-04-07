from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import hashlib

def generate_password_hash(password):
    import hmac, os, binascii
    salt = binascii.hexlify(os.urandom(16)).decode()
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260000)
    return f"pbkdf2:sha256:260000${salt}${binascii.hexlify(dk).decode()}"

def check_password_hash(pwhash, password):
    try:
        method, salt, stored = pwhash.split('$')
        algo = method.split(':')[1]
        iters = int(method.split(':')[2]) if len(method.split(':')) > 2 else 260000
        import binascii
        dk = hashlib.pbkdf2_hmac(algo, password.encode(), salt.encode(), iters)
        return binascii.hexlify(dk).decode() == stored
    except Exception:
        return False

from datetime import datetime, date, timedelta
import os
from dotenv import load_dotenv

# Load environment variables from .env file (local dev only)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'habuild-secret-2026')

# Database configuration: uses PostgreSQL in production (via DATABASE_URL env var)
# Falls back to SQLite locally if DATABASE_URL not set or empty
DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///habuild_onboarding.db'

# Fix Heroku/Railway-style postgres:// → postgresql:// (SQLAlchemy requires postgresql://)
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Migrate database schema - add missing columns to existing tables
def migrate_db():
    with app.app_context():
        try:
            # Add missing columns to new_joiner table if they don't exist
            from sqlalchemy import text

            missing_columns = {
                'employment_type': 'VARCHAR(100)',
                'contact_number': 'VARCHAR(20)',
                'personal_email': 'VARCHAR(120)',
                'date_of_birth': 'DATE'
            }

            # Check which columns are missing and add them
            for col_name, col_type in missing_columns.items():
                try:
                    db.session.execute(text(f"ALTER TABLE new_joiner ADD COLUMN {col_name} {col_type}"))
                    db.session.commit()
                except Exception:
                    # Column already exists, skip
                    pass
        except Exception as e:
            print(f"Migration warning: {e}")

# Initialize database and seed data on app startup
def init_db():
    with app.app_context():
        db.create_all()
        migrate_db()  # Run migrations after creating tables
        if User.query.count() == 0:  # Only seed if no users exist
            users_data = [
                ('HR Admin', 'hr@habuild.in', 'Onboarding@123', 'admin', 'HR', 'Nagpur'),
                ('Rumani Zore', 'rumani.zore@habuild.in', 'Onboarding@123', 'admin', 'HR', 'Nagpur'),
                ('Saurabh Bothra', 'saurabhbothra@habuild.in', 'Onboarding@123', 'admin', 'Leadership', 'Nagpur'),
                ('Team Manager 1', 'manager1@habuild.in', 'Onboarding@123', 'manager', 'Customer Support', 'Nagpur'),
                ('Team Manager 2', 'manager2@habuild.in', 'Onboarding@123', 'manager', 'Operations', 'Mumbai'),
            ]
            users = []
            for name, email, pwd, role, dept, loc in users_data:
                u = User(name=name, email=email, password_hash=generate_password_hash(pwd),
                         role=role, department=dept, location=loc)
                db.session.add(u)
                users.append(u)
            db.session.commit()

            mgr = User.query.filter_by(email='manager1@habuild.in').first()
            sample_joiners = [
                ('Priya Sharma', 'priya.sharma@habuild.in', 'Customer Support Executive', 'Customer Support', 'Nagpur', date.today() - timedelta(days=25)),
                ('Rohit Verma', 'rohit.verma@habuild.in', 'Customer Support Executive', 'Customer Support', 'Nagpur', date.today() - timedelta(days=5)),
                ('Sneha Kulkarni', 'sneha.kulkarni@habuild.in', 'Customer Support Executive', 'Customer Support', 'Nagpur', date.today()),
            ]
            for name, email, role_title, dept, loc, jdate in sample_joiners:
                j = NewJoiner(name=name, email=email, role_title=role_title,
                              department=dept, location=loc, manager_id=mgr.id, joining_date=jdate)
                db.session.add(j)
                db.session.flush()
                create_default_tasks(j.id, jdate)

# ── MODELS ──────────────────────────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='employee')  # admin / manager / employee
    department = db.Column(db.String(100))
    location = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NewJoiner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    role_title = db.Column(db.String(100))
    department = db.Column(db.String(100))
    location = db.Column(db.String(100))
    employment_type = db.Column(db.String(100))
    contact_number = db.Column(db.String(20))
    personal_email = db.Column(db.String(120))
    date_of_birth = db.Column(db.Date)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    joining_date = db.Column(db.Date)
    status = db.Column(db.String(30), default='active')  # active / completed / exited
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    manager = db.relationship('User', backref='team_joiners')

class OnboardingTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    joiner_id = db.Column(db.Integer, db.ForeignKey('new_joiner.id'), nullable=False)
    category = db.Column(db.String(50))   # pre_joining / day1 / week1 / day30 / day60 / day90
    task_name = db.Column(db.String(200))
    owner = db.Column(db.String(50))      # hr / manager / it / employee
    status = db.Column(db.String(20), default='pending')  # pending / done / na
    due_date = db.Column(db.Date)
    completed_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    joiner = db.relationship('NewJoiner', backref='tasks')

class Evaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    joiner_id = db.Column(db.Integer, db.ForeignKey('new_joiner.id'), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    period = db.Column(db.String(10))  # 30 / 60 / 90
    rating = db.Column(db.Integer)     # 1-5
    strengths = db.Column(db.Text)
    improvements = db.Column(db.Text)
    goals_next = db.Column(db.Text)
    recommend_confirm = db.Column(db.String(10))  # yes / no / extend
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    joiner = db.relationship('NewJoiner', backref='evaluations')
    manager = db.relationship('User', backref='submitted_evals')

class JoinerPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    joiner_id = db.Column(db.Integer, db.ForeignKey('new_joiner.id'), nullable=False)
    period = db.Column(db.String(10))   # 30 / 60 / 90
    goals = db.Column(db.Text)
    kpis = db.Column(db.Text)
    support = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    joiner = db.relationship('NewJoiner', backref='plans')
    author = db.relationship('User', backref='authored_plans')

class HRNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    joiner_id = db.Column(db.Integer, db.ForeignKey('new_joiner.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    note = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    joiner = db.relationship('NewJoiner', backref='hr_notes')
    author = db.relationship('User', backref='hr_notes')

class OnboardingPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    joiner_id = db.Column(db.Integer, db.ForeignKey('new_joiner.id'), unique=True, nullable=False)
    goals_30 = db.Column(db.Text)
    status_30 = db.Column(db.String(30), default='pending')  # on_track / achieved / needs_improvement / delayed / not_started
    comments_30 = db.Column(db.Text)
    goals_60 = db.Column(db.Text)
    status_60 = db.Column(db.String(30), default='pending')
    comments_60 = db.Column(db.Text)
    goals_90 = db.Column(db.Text)
    status_90 = db.Column(db.String(30), default='pending')
    comments_90 = db.Column(db.Text)
    training_support = db.Column(db.Text)
    manager_recommendation = db.Column(db.Text)
    next_action_plan = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    joiner = db.relationship('NewJoiner', backref='onboarding_plan', uselist=False)
    updater = db.relationship('User', backref='updated_plans')

# ── HELPERS ─────────────────────────────────────────────────

DEFAULT_TASKS = [
    ('pre_joining', 'Joining Status', 'hr'),
    ('pre_joining', 'Date Of Joining offered', 'hr'),
    ('pre_joining', 'Designation Offered confirmed', 'hr'),
    ('pre_joining', 'Reporting Manager confirmed', 'hr'),
    ('pre_joining', 'Date of Offer confirmed', 'hr'),
    ('pre_joining', 'Date of offer acceptance', 'hr'),
    ('pre_joining', 'Fixed CTC confirmed', 'hr'),
    ('pre_joining', 'ESOPs confirmed', 'hr'),
    ('pre_joining', 'Variable pay confirmed', 'hr'),
    ('pre_joining', 'Agreement status', 'hr'),
    ('pre_joining', 'BGV Initiated Date', 'hr'),
    ('pre_joining', 'BGV Completion Date', 'hr'),
    ('pre_joining', 'BGV Remarks noted', 'hr'),
    ('pre_joining', 'Employee documents collected (Salary slips, experience letter, Degrees, passbook/cancelled cheque)', 'hr'),
    ('day1', 'Welcome Hamper (From Pebel) Status', 'hr'),
    ('day1', 'Day 1 Welcome Kit Handover', 'hr'),
    ('day1', 'Laptop Assigned', 'it'),
    ('day1', 'Email ID Created', 'it'),
    ('day1', 'Official Email id created', 'it'),
    ('day1', 'Added to Group Email IDs', 'it'),
    ('day1', 'Welcome Mail Sent', 'hr'),
    ('day1', 'Introduction (with Habuild Team) Email Sent', 'hr'),
    ('week1', 'Induction Invite Sent', 'hr'),
    ('week1', 'Induction Completion Date', 'hr'),
    ('week1', 'Induction Feedback Status', 'hr'),
    ('week1', 'Meeting with Founders (Date)', 'hr'),
    ('week1', 'Meeting with Founders (Status)', 'hr'),
    ('week1', 'Meeting with Dept. Lead (Date)', 'hr'),
    ('week1', 'Imp doc - Keka', 'hr'),
    ('week1', 'IDs to be created (CRM and Clickup)', 'it'),
    ('week1', 'Current Status', 'hr'),
]

def create_default_tasks(joiner_id, joining_date):
    offsets = {'pre_joining': -3, 'day1': 0, 'week1': 7, 'day30': 30, 'day60': 60, 'day90': 90}
    for category, task_name, owner in DEFAULT_TASKS:
        due = joining_date + timedelta(days=offsets.get(category, 0))
        task = OnboardingTask(joiner_id=joiner_id, category=category,
                              task_name=task_name, owner=owner, due_date=due)
        db.session.add(task)
    db.session.commit()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

def progress_color(pct):
    if pct >= 80: return '#228B22'
    if pct >= 50: return '#f0a500'
    return '#e05252'

def get_joiner_stats(joiner):
    tasks = joiner.tasks
    total = len(tasks)
    done = sum(1 for t in tasks if t.status == 'done')
    pct = int((done / total * 100)) if total else 0
    days_in = (date.today() - joiner.joining_date).days if joiner.joining_date else 0
    if days_in < 0: phase = 'Pre-Joining'
    elif days_in == 0: phase = 'Day 1'
    elif days_in <= 7: phase = 'Week 1'
    elif days_in <= 30: phase = '30-Day Period'
    elif days_in <= 60: phase = '60-Day Period'
    else: phase = '90-Day Period'
    evals_done = [e.period for e in joiner.evaluations]
    plans_done = [p.period for p in joiner.plans]
    return {'total': total, 'done': done, 'pct': pct, 'phase': phase,
            'days_in': days_in, 'evals_done': evals_done, 'plans_done': plans_done,
            'color': progress_color(pct)}

# ── ROUTES ──────────────────────────────────────────────────

# Initialize database on first request (works with Gunicorn too)
_db_initialized = False

@app.before_request
def initialize_db():
    global _db_initialized
    if not _db_initialized:
        init_db()
        _db_initialized = True

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['name'] = user.name
            session['role'] = user.role
            session['email'] = user.email
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    if role == 'admin':
        query = NewJoiner.query

        # Filters
        dept = request.args.get('dept', '').strip()
        status = request.args.get('status', '').strip()
        search = request.args.get('search', '').strip()

        if dept:
            query = query.filter(NewJoiner.department == dept)
        if status:
            query = query.filter(NewJoiner.status == status)
        if search:
            like = f'%{search}%'
            query = query.filter(
                db.or_(NewJoiner.name.ilike(like), NewJoiner.email.ilike(like))
            )

        joiners = query.order_by(NewJoiner.joining_date.desc()).all()
        stats_list = [(j, get_joiner_stats(j)) for j in joiners]

        all_joiners = NewJoiner.query.all()
        total = len(all_joiners)
        active = sum(1 for j in all_joiners if j.status == 'active')
        pending_evals = 0
        for j in all_joiners:
            s = get_joiner_stats(j)
            if s['days_in'] >= 30 and '30' not in s['evals_done']: pending_evals += 1
            if s['days_in'] >= 60 and '60' not in s['evals_done']: pending_evals += 1
            if s['days_in'] >= 90 and '90' not in s['evals_done']: pending_evals += 1

        departments = sorted({j.department for j in all_joiners if j.department})

        return render_template('admin_dashboard.html', stats_list=stats_list,
                               total=total, active=active, pending_evals=pending_evals,
                               departments=departments,
                               filter_dept=dept, filter_status=status, filter_search=search)

    elif role == 'manager':
        user_id = session['user_id']
        joiners = NewJoiner.query.filter_by(manager_id=user_id, status='active').all()
        stats_list = [(j, get_joiner_stats(j)) for j in joiners]
        return render_template('manager_dashboard.html', stats_list=stats_list)
    else:
        joiner = NewJoiner.query.filter_by(email=session['email']).first()
        if joiner:
            stats = get_joiner_stats(joiner)
            tasks_by_cat = {}
            for t in joiner.tasks:
                tasks_by_cat.setdefault(t.category, []).append(t)
            return render_template('employee_dashboard.html', joiner=joiner,
                                   stats=stats, tasks_by_cat=tasks_by_cat)
        return render_template('employee_dashboard.html', joiner=None, stats=None, tasks_by_cat={})

@app.route('/joiner/<int:joiner_id>')
@login_required
def joiner_detail(joiner_id):
    joiner = NewJoiner.query.get_or_404(joiner_id)
    if session['role'] not in ('admin',) and session.get('user_id') != joiner.manager_id:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    stats = get_joiner_stats(joiner)
    tasks_by_cat = {}
    for t in joiner.tasks:
        tasks_by_cat.setdefault(t.category, []).append(t)
    cat_labels = {'pre_joining':'Pre-Joining','day1':'Day 1','week1':'Week 1',
                  'day30':'30 Days','day60':'60 Days','day90':'90 Days'}
    plans_by_period = {p.period: p for p in joiner.plans}
    notes = sorted(joiner.hr_notes, key=lambda n: n.created_at, reverse=True)
    return render_template('joiner_detail.html', joiner=joiner, stats=stats,
                           tasks_by_cat=tasks_by_cat, cat_labels=cat_labels,
                           plans_by_period=plans_by_period, notes=notes)

@app.route('/joiner/<int:joiner_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_joiner(joiner_id):
    joiner = NewJoiner.query.get_or_404(joiner_id)
    managers = User.query.filter(User.role.in_(['admin', 'manager'])).all()
    if request.method == 'POST':
        joiner.name = request.form['name']
        joiner.email = request.form['email'].lower()
        joiner.role_title = request.form['role_title']
        joiner.department = request.form['department']
        joiner.location = request.form['location']
        joiner.manager_id = int(request.form['manager_id'])
        joiner.joining_date = datetime.strptime(request.form['joining_date'], '%Y-%m-%d').date()
        joiner.status = request.form['status']
        db.session.commit()
        flash(f'{joiner.name}\'s details updated successfully.', 'success')
        return redirect(url_for('joiner_detail', joiner_id=joiner_id))
    return render_template('edit_joiner.html', joiner=joiner, managers=managers)

@app.route('/joiner/<int:joiner_id>/delete', methods=['POST'])
@admin_required
def delete_joiner(joiner_id):
    joiner = NewJoiner.query.get_or_404(joiner_id)
    joiner_name = joiner.name

    # Delete all related records
    OnboardingTask.query.filter_by(joiner_id=joiner_id).delete()
    Evaluation.query.filter_by(joiner_id=joiner_id).delete()
    JoinerPlan.query.filter_by(joiner_id=joiner_id).delete()
    HRNote.query.filter_by(joiner_id=joiner_id).delete()
    OnboardingPlan.query.filter_by(joiner_id=joiner_id).delete()

    # Delete the joiner
    db.session.delete(joiner)
    db.session.commit()

    flash(f'{joiner_name} has been completely deleted.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/joiner/<int:joiner_id>/add-note', methods=['POST'])
@login_required
def add_note(joiner_id):
    if session.get('role') != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    note_text = request.form.get('note', '').strip()
    if note_text:
        note = HRNote(joiner_id=joiner_id, author_id=session['user_id'], note=note_text)
        db.session.add(note)
        db.session.commit()
        flash('Note added.', 'success')
    return redirect(url_for('joiner_detail', joiner_id=joiner_id) + '#hr-notes')

@app.route('/joiner/<int:joiner_id>/plan/<period>', methods=['GET', 'POST'])
@login_required
def joiner_plan(joiner_id, period):
    joiner = NewJoiner.query.get_or_404(joiner_id)
    if session['role'] not in ('admin', 'manager'):
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    existing = JoinerPlan.query.filter_by(joiner_id=joiner_id, period=period).first()
    if request.method == 'POST':
        if existing:
            p = existing
            p.updated_at = datetime.utcnow()
        else:
            p = JoinerPlan(joiner_id=joiner_id, period=period, created_by=session['user_id'])
            db.session.add(p)
        p.goals = request.form.get('goals', '')
        p.kpis = request.form.get('kpis', '')
        p.support = request.form.get('support', '')
        db.session.commit()
        flash(f'{period}-day plan saved successfully!', 'success')
        return redirect(url_for('joiner_detail', joiner_id=joiner_id))
    return render_template('joiner_plan.html', joiner=joiner, period=period, existing=existing)

@app.route('/task/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(task_id):
    task = OnboardingTask.query.get_or_404(task_id)
    new_status = request.form.get('status', 'done')
    task.status = new_status
    if new_status == 'done':
        task.completed_date = date.today()
    else:
        task.completed_date = None
    task.notes = request.form.get('notes', task.notes)
    db.session.commit()

    # Return JSON for AJAX requests, redirect for form submissions
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success', 'new_status': new_status})
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/task/<int:task_id>/update-notes', methods=['POST'])
@login_required
def update_task_notes(task_id):
    task = OnboardingTask.query.get_or_404(task_id)
    task.notes = request.form.get('notes', '').strip()
    db.session.commit()

    # Return JSON for AJAX requests, redirect for form submissions
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success', 'notes': task.notes})
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/evaluate/<int:joiner_id>/<period>', methods=['GET', 'POST'])
@login_required
def evaluate(joiner_id, period):
    joiner = NewJoiner.query.get_or_404(joiner_id)
    if session['role'] not in ('admin', 'manager'):
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    existing = Evaluation.query.filter_by(joiner_id=joiner_id, period=period).first()
    if request.method == 'POST':
        if existing:
            e = existing
        else:
            e = Evaluation(joiner_id=joiner_id, manager_id=session['user_id'], period=period)
            db.session.add(e)
        e.rating = int(request.form.get('rating', 3))
        e.strengths = request.form.get('strengths', '')
        e.improvements = request.form.get('improvements', '')
        e.goals_next = request.form.get('goals_next', '')
        e.recommend_confirm = request.form.get('recommend_confirm', 'yes')
        e.submitted_at = datetime.utcnow()
        db.session.commit()
        flash(f'{period}-day evaluation submitted successfully!', 'success')
        return redirect(url_for('joiner_detail', joiner_id=joiner_id))
    return render_template('evaluation.html', joiner=joiner, period=period, existing=existing)

@app.route('/add-joiner', methods=['GET', 'POST'])
@admin_required
def add_joiner():
    if request.method == 'POST':
        joining_date = datetime.strptime(request.form['joining_date'], '%Y-%m-%d').date()
        manager_input = request.form['manager_name'].strip()

        # Find or create manager
        manager = User.query.filter(
            (User.name == manager_input) | (User.email == manager_input.lower())
        ).first()

        if not manager:
            # Auto-create new manager if doesn't exist
            # Generate email from name if only name provided
            if '@' in manager_input:
                manager_email = manager_input.lower()
                manager_name = manager_input.split('@')[0].replace('.', ' ').title()
            else:
                manager_name = manager_input
                # Generate email: firstname.lastname@habuild.in
                manager_email = manager_name.lower().replace(' ', '.') + '@habuild.in'

            manager = User(
                name=manager_name,
                email=manager_email,
                password_hash=generate_password_hash('TempPassword@123'),
                role='manager',
                department=request.form['department'],
                location=request.form['location'],
            )
            db.session.add(manager)
            db.session.flush()

        # Parse date of birth if provided
        dob = None
        if request.form.get('date_of_birth'):
            dob = datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date()

        j = NewJoiner(
            name=request.form['name'],
            email=request.form['email'].lower(),
            role_title=request.form['role_title'],
            department=request.form['department'],
            location=request.form['location'],
            employment_type=request.form.get('employment_type', '').strip(),
            contact_number=request.form.get('contact_number', '').strip(),
            personal_email=request.form.get('personal_email', '').lower().strip() if request.form.get('personal_email') else None,
            date_of_birth=dob,
            manager_id=manager.id,
            joining_date=joining_date,
        )
        db.session.add(j)
        db.session.flush()
        create_default_tasks(j.id, joining_date)
        flash(f'{j.name} added successfully!', 'success')
        return redirect(url_for('joiner_detail', joiner_id=j.id))
    return render_template('add_joiner.html')

@app.route('/add-user', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        email = request.form['email'].lower()
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return redirect(url_for('add_user'))
        u = User(
            name=request.form['name'],
            email=email,
            password_hash=generate_password_hash(request.form['password']),
            role=request.form['role'],
            department=request.form.get('department', ''),
            location=request.form.get('location', ''),
        )
        db.session.add(u)
        db.session.commit()
        flash(f'User {u.name} created!', 'success')
        return redirect(url_for('manage_users'))
    return render_template('add_user.html')

@app.route('/users')
@admin_required
def manage_users():
    users = User.query.order_by(User.role).all()
    return render_template('manage_users.html', users=users)

@app.route('/joiner/<int:joiner_id>/plan', methods=['GET', 'POST'])
@login_required
def view_plan(joiner_id):
    joiner = NewJoiner.query.get_or_404(joiner_id)
    if session.get('role') not in ('admin', 'manager') and session.get('user_id') != joiner.manager_id:
        flash('You do not have access to this joiner.', 'error')
        return redirect(url_for('dashboard'))

    plan = OnboardingPlan.query.filter_by(joiner_id=joiner_id).first()
    if not plan:
        plan = OnboardingPlan(joiner_id=joiner_id)
        db.session.add(plan)
        db.session.commit()

    if request.method == 'POST':
        plan.goals_30 = request.form.get('goals_30', '')
        plan.status_30 = request.form.get('status_30', 'pending')
        plan.comments_30 = request.form.get('comments_30', '')
        plan.goals_60 = request.form.get('goals_60', '')
        plan.status_60 = request.form.get('status_60', 'pending')
        plan.comments_60 = request.form.get('comments_60', '')
        plan.goals_90 = request.form.get('goals_90', '')
        plan.status_90 = request.form.get('status_90', 'pending')
        plan.comments_90 = request.form.get('comments_90', '')
        plan.training_support = request.form.get('training_support', '')
        plan.manager_recommendation = request.form.get('manager_recommendation', '')
        plan.next_action_plan = request.form.get('next_action_plan', '')
        plan.updated_by = session.get('user_id')
        plan.updated_at = datetime.utcnow()
        db.session.commit()
        flash('30-60-90 Plan updated successfully!', 'success')
        return redirect(url_for('joiner_detail', joiner_id=joiner_id))

    stats = get_joiner_stats(joiner)
    can_edit = session.get('role') == 'admin' or session.get('user_id') == joiner.manager_id
    return render_template('onboarding_plan.html', joiner=joiner, plan=plan, stats=stats, can_edit=can_edit)

# ── SEED DATA ───────────────────────────────────────────────

def seed():
    with app.app_context():
        db.create_all()
        if User.query.count() == 0:
            users_data = [
                ('HR Admin', 'hr@habuild.in', 'Onboarding@123', 'admin', 'HR', 'Nagpur'),
                ('Rumani Zore', 'rumani.zore@habuild.in', 'Onboarding@123', 'admin', 'HR', 'Nagpur'),
                ('Saurabh Bothra', 'saurabhbothra@habuild.in', 'Onboarding@123', 'admin', 'Leadership', 'Nagpur'),
                ('Team Manager 1', 'manager1@habuild.in', 'Onboarding@123', 'manager', 'Customer Support', 'Nagpur'),
                ('Team Manager 2', 'manager2@habuild.in', 'Onboarding@123', 'manager', 'Operations', 'Mumbai'),
            ]
            users = []
            for name, email, pwd, role, dept, loc in users_data:
                u = User(name=name, email=email, password_hash=generate_password_hash(pwd),
                         role=role, department=dept, location=loc)
                db.session.add(u)
                users.append(u)
            db.session.commit()

            mgr = User.query.filter_by(email='manager1@habuild.in').first()
            sample_joiners = [
                ('Priya Sharma', 'priya.sharma@habuild.in', 'Customer Support Executive', 'Customer Support', 'Nagpur', date.today() - timedelta(days=25)),
                ('Rohit Verma', 'rohit.verma@habuild.in', 'Customer Support Executive', 'Customer Support', 'Nagpur', date.today() - timedelta(days=5)),
                ('Sneha Kulkarni', 'sneha.kulkarni@habuild.in', 'Customer Support Executive', 'Customer Support', 'Nagpur', date.today()),
            ]
            for name, email, role_title, dept, loc, jdate in sample_joiners:
                j = NewJoiner(name=name, email=email, role_title=role_title,
                              department=dept, location=loc, manager_id=mgr.id, joining_date=jdate)
                db.session.add(j)
                db.session.flush()
                create_default_tasks(j.id, jdate)

if __name__ == '__main__':
    seed()
    # Development: debug=True, Production: debug=False
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, port=5050, host='0.0.0.0')
