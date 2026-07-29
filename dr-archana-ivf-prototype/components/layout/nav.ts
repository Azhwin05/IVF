import type { ScreenId } from '@/lib/store';
import type { Role } from '@/lib/data';
import {
  LayoutDashboard,
  Users,
  UserPlus,
  CalendarClock,
  GitBranch,
  Activity,
  ClipboardList,
  Microscope,
  Snowflake,
  Baby,
  HeartPulse,
  FlaskConical,
  Pill,
  Boxes,
  Receipt,
  Wallet,
  Users2,
  BarChart3,
  ShieldCheck,
  ScrollText,
  Settings,
} from 'lucide-react';

export interface NavItem {
  id: ScreenId;
  label: string;
  icon: any;
  section: string;
  roles: Role[];
  badge?: number;
}

export const NAV: NavItem[] = [
  // ---------------- CLINICAL ----------------
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, section: 'Clinical', roles: ['doctor', 'management'] },
  { id: 'patients', label: 'Patients', icon: Users, section: 'Clinical', roles: ['doctor', 'receptionist', 'management'] },
  { id: 'registration', label: 'Register Couple', icon: UserPlus, section: 'Clinical', roles: ['doctor', 'receptionist'] },
  { id: 'appointments', label: 'Appointments', icon: CalendarClock, section: 'Clinical', roles: ['doctor', 'receptionist', 'management'] },
  { id: 'timeline', label: 'Clinical Timeline', icon: GitBranch, section: 'Clinical', roles: ['doctor', 'embryologist'] },
  { id: 'monitoring', label: 'Stimulation & Monitoring', icon: Activity, section: 'Clinical', roles: ['doctor', 'embryologist'], badge: 2 },
  { id: 'plan', label: 'Treatment Plan', icon: ClipboardList, section: 'Clinical', roles: ['doctor'] },

  // ---------------- LABORATORY ----------------
  { id: 'embryology', label: 'Embryology', icon: Microscope, section: 'Laboratory', roles: ['doctor', 'embryologist'] },
  { id: 'cryostorage', label: 'Cryostorage', icon: Snowflake, section: 'Laboratory', roles: ['doctor', 'embryologist'] },
  { id: 'transfer', label: 'Embryo Transfer', icon: Baby, section: 'Laboratory', roles: ['doctor', 'embryologist'] },
  { id: 'pregnancy', label: 'Pregnancy Follow-up', icon: HeartPulse, section: 'Laboratory', roles: ['doctor'] },
  { id: 'laboratory', label: 'Laboratory', icon: FlaskConical, section: 'Laboratory', roles: ['doctor', 'embryologist', 'management'] },

  // ---------------- OPERATIONS ----------------
  { id: 'pharmacy', label: 'Pharmacy', icon: Pill, section: 'Operations', roles: ['receptionist', 'management', 'doctor'] },
  { id: 'inventory', label: 'Inventory', icon: Boxes, section: 'Operations', roles: ['embryologist', 'management'] },
  { id: 'billing', label: 'Billing & Packages', icon: Receipt, section: 'Operations', roles: ['doctor', 'receptionist', 'management'] },
  { id: 'accounting', label: 'Accounting', icon: Wallet, section: 'Operations', roles: ['management'] },
  { id: 'staff', label: 'Staff Management', icon: Users2, section: 'Operations', roles: ['management'] },

  // ---------------- MANAGEMENT ----------------
  { id: 'reports', label: 'Reports & Analytics', icon: BarChart3, section: 'Management', roles: ['management', 'doctor'] },
  { id: 'access', label: 'Role & Access', icon: ShieldCheck, section: 'Management', roles: ['doctor', 'receptionist', 'embryologist', 'management'] },
  { id: 'audit', label: 'Audit Log', icon: ScrollText, section: 'Management', roles: ['doctor', 'management'] },
  { id: 'administration', label: 'Administration', icon: Settings, section: 'Management', roles: ['management'] },
];

export const SECTIONS = ['Clinical', 'Laboratory', 'Operations', 'Management'];

export function navForRole(role: Role) {
  return NAV.filter((n) => n.roles.includes(role));
}

export function canAccess(role: Role, screen: ScreenId) {
  // Patient workspace is reachable by any role that can see the patient list
  if (screen === 'workspace') return ['doctor', 'receptionist', 'management'].includes(role);
  const item = NAV.find((n) => n.id === screen);
  return item ? item.roles.includes(role) : false;
}

export const SCREEN_TITLES: Record<ScreenId, string> = {
  dashboard: 'Clinical Dashboard',
  patients: 'Patient Registry',
  registration: 'Patient & Couple Registration',
  workspace: 'Patient Workspace',
  appointments: 'Appointment Management',
  timeline: 'Clinical Timeline',
  monitoring: 'Stimulation & Follicle Monitoring',
  plan: 'IVF Treatment Plan',
  embryology: 'Embryology Workspace',
  cryostorage: 'Cryostorage Management',
  transfer: 'Embryo Transfer',
  pregnancy: 'Pregnancy Follow-up',
  laboratory: 'Laboratory Management',
  pharmacy: 'Pharmacy Management',
  inventory: 'Inventory Management',
  billing: 'Billing & IVF Packages',
  accounting: 'Accounting',
  staff: 'Staff Management',
  reports: 'Reports & Analytics',
  access: 'Role-Based Access Control',
  audit: 'Audit Log',
  administration: 'System Administration',
};
