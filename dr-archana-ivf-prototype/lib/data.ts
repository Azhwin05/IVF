// ============================================================
// CLINICAL DATA LAYER
// Mirrors the shape of the future REST API so screens can be
// re-pointed at live endpoints without refactoring.
// ============================================================

export type Role = 'doctor' | 'receptionist' | 'embryologist' | 'management';

export type StatusTone =
  | 'active'
  | 'completed'
  | 'pending'
  | 'attention'
  | 'critical'
  | 'scheduled'
  | 'cancelled'
  | 'neutral';

export interface StaffUser {
  id: string;
  role: Role;
  name: string;
  title: string;
  initials: string;
  email: string;
  department: string;
  accent: string;
}

export const USERS: Record<Role, StaffUser> = {
  doctor: {
    id: 'DAIVF-STAFF-001',
    role: 'doctor',
    name: 'Dr. Archana S. Ayyanathan',
    title: 'Chief Consultant & IVF Specialist',
    initials: 'AA',
    email: 'archana@drarchanaivf.in',
    department: 'Reproductive Medicine',
    accent: 'from-emerald-500 to-teal-600',
  },
  receptionist: {
    id: 'DAIVF-STAFF-014',
    role: 'receptionist',
    name: 'Lakshmi Narayanan',
    title: 'Front Office Executive',
    initials: 'LN',
    email: 'lakshmi@drarchanaivf.in',
    department: 'Patient Services',
    accent: 'from-sky-500 to-blue-600',
  },
  embryologist: {
    id: 'DAIVF-STAFF-007',
    role: 'embryologist',
    name: 'Dr. Meera Kapoor',
    title: 'Senior Clinical Embryologist',
    initials: 'MK',
    email: 'meera@drarchanaivf.in',
    department: 'Embryology Laboratory',
    accent: 'from-violet-500 to-purple-600',
  },
  management: {
    id: 'DAIVF-STAFF-002',
    role: 'management',
    name: 'Rajesh Venkatesan',
    title: 'Hospital Administrator',
    initials: 'RV',
    email: 'rajesh@drarchanaivf.in',
    department: 'Operations & Finance',
    accent: 'from-amber-500 to-orange-600',
  },
};

// ------------------------------------------------------------
// PRIMARY DEMO COUPLE
// ------------------------------------------------------------

export const PATIENT = {
  id: 'DAIVF-2026-00428',
  name: 'Priya Raman',
  initials: 'PR',
  age: 31,
  dob: '18 September 1994',
  bloodGroup: 'B Positive',
  phone: '+91 98407 21894',
  email: 'priya.raman@gmail.com',
  address: 'T-4, Anandam Apartments, Alwarpet, Chennai 600018',
  occupation: 'Architect',
  emergencyContact: 'Arjun Kumar (Spouse) — +91 98410 33127',
  referralSource: 'Referred by Dr. Sudha Menon, Apollo Chennai',
  allergies: 'No known drug allergies',
  infertilityType: 'Primary Infertility',
  duration: '6 Years',
  previousIUI: 2,
  previousIVF: 0,
  amh: '2.4 ng/mL',
  afc: '14 (7 right / 7 left)',
  bmi: '23.4',
  protocol: 'GnRH Antagonist Protocol',
  treatment: 'IVF with ICSI',
  cycleId: 'IVF-2026-00428',
  cycleDay: 8,
  phase: 'Ovarian Stimulation',
  registeredOn: '2 July 2026',
  consultant: 'Dr. Archana S. Ayyanathan',
};

export const PARTNER = {
  id: 'DAIVF-2026-00429',
  name: 'Arjun Kumar',
  initials: 'AK',
  age: 34,
  dob: '22 May 1992',
  bloodGroup: 'O Positive',
  phone: '+91 98410 33127',
  email: 'arjun.kumar@gmail.com',
  occupation: 'Senior Software Engineer',
  relationship: 'Married — 6 Years',
  semenAnalysis: {
    volume: '3.2 mL',
    concentration: '18 million/mL',
    motility: '38% progressive',
    morphology: '3% normal forms',
    verdict: 'Mild oligoasthenoteratozoospermia — ICSI advised',
  },
};

// ------------------------------------------------------------
// PATIENT REGISTRY
// ------------------------------------------------------------

export interface PatientRow {
  id: string;
  name: string;
  initials: string;
  age: number;
  partner: string;
  stage: string;
  tone: StatusTone;
  cycleDay: string;
  consultant: string;
  lastVisit: string;
  amh: string;
}

export const PATIENTS: PatientRow[] = [
  {
    id: 'DAIVF-2026-00428',
    name: 'Priya Raman',
    initials: 'PR',
    age: 31,
    partner: 'Arjun Kumar',
    stage: 'Ovarian Stimulation',
    tone: 'active',
    cycleDay: 'Day 8',
    consultant: 'Dr. Archana',
    lastVisit: 'Today, 9:30 AM',
    amh: '2.4',
  },
  {
    id: 'DAIVF-2026-00391',
    name: 'Nandhini Selvaraj',
    initials: 'NS',
    age: 29,
    partner: 'Rahul Menon',
    stage: 'Embryo Transfer',
    tone: 'scheduled',
    cycleDay: 'Transfer Day',
    consultant: 'Dr. Archana',
    lastVisit: 'Today, 11:30 AM',
    amh: '3.1',
  },
  {
    id: 'DAIVF-2026-00364',
    name: 'Kavitha Ramesh',
    initials: 'KR',
    age: 34,
    partner: 'Ramesh Iyer',
    stage: 'Fertility Assessment',
    tone: 'pending',
    cycleDay: '—',
    consultant: 'Dr. Archana',
    lastVisit: 'Today, 10:00 AM',
    amh: '1.8',
  },
  {
    id: 'DAIVF-2026-00312',
    name: 'Meera Sundaram',
    initials: 'MS',
    age: 32,
    partner: 'Vignesh Kumar',
    stage: 'Pregnancy Follow-up',
    tone: 'completed',
    cycleDay: '7 Weeks',
    consultant: 'Dr. Archana',
    lastVisit: 'Today, 2:00 PM',
    amh: '2.9',
  },
  {
    id: 'DAIVF-2026-00298',
    name: 'Divya Prakash',
    initials: 'DP',
    age: 36,
    partner: 'Prakash Nair',
    stage: 'Embryology',
    tone: 'active',
    cycleDay: 'Day 3 Culture',
    consultant: 'Dr. Archana',
    lastVisit: '28 July 2026',
    amh: '1.2',
  },
  {
    id: 'DAIVF-2026-00276',
    name: 'Anitha Balaji',
    initials: 'AB',
    age: 28,
    partner: 'Balaji Srinivasan',
    stage: 'Oocyte Retrieval',
    tone: 'scheduled',
    cycleDay: 'Trigger Given',
    consultant: 'Dr. Archana',
    lastVisit: '28 July 2026',
    amh: '4.2',
  },
  {
    id: 'DAIVF-2026-00241',
    name: 'Shalini Venkat',
    initials: 'SV',
    age: 38,
    partner: 'Venkat Raman',
    stage: 'Ovarian Stimulation',
    tone: 'attention',
    cycleDay: 'Day 10',
    consultant: 'Dr. Archana',
    lastVisit: '29 July 2026',
    amh: '0.9',
  },
  {
    id: 'DAIVF-2026-00205',
    name: 'Revathi Krishnan',
    initials: 'RK',
    age: 30,
    partner: 'Krishnan Iyer',
    stage: 'Cryo Transfer Planning',
    tone: 'pending',
    cycleDay: '—',
    consultant: 'Dr. Archana',
    lastVisit: '26 July 2026',
    amh: '2.6',
  },
];

// ------------------------------------------------------------
// TODAY'S SCHEDULE
// ------------------------------------------------------------

export interface Appointment {
  id: string;
  time: string;
  patient: string;
  patientId?: string;
  initials: string;
  visit: string;
  status: string;
  tone: StatusTone;
  room: string;
}

export const APPOINTMENTS: Appointment[] = [
  {
    id: 'APT-2026-1841',
    time: '09:30',
    patient: 'Priya Raman & Arjun Kumar',
    patientId: 'DAIVF-2026-00428',
    initials: 'PR',
    visit: 'Follicle Monitoring — Day 8',
    status: 'Waiting',
    tone: 'attention',
    room: 'Scan Room 2',
  },
  {
    id: 'APT-2026-1842',
    time: '10:00',
    patient: 'Kavitha Ramesh',
    patientId: 'DAIVF-2026-00364',
    initials: 'KR',
    visit: 'IVF Consultation',
    status: 'Confirmed',
    tone: 'scheduled',
    room: 'Consult 1',
  },
  {
    id: 'APT-2026-1843',
    time: '10:45',
    patient: 'Shalini Venkat',
    patientId: 'DAIVF-2026-00241',
    initials: 'SV',
    visit: 'Monitoring — Poor Responder Review',
    status: 'In Progress',
    tone: 'active',
    room: 'Scan Room 1',
  },
  {
    id: 'APT-2026-1844',
    time: '11:30',
    patient: 'Nandhini Selvaraj & Rahul Menon',
    patientId: 'DAIVF-2026-00391',
    initials: 'NS',
    visit: 'Embryo Transfer',
    status: 'Scheduled',
    tone: 'scheduled',
    room: 'OT — Transfer Suite',
  },
  {
    id: 'APT-2026-1845',
    time: '14:00',
    patient: 'Meera Sundaram',
    patientId: 'DAIVF-2026-00312',
    initials: 'MS',
    visit: 'Pregnancy Follow-up — 7 Weeks',
    status: 'Confirmed',
    tone: 'scheduled',
    room: 'Consult 1',
  },
  {
    id: 'APT-2026-1846',
    time: '15:30',
    patient: 'Anitha Balaji',
    patientId: 'DAIVF-2026-00276',
    initials: 'AB',
    visit: 'Pre-Retrieval Counselling',
    status: 'Confirmed',
    tone: 'scheduled',
    room: 'Consult 2',
  },
];

// ------------------------------------------------------------
// DASHBOARD METRICS
// ------------------------------------------------------------

export const METRICS = {
  appointments: { value: 24, label: 'Appointments Today', delta: '+3 vs yesterday', trend: [16, 19, 17, 22, 20, 24, 24] },
  waiting: { value: 7, label: 'Patients Waiting', delta: 'Avg wait 12 min', trend: [3, 5, 4, 6, 8, 7, 7] },
  cycles: { value: 12, label: 'Active IVF Cycles', delta: '+2 this week', trend: [8, 9, 9, 10, 11, 12, 12] },
  collection: { value: 184000, label: "Today's Collection", delta: '+18% vs avg', trend: [120, 142, 131, 158, 166, 172, 184] },
  procedures: { value: 3, label: 'Procedures Scheduled', delta: '1 retrieval, 2 transfers', trend: [2, 3, 1, 4, 2, 3, 3] },
  followups: { value: 8, label: 'Follow-ups Due', delta: '3 pregnancy reviews', trend: [5, 6, 7, 6, 9, 8, 8] },
};

export const CLINICAL_ALERTS = [
  {
    id: 'AL-1',
    title: 'Monitoring reports awaiting review',
    detail: 'Priya Raman (Day 8) and Shalini Venkat (Day 10) require doctor sign-off.',
    count: 2,
    tone: 'attention' as StatusTone,
    action: 'Review Now',
  },
  {
    id: 'AL-2',
    title: 'Trigger timing confirmation required',
    detail: 'Anitha Balaji — lead follicle 19 mm, trigger decision due today.',
    count: 1,
    tone: 'critical' as StatusTone,
    action: 'Confirm Trigger',
  },
  {
    id: 'AL-3',
    title: 'Pregnancy follow-ups due today',
    detail: 'Meera Sundaram, Deepa Rajan and Sowmya Iyer scheduled for beta-hCG review.',
    count: 3,
    tone: 'scheduled' as StatusTone,
    action: 'Open List',
  },
  {
    id: 'AL-4',
    title: 'Cryostorage renewals approaching',
    detail: '2 storage consents expire within 30 days — patient consent renewal required.',
    count: 2,
    tone: 'pending' as StatusTone,
    action: 'View Storage',
  },
];

export const ACTIVITY_FEED = [
  { id: 'A1', actor: 'Dr. Meera Kapoor', action: "uploaded Day 8 monitoring for Priya Raman", time: '12 minutes ago', kind: 'lab' },
  { id: 'A2', actor: 'Embryology Lab', action: 'moved Embryo E-02 to cryostorage Tank A / Canister 04', time: '38 minutes ago', kind: 'embryo' },
  { id: 'A3', actor: 'Lakshmi Narayanan', action: "recorded ₹75,000 package payment from Kavitha Ramesh", time: '1 hour ago', kind: 'billing' },
  { id: 'A4', actor: 'Dr. Archana', action: 'finalised treatment plan for Anitha Balaji', time: '2 hours ago', kind: 'clinical' },
  { id: 'A5', actor: 'Lakshmi Narayanan', action: 'registered new couple — Revathi & Krishnan', time: '3 hours ago', kind: 'registration' },
  { id: 'A6', actor: 'Dr. Archana', action: 'updated Gonal-F dosage for Shalini Venkat', time: '4 hours ago', kind: 'clinical' },
];

// Active cycle distribution across pipeline stages
export const CYCLE_DISTRIBUTION = [
  { stage: 'Assessment', count: 3, color: '#94A3B8' },
  { stage: 'Stimulation', count: 4, color: '#10B981' },
  { stage: 'Retrieval', count: 1, color: '#F59E0B' },
  { stage: 'Embryology', count: 2, color: '#8B5CF6' },
  { stage: 'Transfer', count: 1, color: '#0EA5E9' },
  { stage: 'Follow-up', count: 1, color: '#EC4899' },
];

// ------------------------------------------------------------
// IVF JOURNEY TIMELINE
// ------------------------------------------------------------

export interface TimelineStage {
  id: string;
  title: string;
  date: string;
  status: 'completed' | 'active' | 'upcoming';
  summary: string;
  details: { label: string; value: string }[];
  link?: string;
}

export const TIMELINE: TimelineStage[] = [
  {
    id: 'ts-1',
    title: 'Initial Consultation',
    date: '4 July 2026',
    status: 'completed',
    summary: 'Comprehensive fertility assessment completed for both partners.',
    details: [
      { label: 'Consultant', value: 'Dr. Archana S. Ayyanathan' },
      { label: 'Diagnosis', value: 'Primary infertility — 6 years' },
      { label: 'History', value: '2 previous IUI cycles, both unsuccessful' },
      { label: 'Outcome', value: 'Advised IVF with ICSI' },
    ],
  },
  {
    id: 'ts-2',
    title: 'Diagnostic Investigations',
    date: '6 – 10 July 2026',
    status: 'completed',
    summary: 'Baseline hormonal profile, pelvic ultrasound and semen analysis completed.',
    details: [
      { label: 'AMH', value: '2.4 ng/mL — normal ovarian reserve' },
      { label: 'Antral Follicle Count', value: '14 (7 right / 7 left)' },
      { label: 'Semen Analysis', value: 'Mild OAT — ICSI indicated' },
      { label: 'Hysteroscopy', value: 'Normal uterine cavity' },
    ],
    link: 'investigations',
  },
  {
    id: 'ts-3',
    title: 'Treatment Plan Finalised',
    date: '12 July 2026',
    status: 'completed',
    summary: 'GnRH antagonist protocol selected. Consent and package activated.',
    details: [
      { label: 'Protocol', value: 'GnRH Antagonist' },
      { label: 'Stimulation', value: 'Gonal-F 225 IU daily' },
      { label: 'Package', value: 'Complete IVF Treatment — ₹2,50,000' },
      { label: 'Consent', value: 'Signed and verified' },
    ],
    link: 'plan',
  },
  {
    id: 'ts-4',
    title: 'Ovarian Stimulation',
    date: 'Started 22 July 2026 — Currently Day 8',
    status: 'active',
    summary: 'Follicular response progressing appropriately. Monitoring every 48 hours.',
    details: [
      { label: 'Current Day', value: 'Stimulation Day 8' },
      { label: 'Lead Follicle', value: '17 mm (right ovary)' },
      { label: 'Endometrium', value: '8.2 mm — trilaminar' },
      { label: 'Next Review', value: '30 July 2026' },
    ],
    link: 'monitoring',
  },
  {
    id: 'ts-5',
    title: 'Trigger Injection',
    date: 'Planned — 31 July 2026',
    status: 'upcoming',
    summary: 'hCG trigger once lead follicles reach 18–20 mm.',
    details: [
      { label: 'Planned Agent', value: 'Ovitrelle 250 mcg' },
      { label: 'Timing', value: '35 hours before retrieval' },
      { label: 'Criteria', value: '≥3 follicles at 17 mm+' },
    ],
  },
  {
    id: 'ts-6',
    title: 'Oocyte Retrieval',
    date: 'Expected — 2 August 2026',
    status: 'upcoming',
    summary: 'Transvaginal ultrasound-guided oocyte aspiration under sedation.',
    details: [
      { label: 'Procedure', value: 'TVOR under short GA' },
      { label: 'Expected Yield', value: '12 – 16 oocytes' },
      { label: 'Anaesthetist', value: 'Dr. Sanjay Rao' },
    ],
  },
  {
    id: 'ts-7',
    title: 'Embryology & Culture',
    date: 'Expected — 2 – 7 August 2026',
    status: 'upcoming',
    summary: 'ICSI fertilisation followed by extended blastocyst culture to Day 5.',
    details: [
      { label: 'Method', value: 'ICSI' },
      { label: 'Culture', value: 'Continuous time-lapse to Day 5' },
      { label: 'Embryologist', value: 'Dr. Meera Kapoor' },
    ],
    link: 'embryology',
  },
  {
    id: 'ts-8',
    title: 'Embryo Transfer',
    date: 'Expected — 7 August 2026',
    status: 'upcoming',
    summary: 'Single blastocyst transfer under ultrasound guidance.',
    details: [
      { label: 'Plan', value: 'Elective single embryo transfer' },
      { label: 'Support', value: 'Luteal phase progesterone' },
    ],
    link: 'transfer',
  },
  {
    id: 'ts-9',
    title: 'Pregnancy Follow-up',
    date: 'From 21 August 2026',
    status: 'upcoming',
    summary: 'Beta-hCG at Day 14, followed by serial ultrasound milestones.',
    details: [
      { label: 'First Test', value: 'Beta-hCG — Day 14 post transfer' },
      { label: 'First Scan', value: '6 weeks gestation' },
    ],
    link: 'pregnancy',
  },
];

// ------------------------------------------------------------
// STIMULATION MONITORING
// ------------------------------------------------------------

export interface MonitoringVisit {
  day: number;
  date: string;
  right: number[];
  left: number[];
  endometrium: number;
  estradiol: number;
  lh: number;
  progesterone: number;
  note: string;
  reviewed: boolean;
}

export const MONITORING_HISTORY: MonitoringVisit[] = [
  {
    day: 2,
    date: '23 July 2026',
    right: [6, 5, 5, 4],
    left: [6, 5, 4, 4],
    endometrium: 4.1,
    estradiol: 186,
    lh: 3.1,
    progesterone: 0.3,
    note: 'Baseline scan satisfactory. No residual cysts. Commence Gonal-F 225 IU.',
    reviewed: true,
  },
  {
    day: 5,
    date: '26 July 2026',
    right: [11, 10, 9, 8],
    left: [10, 9, 8, 7],
    endometrium: 6.4,
    estradiol: 642,
    lh: 4.2,
    progesterone: 0.5,
    note: 'Even cohort recruitment. Continue current dosage. Add Cetrotide from Day 6.',
    reviewed: true,
  },
  {
    day: 8,
    date: '29 July 2026',
    right: [17, 15, 14, 12],
    left: [16, 15, 13, 11],
    endometrium: 8.2,
    estradiol: 1420,
    lh: 4.8,
    progesterone: 0.7,
    note: 'Follicular response is progressing appropriately. Continue the current dosage and repeat monitoring tomorrow.',
    reviewed: false,
  },
];

export const MEDICATIONS = [
  { name: 'Gonal-F', dose: '225 IU', route: 'Subcutaneous — daily', status: 'Active', since: 'Day 1', tone: 'active' as StatusTone },
  { name: 'Cetrotide', dose: '0.25 mg', route: 'Subcutaneous — daily', status: 'Active', since: 'Day 6', tone: 'active' as StatusTone },
  { name: 'Folic Acid', dose: '5 mg', route: 'Oral — daily', status: 'Ongoing', since: 'Pre-cycle', tone: 'completed' as StatusTone },
  { name: 'Ovitrelle', dose: '250 mcg', route: 'Subcutaneous — single', status: 'Planned', since: 'Day 10', tone: 'pending' as StatusTone },
];

export const HORMONE_REFERENCE = [
  { key: 'estradiol', label: 'Estradiol (E2)', unit: 'pg/mL', value: 1420, range: '1,000 – 2,000', status: 'Optimal', tone: 'completed' as StatusTone },
  { key: 'lh', label: 'Luteinising Hormone', unit: 'mIU/mL', value: 4.8, range: '< 10', status: 'Suppressed', tone: 'completed' as StatusTone },
  { key: 'progesterone', label: 'Progesterone', unit: 'ng/mL', value: 0.7, range: '< 1.5', status: 'Normal', tone: 'completed' as StatusTone },
];

// ------------------------------------------------------------
// EMBRYOLOGY
// ------------------------------------------------------------

export const EMBRYO_SUMMARY = [
  { label: 'Oocytes Retrieved', value: 14, sub: 'TVOR — 2 Aug 2026' },
  { label: 'Mature Oocytes', value: 11, sub: 'MII stage' },
  { label: 'Normally Fertilised', value: 8, sub: '2PN — 73% rate' },
  { label: 'Day 3 Embryos', value: 7, sub: 'Cleavage stage' },
  { label: 'Blastocysts', value: 5, sub: 'Day 5 / Day 6' },
];

export interface Embryo {
  id: string;
  day: number;
  grade: string;
  expansion: string;
  icm: string;
  trophectoderm: string;
  status: string;
  tone: StatusTone;
  note: string;
  storage?: string;
  frozen?: string;
  score: number;
}

export const EMBRYOS: Embryo[] = [
  {
    id: 'E-01',
    day: 5,
    grade: '4AA',
    expansion: 'Expanded blastocyst',
    icm: 'A — tightly packed, many cells',
    trophectoderm: 'A — cohesive epithelium',
    status: 'Selected for Transfer',
    tone: 'active',
    note: 'Top quality blastocyst. Even expansion, no fragmentation. Recommended for fresh transfer.',
    score: 96,
  },
  {
    id: 'E-02',
    day: 5,
    grade: '4AB',
    expansion: 'Expanded blastocyst',
    icm: 'A — prominent inner cell mass',
    trophectoderm: 'B — few larger cells',
    status: 'Cryopreserved',
    tone: 'completed',
    note: 'Excellent morphology. Vitrified on Day 5 for future frozen transfer.',
    storage: 'Tank A / Canister 04 / Cane 02 / Goblet 05 / Straw 03',
    frozen: '4 August 2026',
    score: 88,
  },
  {
    id: 'E-03',
    day: 6,
    grade: '3BB',
    expansion: 'Full blastocyst',
    icm: 'B — loosely grouped cells',
    trophectoderm: 'B — moderate cell number',
    status: 'Cryopreserved',
    tone: 'completed',
    note: 'Good quality Day 6 blastocyst. Delayed expansion but viable.',
    storage: 'Tank A / Canister 04 / Cane 02 / Goblet 05 / Straw 04',
    frozen: '5 August 2026',
    score: 74,
  },
  {
    id: 'E-04',
    day: 5,
    grade: '3BC',
    expansion: 'Full blastocyst',
    icm: 'B — moderate quality',
    trophectoderm: 'C — sparse, irregular cells',
    status: 'Under Clinical Review',
    tone: 'attention',
    note: 'Fair quality. Trophectoderm grading borderline. Awaiting embryologist and clinician joint review.',
    score: 58,
  },
  {
    id: 'E-05',
    day: 6,
    grade: '3CC',
    expansion: 'Full blastocyst',
    icm: 'C — few cells',
    trophectoderm: 'C — sparse cells',
    status: 'Not Suitable for Transfer',
    tone: 'cancelled',
    note: 'Poor morphology on Day 6. Discussed with couple — not recommended for cryopreservation.',
    score: 31,
  },
];

export const CRYO_HIERARCHY = {
  tank: 'Tank A',
  canister: 'Canister 04',
  cane: 'Cane 02',
  goblet: 'Goblet 05',
  straws: [
    { id: 'Straw 03', embryo: 'E-02', grade: '4AB', frozen: '4 Aug 2026', status: 'Active' },
    { id: 'Straw 04', embryo: 'E-03', grade: '3BB', frozen: '5 Aug 2026', status: 'Active' },
  ],
  temperature: '-196 °C',
  consent: 'Verified — signed 3 Aug 2026',
  renewal: '4 August 2027',
  custody: [
    { at: '4 Aug 2026, 11:42', by: 'Dr. Meera Kapoor', event: 'Vitrification completed — E-02 loaded to Straw 03' },
    { at: '4 Aug 2026, 11:58', by: 'Dr. Meera Kapoor', event: 'Straw transferred to Tank A / Canister 04 / Cane 02' },
    { at: '4 Aug 2026, 12:05', by: 'Anand Kumar (Lab Tech)', event: 'Witness verification completed — double signature recorded' },
    { at: '5 Aug 2026, 10:20', by: 'Dr. Meera Kapoor', event: 'E-03 vitrified and stored in Straw 04' },
    { at: '5 Aug 2026, 18:00', by: 'System', event: 'Automated tank temperature log — -196 °C, nominal' },
  ],
};

export const TRANSFER_CHECKLIST = [
  { id: 'c1', label: 'Patient identity verified', detail: 'Priya Raman — DAIVF-2026-00428 — verified against photo ID and wristband' },
  { id: 'c2', label: 'Couple information verified', detail: 'Arjun Kumar — DAIVF-2026-00429 — partner consent on file' },
  { id: 'c3', label: 'Embryo identity verified', detail: 'E-01 — Day 5 — Grade 4AA — dish label double-witnessed' },
  { id: 'c4', label: 'Consent confirmed', detail: 'Embryo transfer consent signed 6 Aug 2026 by both partners' },
  { id: 'c5', label: 'Clinical team verified', detail: 'Dr. Archana S. Ayyanathan (Clinician), Dr. Meera Kapoor (Embryologist)' },
  { id: 'c6', label: 'Procedure documentation completed', detail: 'Catheter batch, media lot and witness signatures recorded' },
];

// ------------------------------------------------------------
// PREGNANCY
// ------------------------------------------------------------

export const BETA_HCG = [
  { day: 'Day 14', value: 612, verdict: 'Positive', tone: 'completed' as StatusTone },
  { day: 'Day 16', value: 1248, verdict: 'Appropriate rise', tone: 'completed' as StatusTone },
  { day: 'Day 21', value: 5840, verdict: 'Strong progression', tone: 'completed' as StatusTone },
];

export const PREGNANCY_MILESTONES = [
  { label: 'Embryo Transfer', date: '7 Aug 2026', status: 'completed' as const, detail: 'Single blastocyst E-01 transferred' },
  { label: 'Positive Beta-hCG', date: '21 Aug 2026', status: 'completed' as const, detail: '612 mIU/mL — biochemical pregnancy confirmed' },
  { label: 'Gestational Sac', date: '4 Sep 2026', status: 'completed' as const, detail: '6 weeks — single intrauterine sac visualised' },
  { label: 'Cardiac Activity', date: '11 Sep 2026', status: 'completed' as const, detail: '7 weeks — fetal heart rate 128 bpm' },
  { label: 'First Trimester Scan', date: '9 Oct 2026', status: 'upcoming' as const, detail: '11–13 weeks NT scan scheduled' },
  { label: 'Delivery Outcome', date: 'May 2027', status: 'upcoming' as const, detail: 'Estimated due date 15 May 2027' },
];

// ------------------------------------------------------------
// BILLING
// ------------------------------------------------------------

export const PACKAGE = {
  name: 'Complete IVF Treatment Package',
  value: 250000,
  paid: 175000,
  outstanding: 75000,
  inclusions: [
    { item: 'Consultations (unlimited)', status: 'Included' },
    { item: 'Stimulation monitoring scans', status: 'Included' },
    { item: 'Oocyte retrieval & anaesthesia', status: 'Included' },
    { item: 'ICSI & embryology laboratory', status: 'Included' },
    { item: 'Embryo transfer procedure', status: 'Included' },
    { item: 'Stimulation medicines', status: 'Excluded' },
    { item: 'Additional investigations', status: 'Excluded' },
    { item: 'Cryostorage (per year)', status: 'Additional' },
  ],
};

export const INVOICES = [
  { id: 'INV-2026-0912', date: '12 July 2026', description: 'IVF Package — Advance (40%)', amount: 100000, method: 'Bank Transfer', status: 'Paid' },
  { id: 'INV-2026-1043', date: '22 July 2026', description: 'IVF Package — Second instalment (30%)', amount: 75000, method: 'UPI — HDFC', status: 'Paid' },
  { id: 'INV-2026-1188', date: '2 August 2026', description: 'IVF Package — Final instalment (30%)', amount: 75000, method: '—', status: 'Due' },
  { id: 'INV-2026-1201', date: '4 August 2026', description: 'Cryostorage — 1 year (2 straws)', amount: 18000, method: '—', status: 'Due' },
];

// ------------------------------------------------------------
// MANAGEMENT ANALYTICS
// ------------------------------------------------------------

export const REVENUE_TREND = [
  { month: 'Feb', revenue: 38.2, cycles: 14 },
  { month: 'Mar', revenue: 42.6, cycles: 17 },
  { month: 'Apr', revenue: 39.8, cycles: 15 },
  { month: 'May', revenue: 47.1, cycles: 19 },
  { month: 'Jun', revenue: 52.4, cycles: 22 },
  { month: 'Jul', revenue: 58.9, cycles: 26 },
];

export const MANAGEMENT_KPIS = [
  { label: 'New Patients This Month', value: 38, delta: '+22%', positive: true },
  { label: 'Active IVF Cycles', value: 12, delta: '+2', positive: true },
  { label: 'Embryo Transfers', value: 19, delta: '+4', positive: true },
  { label: 'Clinical Pregnancy Rate', value: 62, suffix: '%', delta: '+5 pts', positive: true },
];

export const OUTCOME_BREAKDOWN = [
  { label: 'Clinical Pregnancy', value: 62, color: '#10B981' },
  { label: 'Biochemical Only', value: 11, color: '#F59E0B' },
  { label: 'Not Pregnant', value: 27, color: '#D6D3D1' },
];

export const OPERATIONAL_METRICS = [
  { label: 'Monthly Revenue', value: '₹58.9 L', delta: '+12.4%', positive: true },
  { label: 'Daily Collection', value: '₹1.84 L', delta: '+18%', positive: true },
  { label: 'Outstanding Payments', value: '₹9.2 L', delta: '-6.1%', positive: true },
  { label: 'Appointment Volume', value: '486', delta: '+9%', positive: true },
  { label: 'Pharmacy Sales', value: '₹7.4 L', delta: '+3.2%', positive: true },
  { label: 'Inventory Alerts', value: '4', delta: '2 critical', positive: false },
];

export const DOCTOR_PERFORMANCE = [
  { name: 'Dr. Archana S. Ayyanathan', consultations: 186, cycles: 24, transfers: 12, success: 66 },
  { name: 'Dr. Kavya Raghunathan', consultations: 142, cycles: 15, transfers: 8, success: 61 },
  { name: 'Dr. Suresh Ramachandran', consultations: 118, cycles: 11, transfers: 6, success: 58 },
];

// ------------------------------------------------------------
// ROLE PERMISSIONS
// ------------------------------------------------------------

export const ROLE_MATRIX: Record<Role, { allowed: string[]; restricted: string[]; summary: string }> = {
  doctor: {
    summary: 'Full clinical authority across patient care, treatment planning and cycle management.',
    allowed: ['Complete Patient Profile', 'Clinical Notes', 'Treatment Plans', 'IVF Cycle Management', 'Follicle Monitoring', 'Prescriptions', 'Embryology Review', 'Procedure Sign-off'],
    restricted: ['Accounting Configuration', 'Payroll & Staff Salary'],
  },
  receptionist: {
    summary: 'Front-office operations — registration, scheduling, queue and basic billing.',
    allowed: ['Patient Registration', 'Appointment Scheduling', 'Queue Management', 'Basic Billing & Receipts', 'Document Upload'],
    restricted: ['Embryology Details', 'Detailed Clinical Notes', 'Management Reports', 'Treatment Plans'],
  },
  embryologist: {
    summary: 'Laboratory workspace covering oocytes, embryo development, grading and cryostorage.',
    allowed: ['IVF Cycle Information', 'Oocyte Assessment', 'Embryo Development & Grading', 'Cryostorage Management', 'Chain of Custody', 'Lab Witness Sign-off'],
    restricted: ['Financial Reports', 'Accounting', 'Patient Billing', 'Staff Administration'],
  },
  management: {
    summary: 'Operational and financial oversight with configurable clinical visibility.',
    allowed: ['Hospital Dashboard', 'Operational Reports', 'Revenue & Collections', 'Clinical Performance Metrics', 'Inventory Insights', 'Audit Logs'],
    restricted: ['Individual Clinical Notes', 'Embryo-level Laboratory Data'],
  },
};

// ------------------------------------------------------------
// AUDIT LOG
// ------------------------------------------------------------

export const AUDIT_LOG = [
  { id: 'AU-8841', user: 'Dr. Archana S. Ayyanathan', action: 'Medication updated', entity: 'IVF-2026-00428 — Gonal-F 225 IU', time: '29 Jul 2026, 09:48', ip: '10.0.4.22', tone: 'active' as StatusTone },
  { id: 'AU-8840', user: 'Dr. Meera Kapoor', action: 'Monitoring record created', entity: 'IVF-2026-00428 — Day 8 scan', time: '29 Jul 2026, 09:31', ip: '10.0.4.18', tone: 'completed' as StatusTone },
  { id: 'AU-8839', user: 'Lakshmi Narayanan', action: 'Payment recorded', entity: 'INV-2026-1043 — ₹75,000', time: '29 Jul 2026, 08:55', ip: '10.0.4.09', tone: 'completed' as StatusTone },
  { id: 'AU-8838', user: 'Dr. Meera Kapoor', action: 'Cryostorage transfer', entity: 'E-02 → Tank A / Canister 04', time: '28 Jul 2026, 17:12', ip: '10.0.4.18', tone: 'scheduled' as StatusTone },
  { id: 'AU-8837', user: 'Rajesh Venkatesan', action: 'Report exported', entity: 'July operational summary', time: '28 Jul 2026, 16:40', ip: '10.0.4.31', tone: 'neutral' as StatusTone },
  { id: 'AU-8836', user: 'System', action: 'Failed login attempt blocked', entity: 'Unknown device — Chennai', time: '28 Jul 2026, 02:14', ip: '49.37.x.x', tone: 'critical' as StatusTone },
];

export const NOTIFICATIONS = [
  { id: 'N1', title: 'Day 8 monitoring awaiting your review', body: 'Priya Raman — uploaded 12 minutes ago by Dr. Meera Kapoor.', time: '12m', unread: true, tone: 'attention' as StatusTone },
  { id: 'N2', title: 'Trigger decision required', body: 'Anitha Balaji — lead follicle 19 mm. Confirm trigger timing today.', time: '45m', unread: true, tone: 'critical' as StatusTone },
  { id: 'N3', title: 'Embryo E-02 cryopreserved', body: 'Vitrification complete. Witness verification recorded.', time: '2h', unread: true, tone: 'completed' as StatusTone },
  { id: 'N4', title: 'Package payment received', body: 'Kavitha Ramesh — ₹75,000 via UPI.', time: '3h', unread: false, tone: 'completed' as StatusTone },
  { id: 'N5', title: 'Cryostorage consent expiring', body: '2 storage consents expire within 30 days.', time: '1d', unread: false, tone: 'pending' as StatusTone },
];

export const INVESTIGATIONS = [
  { name: 'Anti-Müllerian Hormone (AMH)', value: '2.4 ng/mL', ref: '1.0 – 4.0', date: '6 Jul 2026', flag: 'normal' as const },
  { name: 'Follicle Stimulating Hormone', value: '6.8 mIU/mL', ref: '3.5 – 12.5', date: '6 Jul 2026', flag: 'normal' as const },
  { name: 'Thyroid Stimulating Hormone', value: '2.1 µIU/mL', ref: '0.4 – 4.0', date: '6 Jul 2026', flag: 'normal' as const },
  { name: 'Prolactin', value: '18.4 ng/mL', ref: '4.8 – 23.3', date: '6 Jul 2026', flag: 'normal' as const },
  { name: 'Vitamin D (25-OH)', value: '18 ng/mL', ref: '30 – 100', date: '6 Jul 2026', flag: 'low' as const },
  { name: 'Antral Follicle Count', value: '14', ref: '10 – 20', date: '8 Jul 2026', flag: 'normal' as const },
  { name: 'Semen Analysis (Partner)', value: '18 M/mL, 38% motile', ref: '≥16 M/mL, ≥30%', date: '9 Jul 2026', flag: 'low' as const },
  { name: 'Hysteroscopy', value: 'Normal cavity', ref: 'Normal', date: '10 Jul 2026', flag: 'normal' as const },
];

export const CONSULTATIONS = [
  { date: '4 Jul 2026', type: 'Initial Fertility Consultation', doctor: 'Dr. Archana', note: 'Couple with 6 years primary infertility. Two failed IUI cycles. Advised complete workup and likely IVF-ICSI.' },
  { date: '12 Jul 2026', type: 'Treatment Planning', doctor: 'Dr. Archana', note: 'Reviewed investigations. AMH 2.4, AFC 14. Partner sample shows mild OAT. Plan: antagonist protocol with ICSI. Counselled on success rates and risks.' },
  { date: '22 Jul 2026', type: 'Cycle Initiation', doctor: 'Dr. Archana', note: 'Baseline scan clear. Commenced Gonal-F 225 IU. Injection technique demonstrated. Review Day 5.' },
  { date: '26 Jul 2026', type: 'Monitoring Review — Day 5', doctor: 'Dr. Archana', note: 'Good even cohort. E2 rising appropriately. Continue dose, start Cetrotide Day 6.' },
];
