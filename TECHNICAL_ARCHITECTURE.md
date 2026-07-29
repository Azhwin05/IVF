# Dr. Archana IVF Clinical OS — Technical Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT BROWSER (Desktop)                    │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  React App (Next.js 15)                                    │ │
│  │  - Role-based interface rendering                          │ │
│  │  - State management (Zustand)                              │ │
│  │  - Form handling (React Hook Form + Zod)                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER (Current)                      │
│                                                                   │
│  ✅ React Components                                             │
│  ✅ Tailwind CSS Styling                                         │
│  ✅ Lucide Icons                                                 │
│  ✅ Mock Data Layer                                              │
│  ✅ Role-based routing                                           │
│  ✅ Complete UI/UX for all screens                               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│              BACKEND LAYER (To Be Implemented)                   │
│                                                                   │
│  📋 FastAPI Python Backend                                       │
│  🗄️  PostgreSQL Database                                         │
│  🔐 JWT Authentication                                           │
│  🔒 Role-Based Access Control (RBAC)                             │
│  📊 Audit Logging System                                         │
│  🔗 Third-party Integrations                                     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Components

### 1. Frontend Architecture (Current - Production Ready)

#### Technology Stack
```
Next.js 15
├── React 18.2
├── TypeScript 5.3
├── Tailwind CSS 3.3
├── Lucide React (Icons)
├── React Hook Form (Form handling)
├── Zod (Schema validation)
├── Zustand (State management - ready to use)
└── Recharts (Analytics - ready to use)
```

#### Project Structure
```
dr-archana-ivf-prototype/
├── app/
│   ├── layout.tsx           # Root layout
│   └── page.tsx             # Home page
├── app.tsx                  # Main application component
├── globals.css              # Global styles
├── tailwind.config.ts       # Tailwind configuration
├── tsconfig.json            # TypeScript config
├── package.json             # Dependencies
├── README.md                # Documentation
└── DEPLOYMENT_GUIDE.md      # Deployment instructions
```

#### Component Architecture

**Screen Components:**
- LoginScreen
- DoctorDashboard
- ManagementDashboard
- DoctorPatientWorkspace
- TimelineScreen
- MonitoringScreen
- EmbryologyScreen
- TransferScreen
- PregnancyFollowupScreen
- RegistrationScreen
- BillingScreen

**UI Components:**
- StatusBadge
- MetricCard
- PatientCard
- Timeline

**Layout Components:**
- Sidebar navigation
- Top navigation bar
- Main content area

#### Design System

**Color Palette:**
```
Primary: Emerald (#16a34a)
  - Emerald-600: Active state
  - Emerald-50: Background
  - Emerald-700: Hover state

Neutral: Stone
  - Stone-900: Text
  - Stone-600: Secondary text
  - Stone-50: Light backgrounds
  - Stone-200: Borders

Status Colors:
  - Green: Completed, Active
  - Amber: Warning, Pending
  - Red: Critical (muted)
  - Blue: Scheduled
```

**Typography:**
```
Display: System font weight 700
Body: System font weight 400
Mono: System font family, weight 600
Scale: 12px → 14px → 16px → 18px → 20px → 24px → 32px → 40px → 48px
```

**Spacing:**
```
Base unit: 8px
Scale: 4, 8, 12, 16, 24, 32, 48, 64px
Applied via Tailwind classes
```

#### State Management

**Currently: Mock Data**
```typescript
// Data layer in app.tsx
const MOCK_USERS = {...}
const PRIYA_PATIENT = {...}
const MOCK_APPOINTMENTS = {...}
const IVF_TIMELINE = {...}
// etc.
```

**Ready to integrate: Zustand**
```typescript
// Will replace mock data
const useAppStore = create((set) => ({
  currentUser: null,
  patients: [],
  appointments: [],
  setCurrentUser: (user) => set({ currentUser: user }),
  // etc.
}));
```

---

### 2. Backend Architecture (To Be Built)

#### Technology Stack (Recommended)
```
FastAPI (Python 3.11+)
├── Pydantic models
├── SQLAlchemy ORM
└── Dependency injection

PostgreSQL 15
├── JSONB for flexible data
├── Full-text search
└── Row-level security

Redis
├── Session management
├── Caching
└── Background jobs

Celery
└── Async task processing
```

#### Core Modules

**Authentication Module**
```python
# Authentication service
- JWT token generation
- Role-based access control (RBAC)
- Session management
- Password hashing (bcrypt)
- MFA support (TOTP)
```

**Patient Management Module**
```python
# Patient service
- Patient profile CRUD
- Couple linkage
- Fertility history
- Medical records
- Document management
```

**IVF Cycle Management Module**
```python
# IVF service
- Cycle creation and tracking
- Protocol management
- Timeline management
- Status updates
```

**Monitoring & Lab Module**
```python
# Lab service
- Monitoring records (ultrasound, labs)
- Lab results integration
- Hormone tracking
- Equipment integration APIs
```

**Embryology Module**
```python
# Embryology service
- Oocyte assessment
- Fertilization records
- Embryo grading
- Embryo transfer
- Cryostorage management
- Location tracking
```

**Billing Module**
```python
# Billing service
- Package management
- Invoice generation
- Payment tracking
- Collection reporting
```

**Analytics Module**
```python
# Analytics service
- KPI calculation
- Trend analysis
- Report generation
- Performance metrics
```

#### Database Design

**Core Tables:**
```sql
users
├── id, email, password_hash
├── role (doctor, embryologist, receptionist, admin)
└── permissions JSON

patients
├── id, name, age, blood_group
├── fertility_status, duration
└── contact_info

couples
├── female_patient_id
├── male_partner_id
└── relationship_info

ivf_cycles
├── id, patient_couple_id
├── protocol, start_date, status
└── treatment_notes

monitoring_records
├── id, ivf_cycle_id, record_date
├── follicle_sizes, endometrial_thickness
└── hormone_results JSONB

embryos
├── id, ivf_cycle_id
├── day, grade, status
└── genetic_screening_results

cryostorage
├── id, embryo_id
├── location (tank, canister, cane, goblet, straw)
├── freeze_date, consent_status
└── renewal_date

invoices
├── id, patient_couple_id
├── package_id, amount_paid, outstanding
└── payment_history JSONB

audit_logs
├── id, user_id, action
├── entity_type, entity_id
├── timestamp, changes JSON
└── ip_address
```

#### API Endpoints (RESTful)

```
Authentication:
POST   /auth/login
POST   /auth/logout
POST   /auth/refresh-token

Patients:
GET    /patients
GET    /patients/{id}
POST   /patients
PUT    /patients/{id}
GET    /couples/{id}

IVF Cycles:
GET    /ivf-cycles
GET    /ivf-cycles/{id}
POST   /ivf-cycles
PUT    /ivf-cycles/{id}/status

Monitoring:
GET    /monitoring/{cycle_id}
POST   /monitoring/{cycle_id}
GET    /monitoring/{cycle_id}/history

Embryology:
GET    /embryology/{cycle_id}
POST   /embryos
PUT    /embryos/{id}/transfer
GET    /cryostorage

Billing:
GET    /invoices
GET    /invoices/{id}
POST   /payments
GET    /collections/daily

Analytics:
GET    /analytics/dashboard
GET    /analytics/cycles
GET    /analytics/outcomes
```

---

### 3. Security Architecture

#### Authentication & Authorization
```
Login Flow:
1. User enters credentials
2. Backend validates against password hash
3. JWT token issued (valid 1 hour)
4. Refresh token issued (valid 30 days)
5. Client stores tokens securely (httpOnly cookies)

Role-Based Access Control:
- Doctor: Full clinical access
- Embryologist: Lab and embryo records only
- Receptionist: Patient management, appointments
- Admin: Operations and analytics
- Each role has specific API permissions
```

#### Data Protection
```
At Rest:
- Database encryption (PostgreSQL pgcrypto)
- Encrypted fields for sensitive data
- Regular backups with encryption

In Transit:
- HTTPS/TLS 1.3 only
- Certificate pinning (optional)

Access Patterns:
- Row-level security (PostgreSQL RLS)
- Column-level encryption for PII
- Audit logging for all data access
```

#### Compliance
```
HIPAA:
- Access controls and authentication
- Audit trails and logging
- Encryption of data
- Business associate agreements

Data Privacy:
- GDPR-compliant data handling
- Right to deletion implementation
- Data export functionality
- Privacy policy enforcement
```

---

### 4. Integration Points

#### Third-Party Services
```
SMS/Email:
- Twilio (SMS notifications)
- SendGrid (Email)

Payment Processing:
- Razorpay (Indian payments)
- Stripe (International payments)

Lab Equipment:
- Ultrasound machine APIs
- Lab analyzer integrations
- ERP system connectors

Analytics:
- Metabase (internal BI)
- Segment (event tracking)

Monitoring:
- Sentry (error tracking)
- DataDog (performance monitoring)
```

---

## Development Roadmap

### Phase 1: Core Workflows (Weeks 1-8)
**Deliverables:**
- Backend API infrastructure
- User authentication system
- Patient management database
- IVF cycle tracking
- Monitoring records system
- Basic analytics dashboard

**Timeline:** 8 weeks
**Team Size:** 2-3 developers

**Deliverable:** Functional alpha version with core workflows

---

### Phase 2: Operations & Billing (Weeks 9-16)
**Deliverables:**
- Embryology module completion
- Billing and invoicing system
- Cryostorage management
- Pharmacy module
- Inventory system

**Timeline:** 8 weeks
**Team Size:** 3-4 developers + QA

**Deliverable:** Functional beta version with all operations modules

---

### Phase 3: Advanced Features (Weeks 17-24)
**Deliverables:**
- Advanced analytics and reporting
- Integrations with lab equipment
- SMS/Email automation
- Mobile companion app
- Video conferencing integration
- Comprehensive audit system

**Timeline:** 8 weeks
**Team Size:** 4-5 developers + QA + DevOps

**Deliverable:** Production-ready system with advanced features

---

## Deployment Architecture

### Development Environment
```
Local Development:
- Next.js dev server (port 3000)
- FastAPI dev server (port 8000)
- PostgreSQL local instance
- Redis local instance
```

### Staging Environment
```
AWS EC2/RDS Setup:
- Frontend: Vercel (automatic deployments)
- Backend: AWS ECS (containerized FastAPI)
- Database: AWS RDS PostgreSQL
- Cache: AWS ElastiCache Redis
- Storage: AWS S3 (documents, images)
```

### Production Environment
```
High-Availability Setup:
- Frontend: Vercel (global CDN, auto-scaling)
- Backend: AWS ECS with load balancing
- Database: RDS with multi-AZ failover
- Cache: ElastiCache cluster
- Storage: S3 with encryption
- Monitoring: CloudWatch + Sentry
- Backup: Automated daily backups
```

---

## Performance Targets

```
Load Time:
- Initial page load: <2 seconds
- Dashboard render: <1 second
- Patient record load: <500ms
- Report generation: <5 seconds

Scalability:
- Support 5+ concurrent users per doctor
- Handle 500+ patient records
- Process 100+ monitoring records daily
- Generate reports for 1000+ historical cycles

Uptime:
- 99.9% SLA
- Maximum 30-second downtime for updates
- Automated failover < 5 seconds
```

---

## Monitoring & Maintenance

```
Automated Monitoring:
- Error tracking (Sentry)
- Performance metrics (DataDog)
- Uptime monitoring (StatusPage)
- Database health checks

Maintenance Windows:
- Tuesday 2-4 AM (weekly)
- No clinical operations
- Automatic backups
- Security patches

Support Schedule:
- 24/7 emergency support (downtime)
- 9 AM - 6 PM standard support (features)
- 72-hour response SLA
- Dedicated support engineer
```

---

## Cost Estimates

### Development Costs
```
Phase 1: ₹8-10 lakhs (Core workflows)
Phase 2: ₹8-10 lakhs (Operations)
Phase 3: ₹5-8 lakhs (Advanced features)

Total: ₹21-28 lakhs for complete system
```

### Infrastructure Costs (Monthly)
```
AWS Compute:
- ECS/EC2: ₹15,000
- RDS PostgreSQL: ₹12,000
- ElastiCache Redis: ₹5,000
- S3 Storage: ₹2,000

Third-party Services:
- Vercel (frontend): ₹2,000
- Sentry (monitoring): ₹1,500
- DataDog: ₹3,000
- Twilio (SMS): ₹2,000

Total: ₹42,500/month (~$510 USD)
```

### Team Costs
```
Development Team:
- Tech Lead: ₹1.2-1.5 lakhs/month
- Senior Backend Dev: ₹80k-1 lakh/month
- Senior Frontend Dev: ₹80k-1 lakh/month
- QA Engineer: ₹50-60k/month
- DevOps Engineer: ₹70-80k/month

Option: Build in-house vs. outsource vs. hybrid
```

---

## Next Steps

1. **Immediate (Days 1-3):**
   - Client approves prototype and vision
   - Schedule requirements workshop
   - Define exact workflows and integrations

2. **Short-term (Weeks 1-2):**
   - Complete technical architecture design
   - Database schema finalization
   - API contract definition
   - Team assembly

3. **Medium-term (Weeks 3-4):**
   - Backend infrastructure setup
   - Development begins
   - Continuous integration/deployment setup
   - Regular sprint reviews

4. **Long-term (Months 2-6):**
   - Phased development as per roadmap
   - Testing and QA
   - User acceptance testing
   - Training and deployment

---

## Conclusion

The prototype demonstrates that a comprehensive, purpose-built IVF Clinical Operating System is not only possible—it's practical and achievable. The architecture is modern, scalable, and designed for healthcare workflows from day one.

With clear phases, dedicated team, and realistic timelines, Dr. Archana IVF can have a complete, production-quality system within 6 months.

The question is not whether it can be built.

**The question is: Can you afford to wait?**
