# Full-Stack Quiz Application

A secure, full-stack quiz web application with an integrated online code compiler (Python, Java, C) and proctoring features.

## 🚀 Deployment Overview

This project is structured for easy deployment using a "Manual" or "Blueprint" approach.

### **Architecture**
- **Backend**: Django + Django Rest Framework (DRF)
- **Frontend**: React + Vite
- **Database**: PostgreSQL (Supabase/Render)
- **Code Execution**: Integrated compiler requiring OpenJDK 21 (installed via `build.sh`)

---

## 🛠️ Backend Deployment (Render)

### **Manual Setup**
1. **Create Web Service**:
   - **Root Directory**: `backend-modified`
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `bash -c "source $HOME/.profile && gunicorn quiz_backend.wsgi:application"`

2. **Environment Variables**:
   - `DATABASE_URL`: Your PostgreSQL connection string.
   - `DJANGO_SECRET_KEY`: A secure random string.
   - `DJANGO_SETTINGS_MODULE`: `quiz_backend.settings`
   - `PYTHON_VERSION`: `3.12.0`
   - `DEBUG`: `False`
   - `FRONTEND_URL`: Your Vercel frontend URL (e.g., `https://your-app.vercel.app`).

---

## 💻 Frontend Deployment (Vercel)

### **Manual Setup**
1. **Import Project**: Connect your GitHub repo.
2. **Framework Preset**: `Vite`
3. **Root Directory**: `frontend-modified`
4. **Environment Variables**:
   - `VITE_API_URL`: Your Render backend URL (e.g., `https://quiz-backend.onrender.com`).

---

## 🔒 Security & Proctoring Features
- **Fullscreen Lock**: The quiz requires fullscreen mode to proceed.
- **Tab/Window Detection**: Monitors tab switching and window blur with warning counts.
- **Copy/Paste Prevention**: Disables copying and right-clicking during the exam.
- **Sanitized Output**: Code execution errors are sanitized to prevent server path leakage.

---

## 📂 Project Structure
- `backend-modified/`: Django backend source.
  - `build.sh`: Build script for Render (Installs OpenJDK 21).
  - `Procfile`: Render/Heroku process file.
- `frontend-modified/`: React frontend source.
  - `src/config.js`: Dynamic API URL configuration.
- `render.yaml`: Blueprint configuration for Render.
- `docker-compose.yml`: Local development configuration.

---

## ✅ Post-Deployment Checklist
- [ ] Backend health check: `https://<backend>.onrender.com/api/questions/` returns JSON.
- [ ] Admin panel: `https://<backend>.onrender.com/admin/` loads successfully.
- [ ] Frontend: `https://<frontend>.vercel.app/` loads the Welcome page.
- [ ] Quiz: Questions load and submission works without CORS errors.
- [ ] Compiler: Python, Java, and C code execution works in the integrated editor.
