# Local Lift Frontend

**Next.js 14+ Application** - Production-ready web interface for Local Lift platform.

---

## 🏗️ Architecture

- **Framework:** Next.js 14+ (App Router)
- **Language:** TypeScript (strict mode)
- **Styling:** Tailwind CSS
- **Data Fetching:** TanStack Query (React Query)
- **API Client:** Type-safe axios wrapper
- **Charts:** Recharts

---

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── admin/              # Admin dashboard pages
│   │   ├── contractor/         # Contractor portal pages
│   │   ├── layout.tsx          # Root layout
│   │   └── page.tsx            # Home (redirects to admin)
│   ├── components/
│   │   ├── admin/              # Admin-specific components
│   │   ├── contractor/        # Contractor-specific components
│   │   └── shared/             # Shared components
│   └── lib/
│       ├── api-client.ts       # Type-safe API client (ALL Phases 1-5)
│       └── utils.ts             # Utility functions
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ installed
- Backend API running on `http://localhost:8000`

### Installation
```bash
cd frontend
npm install
```

### Development
```bash
npm run dev
```

Visit `http://localhost:3000`

### Build
```bash
npm run build
npm start
```

---

## 🔌 API Integration

All backend APIs (Phases 1-5) are integrated via `src/lib/api-client.ts`:

- ✅ Scoring API (Phase 2)
- ✅ Leads API (Phase 3)
- ✅ Contractors API (Phase 3)
- ✅ Dashboard API (Phase 3)
- ✅ Delivery API (Phase 4)
- ✅ Feedback API (Phase 5)
- ✅ Calibration API (Phase 5)

---

## 📊 Features

### Admin Dashboard
- System overview & metrics
- Lead management
- Contractor management
- Territory management
- Analytics & reporting
- Model refinement controls

### Contractor Portal
- Lead dashboard
- Lead management
- Feedback submission
- Performance tracking
- Territory view

---

## 🎯 Design Principles

1. **Optimization First** - Performance over aesthetics
2. **Clarity** - Clear, readable code
3. **Efficiency** - Minimal re-renders, optimized queries
4. **Type Safety** - Full TypeScript coverage
5. **Error Handling** - Graceful error boundaries

---

## ✅ Production Ready

- Type-safe API integration
- Error boundaries
- Loading states
- Responsive design
- Optimized performance
- Clean code structure

---

**Status:** ✅ **Ready for Production Use**

