# Workflow Docs

Documents the configurable clinical/operational workflows referenced in `IMPLEMENTATION_PLAN.md` Phase 3 (Workflow Engine) — the actual step definitions (role required, checklist, associated charge, allowed next steps) for each hospital process:

- Front desk patient status flow (`Registered → Arrived → Waiting → Consultation → ... → Completed`)
- Billing lock / payment-required gate and authorized-override rules
- IVF clinical workflow (Consultation → Stimulation → Retrieval → Embryology → Transfer → Pregnancy)
- Pharmacy dispensing (prescription validation → stock → deduction → billing)
- Purchasing (Request → Approval → PO → GRN → Stock Entry → Payment)
- OT/procedure scheduling and checklist flow
- Daily departmental readiness checklists

To be written module-by-module starting in Phase 3, using the workflow shapes already implied by the existing frontend (`Transfer.tsx`'s 6-point checklist, `Plan.tsx`'s stage tracker, `Registration.tsx`'s 5-step wizard) as the starting reference, not a blank slate.
