# Claude Code Guidelines for Habuild Onboarding

Instructions for working with this project via Claude Code.

---

## 🚀 IMPORTANT: GitHub Push Triggers Production Deployment

**Every `git push origin main` automatically deploys to Railway production!**

```
git push origin main
    ↓
GitHub notifies Railway
    ↓
Railway pulls code + rebuilds
    ↓
Your live app updates (2-3 minutes)
    ↓
Users see new changes immediately
```

**BE CAREFUL:** Only push when changes are tested and ready for production.

---

## 📋 Before Pushing to GitHub

**Claude MUST:**
1. ✅ Ask user permission before any `git push`
2. ✅ Show the user what will be pushed (files changed, commit message)
3. ✅ Remind user: "This will trigger production deployment to Railway"
4. ✅ Wait for user approval before proceeding

**Example:**

```
Files to be committed:
  - app.py (modified)
  - requirements.txt (modified)

Commit message:
  "Add new feature"

⚠️ This will trigger production deployment!
   Your live app at https://habuild-onboarding-production.up.railway.app will update.

Ready to push? (yes/no)
```

---

## 🔄 Local Development Guidelines

- ✅ Make changes locally
- ✅ Test with `python3 app.py` (uses SQLite locally)
- ✅ Make sure everything works
- ✅ THEN ask permission to push

---

## 🔐 Secret Management

- ✅ `.env` file contains `SECRET_KEY` and `DATABASE_URL`
- ✅ `.env` is in `.gitignore` (never committed)
- ✅ Production values set in Railway environment variables
- ❌ Never commit `.env` file
- ❌ Never commit secrets in code

---

## 📝 Commit Message Format

Commit messages should:
- Be clear and descriptive
- Start with action verb: "Add", "Fix", "Update", "Refactor"
- Explain the "why", not just the "what"

**Good:**
```
Fix database initialization on Railway

Tables now auto-created on first request,
works with both local Flask and Gunicorn
```

**Bad:**
```
stuff
```

---

## 🎯 Files NOT to Modify Without Asking

These are critical for production:
- `Procfile` (how Railway runs the app)
- `requirements.txt` (dependencies)
- `Dockerfile` (container config)
- Environment variable setup in Railway

Ask before modifying these!

---

## 📊 Project Structure

```
habuild-onboarding/
├── app.py                  ← Main Flask app (be careful!)
├── requirements.txt        ← Dependencies (production critical)
├── Procfile               ← Railway startup (don't modify lightly)
├── Dockerfile             ← Container image
├── .env                   ← Local secrets (never commit)
├── .env.example           ← Template (can commit)
├── static/                ← CSS, images
├── templates/             ← HTML pages
├── instance/              ← SQLite (local only)
└── docs/                  ← Guides
```

---

## 🚨 Emergency: Revert Production

If something breaks in production:

```bash
git log --oneline           # See recent commits
git revert <commit-hash>    # Undo the bad commit
git push origin main        # Deploy revert
```

This creates a NEW commit that undoes changes (safer than reset).

---

## ✅ Deployment Checklist

Before pushing:
- [ ] Tested locally with `python3 app.py`
- [ ] Login works
- [ ] Can add joiners
- [ ] 30-60-90 plan works
- [ ] No error messages
- [ ] Ready for users to see

---

## 📞 Questions?

If unsure about something:
1. Ask the user first
2. Don't assume
3. Be transparent about what will happen

---

## Summary

**Golden Rule:** ⚠️ **Ask before push. Explain it triggers production.** ⚠️

Every push = users see changes in 2-3 minutes. Act accordingly!
