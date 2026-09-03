"""
Default roles and the granular permission taxonomy, per enterprise
spec §6. Run via `python -m app.roles.seed` or automatically on first
container start (see backend/scripts/seed_db.py).

Role set matches the spec's 10 roles. The existing frontend prototype's
4 demo roles (doctor, receptionist, embryologist, management) map onto
this richer set — `management` maps to `admin`+`it_admin` combined
visibility for the prototype's demo purposes; production deployments
should split these into distinct accounts.
"""
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.roles.models import Permission, Role

# ---------------------------------------------------------------------------
# Permission taxonomy — module.action strings, per spec §6 examples plus the
# full module list this backend implements.
# ---------------------------------------------------------------------------
PERMISSIONS: list[tuple[str, str, str, bool]] = [
    # (code, module, description, is_critical)
    # Patients
    ("patients.read", "patients", "View patient records", False),
    ("patients.create", "patients", "Register new patients/couples", False),
    ("patients.update", "patients", "Edit patient demographic/medical data", False),
    ("patients.merge", "patients", "Merge duplicate patient records", True),
    ("patients.sensitive_documents", "patients", "View/download Aadhaar, visa and other identity documents", True),
    # Appointments
    ("appointments.read", "appointments", "View appointment book", False),
    ("appointments.create", "appointments", "Book appointments", False),
    ("appointments.checkin", "appointments", "Check in a patient", False),
    ("appointments.cancel", "appointments", "Cancel an appointment", False),
    # Clinical
    ("clinical.read", "clinical", "View consultations and clinical notes", False),
    ("clinical.write", "clinical", "Create/edit clinical notes", False),
    ("clinical.correct", "clinical", "Issue a correction to a signed clinical record", True),
    # IVF
    ("ivf.read", "ivf", "View IVF cycle and treatment plan data", False),
    ("ivf.write", "ivf", "Create/edit IVF cycles and treatment plans", False),
    ("ivf.monitoring.write", "ivf", "Record stimulation monitoring visits", False),
    ("ivf.protocol.read", "ivf", "View the restricted treatment protocol", True),
    ("ivf.protocol.write", "ivf", "Write the restricted treatment protocol", True),
    # Embryology
    ("embryology.read", "embryology", "View embryology records", False),
    ("embryology.write", "embryology", "Grade and record embryo development", False),
    ("embryology.transfer", "embryology", "Perform/confirm embryo transfer", True),
    # Cryostorage
    ("cryostorage.read", "cryostorage", "View cryostorage inventory", False),
    ("cryostorage.move", "cryostorage", "Move stored embryos between locations", True),
    # Laboratory
    ("laboratory.read", "laboratory", "View lab orders and results", False),
    ("laboratory.order", "laboratory", "Order lab tests", False),
    ("laboratory.result", "laboratory", "Enter/verify lab results", False),
    # OT
    ("ot.read", "ot", "View OT schedule", False),
    ("ot.schedule", "ot", "Schedule OT procedures", False),
    ("ot.checklist", "ot", "Complete OT readiness checklists", False),
    # Pharmacy
    ("pharmacy.read", "pharmacy", "View pharmacy stock and sales", False),
    ("pharmacy.dispense", "pharmacy", "Dispense medicine to a patient", True),
    ("pharmacy.return", "pharmacy", "Process a pharmacy return", True),
    # Inventory
    ("inventory.read", "inventory", "View inventory levels", False),
    ("inventory.adjust", "inventory", "Adjust inventory stock counts", True),
    ("inventory.write_off", "inventory", "Write off damaged/expired stock", True),
    # Purchasing
    ("purchasing.read", "purchasing", "View purchase requests/orders", False),
    ("purchasing.request", "purchasing", "Submit a purchase request", False),
    ("purchasing.approve", "purchasing", "Approve a purchase order", True),
    ("purchasing.receive", "purchasing", "Record goods receipt (GRN)", False),
    # Billing
    ("billing.read", "billing", "View invoices and payment status", False),
    ("billing.create", "billing", "Create charges and invoices", False),
    ("billing.payment", "billing", "Record a payment", False),
    ("billing.refund", "billing", "Issue a refund", True),
    ("billing.override", "billing", "Override the billing lock (emergency)", True),
    ("billing.discount", "billing", "Apply a discount to an invoice", True),
    # Accounting
    ("accounting.read", "accounting", "View ledger, cash book, GST reports", False),
    ("accounting.write", "accounting", "Post accounting entries", True),
    # Assets
    ("assets.read", "assets", "View asset register", False),
    ("assets.move", "assets", "Record an asset movement", False),
    ("assets.delete", "assets", "Retire/delete an asset record", True),
    # Maintenance
    ("maintenance.read", "maintenance", "View maintenance schedule", False),
    ("maintenance.complete", "maintenance", "Mark maintenance task complete", False),
    # Quality
    ("quality.read", "quality", "View QA/QC checklists", False),
    ("quality.complete", "quality", "Complete a QA/QC task", False),
    # HR
    ("hr.read", "hr", "View employee directory", False),
    ("hr.write", "hr", "Edit employee records", True),
    ("hr.approve_leave", "hr", "Approve/reject leave requests", False),
    # Reports
    ("reports.read", "reports", "View operational/clinical reports", False),
    ("reports.export", "reports", "Export reports", False),
    # Audit
    ("audit.read", "audit", "View the audit log", True),
    # Donor management — new module, source doc §22-23
    ("donor.read", "donor", "View donor records and matching history", False),
    ("donor.write", "donor", "Register donors and record benchmarks", False),
    ("donor.match", "donor", "Match/unmatch a donor to a patient", True),
    # Admin
    ("admin.manage_users", "admin", "Create/edit/deactivate user accounts", True),
    ("admin.manage_roles", "admin", "Edit role/permission assignments", True),
    ("admin.manage_settings", "admin", "Edit master settings (charges, packages, tests)", True),
]

# ---------------------------------------------------------------------------
# Default roles and the permission codes each one gets out of the box.
# ---------------------------------------------------------------------------
ROLE_DEFAULTS: dict[str, tuple[str, list[str]]] = {
    "doctor": ("Doctor", [
        "patients.read", "patients.create", "patients.update", "patients.sensitive_documents",
        "appointments.read", "appointments.create", "appointments.checkin", "appointments.cancel",
        "clinical.read", "clinical.write", "clinical.correct",
        "ivf.read", "ivf.write", "ivf.monitoring.write",
        "embryology.read", "embryology.transfer",
        "cryostorage.read",
        "laboratory.read", "laboratory.order",
        "ot.read", "ot.schedule",
        "pharmacy.read",
        "billing.read", "billing.override", "donor.read",
        "reports.read", "audit.read",
    ]),
    "nurse": ("Nurse", [
        "patients.read", "appointments.read", "appointments.checkin",
        "clinical.read", "clinical.write",
        "ivf.read", "ivf.monitoring.write",
        "ot.read", "ot.checklist",
        "pharmacy.read",
    ]),
    "receptionist": ("Receptionist", [
        "patients.read", "patients.create", "patients.sensitive_documents",
        "appointments.read", "appointments.create", "appointments.checkin", "appointments.cancel",
        "billing.read", "billing.create", "billing.payment",
    ]),
    "embryologist": ("Embryologist", [
        "patients.read",
        "ivf.read",
        "embryology.read", "embryology.write", "embryology.transfer",
        "cryostorage.read", "cryostorage.move",
        "laboratory.read", "laboratory.result",
        "inventory.read",
        "donor.read", "donor.write", "donor.match",
    ]),
    "lab_technician": ("Lab Technician", [
        "patients.read",
        "laboratory.read", "laboratory.order", "laboratory.result",
        "quality.read", "quality.complete",
    ]),
    "pharmacist": ("Pharmacist", [
        "patients.read",
        "pharmacy.read", "pharmacy.dispense", "pharmacy.return",
        "inventory.read",
        "purchasing.read", "purchasing.request", "purchasing.receive",
    ]),
    "accountant": ("Accountant", [
        "billing.read", "billing.create", "billing.payment", "billing.refund",
        "accounting.read", "accounting.write",
        "reports.read", "reports.export",
    ]),
    "management": ("Management", [
        "patients.read", "appointments.read",
        "billing.read", "accounting.read",
        "inventory.read", "purchasing.read", "purchasing.approve",
        "hr.read", "hr.approve_leave",
        "reports.read", "reports.export",
        "audit.read",
        "maintenance.read", "quality.read", "assets.read",
    ]),
    "chief_consultant": ("Chief Consultant", [
        # Everything a doctor has, plus the restricted treatment protocol.
        # New requirement (source doc §7/§33): "Protocol = Akshana Ma'am +
        # Admin only." RBAC in this system is role-based, not per-user, so
        # this role exists specifically to be assigned to that one
        # individual (and any future chief consultant) without widening
        # what the general "doctor" role can see — do not add
        # ivf.protocol.* to the doctor role.
        "patients.read", "patients.create", "patients.update", "patients.sensitive_documents",
        "appointments.read", "appointments.create", "appointments.checkin", "appointments.cancel",
        "clinical.read", "clinical.write", "clinical.correct",
        "ivf.read", "ivf.write", "ivf.monitoring.write", "ivf.protocol.read", "ivf.protocol.write",
        "embryology.read", "embryology.transfer",
        "cryostorage.read",
        "laboratory.read", "laboratory.order",
        "ot.read", "ot.schedule",
        "pharmacy.read",
        "billing.read", "billing.override", "donor.read",
        "reports.read", "audit.read",
    ]),
    "administrator": ("Administrator", ["*"]),  # gets every permission below
    "it_administrator": ("IT Administrator", [
        "admin.manage_users", "admin.manage_roles", "admin.manage_settings",
        "audit.read", "reports.read",
    ]),
}


async def seed_roles_and_permissions(session: AsyncSession) -> None:
    existing = (await session.execute(select(Permission.code))).scalars().all()
    existing_codes = set(existing)

    perms_by_code: dict[str, Permission] = {}
    for code, module, desc, critical in PERMISSIONS:
        if code in existing_codes:
            continue
        perm = Permission(code=code, module=module, description=desc, is_critical=critical)
        session.add(perm)
        perms_by_code[code] = perm
    await session.flush()

    # reload full set (existing + just-created) so role assignment can reference any of them
    all_perms = {p.code: p for p in (await session.execute(select(Permission))).scalars().all()}

    existing_roles = {r.code for r in (await session.execute(select(Role))).scalars().all()}

    for role_code, (name, perm_codes) in ROLE_DEFAULTS.items():
        if role_code in existing_roles:
            if perm_codes == ["*"]:
                # A "*" role (administrator) must always hold every current
                # permission, including ones added to PERMISSIONS after this
                # role was first seeded — re-sync it every run rather than
                # silently drifting out of date whenever a new permission
                # (like ivf.protocol.*) is introduced.
                result = await session.execute(select(Role).where(Role.code == role_code))
                role = result.scalar_one()
                role.permissions = list(all_perms.values())
                session.add(role)
            continue
        role = Role(code=role_code, name=name, is_system_role=True)
        if perm_codes == ["*"]:
            role.permissions = list(all_perms.values())
        else:
            role.permissions = [all_perms[c] for c in perm_codes if c in all_perms]
        session.add(role)

    await session.flush()


async def main() -> None:
    async with AsyncSessionLocal() as session:
        await seed_roles_and_permissions(session)
        await session.commit()
    print(f"Seeded {len(PERMISSIONS)} permissions and {len(ROLE_DEFAULTS)} roles.")


if __name__ == "__main__":
    asyncio.run(main())
