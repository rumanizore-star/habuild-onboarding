# Habuild Onboarding Platform

A comprehensive employee onboarding management system built with Flask, designed to streamline the entire onboarding journey from pre-joining to 90-day probation completion.

## Features

### 📋 Onboarding Checklist (41 Tasks)
- **Pre-Joining (24 tasks):** Joining status, BGV, CTC, documents, agreements
- **Day 1 (8 tasks):** Welcome hamper, laptop setup, email creation, induction
- **Week 1 (9 tasks):** Induction completion, founder meetings, Keka setup, CRM/Clickup IDs

### 📊 30-60-90 Day Plan
- Structured planning with **Expected Goals**, **Status**, and **Manager Comments** per period
- Track **Training & Support Required**, **Manager Recommendation**, and **Next Action Plan**
- Real-time status updates: On Track / Achieved / Needs Improvement / Delayed / Not Started

### 👥 Role-Based Access
- **Admin (HR):** Dashboard, manage joiners, reset tasks, view all plans
- **Manager:** Track team onboarding, evaluate progress, create/edit plans
- **Employee:** View personal onboarding journey and progress

### 📈 Progress Tracking
- Visual progress bars (color-coded by completion %)
- Phase timeline (Pre-Joining → Day 1 → Week 1 → 30/60/90 Days)
- Task completion tracking with owner assignment

### 📝 Manager Evaluations
- 30-day, 60-day, and 90-day performance reviews
- Rating system (1-5 stars)
- Confirmation recommendations (Confirm / Extend / Do Not Confirm)
- Feedback collection (Strengths, Areas for Improvement, Next Goals)

## Tech Stack

- **Backend:** Flask + SQLAlchemy
- **Database:** SQLite (file-based)
- **Frontend:** HTML + CSS (custom styling with blue theme)
- **Authentication:** Session-based with password hashing (PBKDF2-SHA256)

## Database Schema

### Models
- `User` - Admin, Manager, Employee accounts
- `NewJoiner` - Employee being onboarded
- `OnboardingTask` - Individual checklist tasks (41 per joiner)
- `OnboardingPlan` - 30-60-90 day plan with goals/status/comments
- `Evaluation` - 30/60/90-day performance reviews
- `JoinerPlan` - Legacy plan format (goals/KPIs/support)
- `HRNote` - HR notes and comments

## Setup & Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python3 app.py
```

**Default port:** `http://localhost:5050`

## Default Credentials

| User | Email | Password | Role |
|------|-------|----------|------|
| HR Admin | hr@habuild.in | Onboarding@123 | Admin |
| Rumani Zore | rumani.zore@habuild.in | Onboarding@123 | Admin |
| Team Manager 1 | manager1@habuild.in | Onboarding@123 | Manager |

## Sample Joiners

- Priya Sharma (25 days in)
- Rohit Verma (5 days in)
- Sneha Kulkarni (Day 1)

## Key Pages

- `/dashboard` - HR/Admin dashboard with filters and stats
- `/joiner/<id>` - Joiner detail with tasks, evaluations, plans
- `/joiner/<id>/plan` - 30-60-90 day plan editor
- `/evaluate/<id>/<period>` - Performance evaluation form
- `/admin/reset-tasks` - Reset all onboarding tasks

## Recent Changes (April 2026)

✅ **Color Theme:** Changed from green to light blue (#1565C0)
✅ **Checklist:** Replaced 37 generic tasks with 41-item comprehensive checklist
✅ **30-60-90 Plans:** New structured planning system with goals, status, and comments
✅ **OnboardingPlan Model:** Dedicated database table for plan tracking

## Author

Built for Habuild - Employee Onboarding Platform

## License

Internal Use Only
