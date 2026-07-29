# Dr. Archana IVF Clinical Operating System

**Premium integrated desktop web application for IVF Hospital Management**

## Overview

A high-fidelity, fully-interactive prototype of a comprehensive Clinical Operating System for Dr. Archana IVF & Women Centre, featuring:

- ✅ **14 fully-functional screens** with complete IVF patient journey
- ✅ **Role-based access** for Doctor, Receptionist, Embryologist, Management
- ✅ **Premium design** with emerald/gold aesthetic
- ✅ **Realistic demo data** throughout the system
- ✅ **Production-grade UI** using modern React stack
- ✅ **Complete interactivity** across all clinical workflows

## Screens Included

### Authentication
1. **Secure Staff Login** — Role-based access control

### Clinical Workflows
2. **Executive Clinical Dashboard** — Real-time metrics and schedule
3. **Doctor Patient Workspace** — Complete patient profile and clinical summary
4. **IVF Patient Timeline** — Visual journey from consultation to outcome
5. **Ovarian Stimulation & Follicle Monitoring** — Real-time monitoring workspace
6. **Embryology Workspace** — Embryo tracking and grading
7. **Embryo Transfer Procedure** — Pre-transfer checklist and confirmation
8. **Pregnancy Follow-up** — Outcome tracking with hCG and ultrasound

### Hospital Operations
9. **Patient Registration** — Couple registration with fertility history
10. **Billing & IVF Packages** — Package management and payment tracking
11. **Management Dashboard** — Analytics and performance metrics

### Supporting Features
- Sidebar navigation with role-aware menu
- Global patient search
- Notifications and user profile
- Security and audit indicators
- Status badges and clinical indicators

## Technology Stack

- **Framework**: Next.js 15
- **Language**: TypeScript
- **UI**: React with Tailwind CSS
- **Icons**: Lucide React
- **Charts**: Recharts (ready to integrate)
- **Form Handling**: React Hook Form + Zod
- **State Management**: Zustand (ready to integrate)
- **Database**: Mock data layer (replace with real backend)

## Getting Started

### Prerequisites
- Node.js 18+ and npm/yarn

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

The application will be available at `http://localhost:3000`

### Demo Credentials

Login as different roles to see role-based experiences:

- **👩‍⚕️ Dr. Archana** — Full clinical access
- **👩‍💼 Receptionist** — Patient management access
- **👨‍🔬 Embryologist** — Lab and embryo access
- **👨‍💼 Management** — Hospital analytics access

## Project Structure

```
dr-archana-ivf/
├── app.tsx                 # Main application component
├── app/
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── globals.css            # Global styles
├── tailwind.config.ts     # Tailwind configuration
├── tsconfig.json          # TypeScript config
└── package.json           # Dependencies
```

## Key Features

### Design System
- **Colors**: Emerald (#16a34a) + Stone (neutral palette)
- **Typography**: System fonts with clear hierarchy
- **Components**: Reusable cards, badges, timelines, metrics
- **Spacing**: Consistent 8px grid system
- **Shadows**: Subtle, premium aesthetic

### Data Layer
All demo data is organized in a clean mock data layer:
- Patient profiles (Priya Raman & Arjun Kumar)
- Appointment schedule
- IVF cycle timeline
- Monitoring results
- Embryology records
- Billing information

Replace mock data with backend API calls as needed.

### Role-Based Access

The system includes role-aware experiences for:
- **Doctor**: Complete clinical access, monitoring, treatment planning
- **Receptionist**: Patient registration, appointments, queue management
- **Embryologist**: IVF cycle details, embryo grading, cryostorage
- **Management**: Analytics, revenue, operational metrics

## Customization

### Adding New Screens

1. Create a new component function
2. Add to the `currentScreen` state switch
3. Add navigation button in sidebar or another screen
4. Style using Tailwind classes

### Integrating Real Data

1. Replace mock data in the data layer (top of `app.tsx`)
2. Create API service layer
3. Use React hooks to fetch data
4. Update component props

### Styling Changes

Modify `tailwind.config.ts` for:
- Color palette changes
- Font adjustments
- Spacing modifications
- Custom animations

## Deployment

### Vercel (Recommended)

```bash
# Push to GitHub and connect to Vercel
# Automatic deployments on push to main
```

### Docker

```bash
# Build and run in Docker container
docker build -t dr-archana-ivf .
docker run -p 3000:3000 dr-archana-ivf
```

### Traditional Hosting

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Performance Optimizations

- Image optimization
- Code splitting by route
- Tailwind CSS purging
- Next.js dynamic imports
- Caching strategies

## Security Considerations

- Session management (implement JWT)
- HIPAA compliance requirements
- Data encryption in transit
- Role-based access control
- Audit logging
- CORS configuration

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (responsive design included)

## Future Enhancements

- [ ] Real backend API integration
- [ ] Database connectivity (PostgreSQL)
- [ ] User authentication system
- [ ] Real-time notifications
- [ ] Video consultations
- [ ] Document management
- [ ] Advanced analytics
- [ ] Mobile app version
- [ ] Telemedicine features
- [ ] Integration with lab equipment

## Support & Documentation

For detailed workflow documentation, refer to the context prompt included with this project.

## License

Proprietary — Dr. Archana IVF & Women Centre

---

**Built with precision for premium IVF clinical care.**
