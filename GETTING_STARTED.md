# Getting Started - Local Lift

**Quick start guide to access and run the Local Lift platform.**

---

## 🚀 Prerequisites

1. **Python 3.12+** installed
2. **Node.js 18+** installed
3. **Docker** installed (for PostgreSQL and Redis)
4. **PostgreSQL 16+** (via Docker or local installation)

---

## 📋 Step-by-Step Setup

### Step 1: Start Database Services

```bash
cd /Users/colinsmith/local-lift
docker-compose up -d
```

This starts:
- PostgreSQL on port `5433`
- Redis on port `6379`

**Verify services are running:**
```bash
docker-compose ps
```

---

### Step 2: Set Up Backend

```bash
cd /Users/colinsmith/local-lift/backend

# Activate virtual environment (if you have one)
source ../.venv/bin/activate  # or: python -m venv .venv && source .venv/bin/activate

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Set environment variables (create .env file if needed)
# DATABASE_URL=postgresql+asyncpg://locallift:locallift_dev@localhost:5433/locallift
# REDIS_URL=redis://localhost:6379/0
```

**Start the backend server:**
```bash
# From backend directory
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend will be available at:** `http://localhost:8000`

**API Documentation:** `http://localhost:8000/docs`

---

### Step 3: Set Up Frontend

**Open a new terminal window:**

```bash
cd /Users/colinsmith/local-lift/frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Frontend will be available at:** `http://localhost:3000`

---

### Step 4: Access the Application

#### **Admin Dashboard**
Open your browser and navigate to:
```
http://localhost:3000/admin
```

**Available pages:**
- Dashboard: `http://localhost:3000/admin`
- Leads: `http://localhost:3000/admin/leads`
- Contractors: `http://localhost:3000/admin/contractors`
- Analytics: `http://localhost:3000/admin/analytics`
- Model Refinement: `http://localhost:3000/admin/model`
- Scoring: `http://localhost:3000/admin/scoring`
- Territories: `http://localhost:3000/admin/territories`
- Data Ingestion: `http://localhost:3000/admin/ingestion`

#### **Contractor Portal**
```
http://localhost:3000/contractor
```

**Available pages:**
- Dashboard: `http://localhost:3000/contractor`
- Leads: `http://localhost:3000/contractor/leads`
- Performance: `http://localhost:3000/contractor/performance`
- Territories: `http://localhost:3000/contractor/territories`

---

## 🔧 Quick Commands Reference

### Backend
```bash
# Start backend
cd backend
uvicorn src.main:app --reload

# Run property ingestion (if needed)
python -m src.ingestion.property_universe

# Run tests
pytest
```

### Frontend
```bash
# Start frontend
cd frontend
npm run dev

# Build for production
npm run build
npm start

# Type check
npm run type-check
```

### Database
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f
```

---

## 🌐 API Endpoints

**Backend API Base URL:** `http://localhost:8000/api/v1`

**Key endpoints:**
- `GET /api/v1/dashboard/stats` - Dashboard statistics
- `GET /api/v1/leads` - List leads
- `GET /api/v1/contractors` - List contractors
- `GET /api/v1/scoring/high-intent` - High intent properties
- `POST /api/v1/feedback/lead/{id}` - Submit feedback
- `GET /api/v1/calibration/adjustments` - Calibration data

**Full API docs:** `http://localhost:8000/docs`

---

## ⚠️ Troubleshooting

### Backend won't start
1. Check if PostgreSQL is running: `docker-compose ps`
2. Verify database connection in `.env`
3. Check port 8000 is not in use: `lsof -i :8000`

### Frontend won't start
1. Check if Node.js is installed: `node --version`
2. Install dependencies: `npm install`
3. Check port 3000 is not in use: `lsof -i :3000`

### Database connection errors
1. Verify Docker services: `docker-compose ps`
2. Check database credentials in `.env`
3. Restart services: `docker-compose restart`

### API errors in frontend
1. Verify backend is running on port 8000
2. Check browser console for CORS errors
3. Verify `NEXT_PUBLIC_API_URL` in frontend (defaults to `http://localhost:8000`)

---

## 📝 First-Time Setup Checklist

- [ ] Docker installed and running
- [ ] `docker-compose up -d` executed
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Backend server running (`uvicorn src.main:app --reload`)
- [ ] Frontend server running (`npm run dev`)
- [ ] Can access `http://localhost:3000/admin`

---

## 🎯 Next Steps

1. **Populate Database:**
   ```bash
   cd backend
   python -m src.ingestion.property_universe
   ```

2. **Create a Contractor:**
   - Navigate to `/admin/contractors`
   - Click "Add Contractor"
   - Fill in details

3. **Generate Leads:**
   - Navigate to `/admin/scoring`
   - View high-intent properties
   - Generate leads from scoring page

4. **View Analytics:**
   - Navigate to `/admin/analytics`
   - View score accuracy and feature importance

---

**You're all set!** 🎉

The system is now accessible and ready to use.

