'use client';

import React, { useMemo, useRef, useState } from 'react';
import {
  FileText,
  Upload,
  ScanLine,
  RefreshCw,
  Pencil,
  History,
  Plus,
  ExternalLink,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';

import { Badge, Button, Card, CardHeader, InfoNote, Input, Modal, Select } from '@/components/ui/primitives';
import { useApp } from '@/lib/store';
import { ApiError } from '@/lib/api/client';
import { usePatients } from '@/lib/api/patients';
import {
  fetchLabReportDocument,
  useAddLabReportResult,
  useCorrectLabReportResult,
  useLabReport,
  useLabReportResultCorrections,
  useLabReports,
  useRunLabReportExtraction,
  useUploadLabReport,
  type LabExtractionMethod,
  type LabExtractionStatus,
  type LabReportResult,
  type LabResultValidationStatus,
} from '@/lib/api/laboratory';

const STATUS_TONE: Record<LabExtractionStatus, 'pending' | 'active' | 'completed' | 'critical'> = {
  pending: 'pending',
  processing: 'active',
  completed: 'completed',
  failed: 'critical',
};
const STATUS_LABEL: Record<LabExtractionStatus, string> = {
  pending: 'Not yet extracted',
  processing: 'Extracting…',
  completed: 'Extraction complete',
  failed: 'Extraction failed',
};
const METHOD_LABEL: Record<LabExtractionMethod, string> = {
  native_pdf_text: 'Digital PDF text',
  ocr: 'OCR (scanned)',
  ai_vision: 'AI vision',
  manual: 'Manual entry',
  none: '—',
};
const VALIDATION_TONE: Record<LabResultValidationStatus, 'completed' | 'attention' | 'critical'> = {
  ok: 'completed',
  needs_review: 'attention',
  not_extracted: 'critical',
};
const VALIDATION_LABEL: Record<LabResultValidationStatus, string> = {
  ok: 'OK',
  needs_review: 'Needs review',
  not_extracted: 'Not extracted',
};

function errMsg(e: unknown, fallback: string): string {
  return e instanceof ApiError ? e.message : fallback;
}

function fmtDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/** A single extracted/manual result row with inline correction + history. */
function ResultRow({ reportId, r }: { reportId: string; r: LabReportResult }) {
  const { toast } = useApp();
  const [editing, setEditing] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const correct = useCorrectLabReportResult(reportId);
  const corrections = useLabReportResultCorrections(showHistory ? r.id : null);

  const [form, setForm] = useState({
    test_name: r.test_name ?? '',
    value: r.value ?? '',
    unit: r.unit ?? '',
    reference_range: r.reference_range ?? '',
    reason: '',
  });
  const [error, setError] = useState<string | null>(null);

  // A field the user changed away from what extraction produced.
  const corrected = (field: 'test_name' | 'value' | 'unit' | 'reference_range') => {
    const ex = r[`extracted_${field}` as const];
    return r.entry_origin === 'extracted' && ex !== null && r[field] !== ex;
  };

  const submit = () => {
    setError(null);
    const body: Record<string, string | null> = {};
    (['test_name', 'value', 'unit', 'reference_range'] as const).forEach((f) => {
      const next = form[f].trim() === '' ? null : form[f].trim();
      const cur = r[f];
      if (next !== cur) body[f] = next;
    });
    if (Object.keys(body).length === 0) {
      setError('Change at least one field before saving.');
      return;
    }
    if (form.reason.trim()) body.reason = form.reason.trim();
    correct.mutate(
      { resultId: r.id, ...body },
      {
        onSuccess: () => {
          setEditing(false);
          setForm((s) => ({ ...s, reason: '' }));
          toast({ title: 'Result corrected', body: `${r.test_name ?? 'Result'} updated.`, tone: 'success' });
        },
        onError: (e) => setError(errMsg(e, 'Could not save the correction.')),
      },
    );
  };

  return (
    <div className="border-b border-ink-100 px-4 py-3 last:border-0">
      <div className="grid grid-cols-2 gap-2 md:grid-cols-[2fr_1fr_0.8fr_1.1fr_auto] md:items-center">
        <div className="min-w-0">
          <p className="truncate text-[13px] font-medium text-ink-800">{r.test_name ?? <span className="text-ink-400">— (not read)</span>}</p>
          {r.normalization_note && <p className="text-[11.5px] text-ink-400">{r.normalization_note}</p>}
        </div>
        <span className="tnum text-[13px] text-ink-900">{r.value ?? '—'}</span>
        <span className="text-[12.5px] text-ink-500">{r.unit ?? '—'}</span>
        <span className="tnum text-[12.5px] text-ink-500">{r.reference_range ?? '—'}</span>
        <div className="flex items-center gap-1.5">
          <Badge tone={VALIDATION_TONE[r.validation_status]} size="sm">
            {VALIDATION_LABEL[r.validation_status]}
          </Badge>
        </div>
      </div>

      <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11.5px] text-ink-400">
        <Badge tone={r.entry_origin === 'manual' ? 'scheduled' : 'neutral'} size="sm" dot={false}>
          {r.entry_origin === 'manual' ? 'Manual entry' : 'Auto-extracted'}
        </Badge>
        {(['test_name', 'value', 'unit', 'reference_range'] as const).some(corrected) && (
          <Badge tone="attention" size="sm" dot={false}>Corrected</Badge>
        )}
        {typeof r.confidence === 'number' && <span>confidence {(r.confidence * 100).toFixed(0)}%</span>}
        {r.source_snippet && <span className="truncate">“{r.source_snippet}”</span>}
        <button className="inline-flex items-center gap-1 text-brand-700 hover:underline" onClick={() => setEditing((v) => !v)}>
          <Pencil className="h-3 w-3" /> Correct
        </button>
        <button className="inline-flex items-center gap-1 text-ink-500 hover:underline" onClick={() => setShowHistory((v) => !v)}>
          <History className="h-3 w-3" /> History
        </button>
      </div>

      {r.validation_notes.length > 0 && (
        <ul className="mt-1.5 list-disc pl-5 text-[11.5px] text-amber-700">
          {r.validation_notes.map((n, i) => <li key={i}>{n}</li>)}
        </ul>
      )}

      {editing && (
        <div className="mt-3 rounded-lg border border-ink-200/70 bg-ink-50/50 p-3">
          <div className="grid gap-2 sm:grid-cols-2">
            <Input label="Test name" value={form.test_name} onChange={(e) => setForm((s) => ({ ...s, test_name: e.target.value }))} />
            <Input label="Value" value={form.value} onChange={(e) => setForm((s) => ({ ...s, value: e.target.value }))} />
            <Input label="Unit" value={form.unit} onChange={(e) => setForm((s) => ({ ...s, unit: e.target.value }))} />
            <Input label="Reference range" value={form.reference_range} onChange={(e) => setForm((s) => ({ ...s, reference_range: e.target.value }))} />
          </div>
          <Input className="mt-2" label="Reason (optional)" value={form.reason} onChange={(e) => setForm((s) => ({ ...s, reason: e.target.value }))} />
          {r.entry_origin === 'extracted' && (
            <p className="mt-2 text-[11.5px] text-ink-400">
              Originally extracted: {r.extracted_test_name ?? '—'} · {r.extracted_value ?? '—'} ·{' '}
              {r.extracted_unit ?? '—'} · {r.extracted_reference_range ?? '—'} (kept on record).
            </p>
          )}
          {error && <p className="mt-2 text-[12px] text-rose-600">{error}</p>}
          <div className="mt-2 flex gap-2">
            <Button size="sm" variant="primary" loading={correct.isPending} onClick={submit}>Save correction</Button>
            <Button size="sm" onClick={() => { setEditing(false); setError(null); }}>Cancel</Button>
          </div>
        </div>
      )}

      {showHistory && (
        <div className="mt-3 rounded-lg border border-ink-200/70 p-3 text-[12px]">
          {corrections.isLoading && <p className="text-ink-400">Loading history…</p>}
          {corrections.data && corrections.data.length === 0 && (
            <p className="text-ink-400">No corrections recorded for this result.</p>
          )}
          {corrections.data && corrections.data.length > 0 && (
            <ol className="space-y-1.5">
              {corrections.data.map((c) => (
                <li key={c.id} className="flex flex-wrap items-baseline gap-x-2">
                  <span className="font-medium text-ink-700">{c.field}</span>
                  <span className="tnum text-ink-500 line-through">{c.previous_value ?? '∅'}</span>
                  <span className="text-ink-400">→</span>
                  <span className="tnum text-ink-900">{c.new_value ?? '∅'}</span>
                  <span className="text-ink-400">· {fmtDate(c.created_at)}</span>
                  {c.reason && <span className="text-ink-400">· {c.reason}</span>}
                </li>
              ))}
            </ol>
          )}
        </div>
      )}
    </div>
  );
}

function ManualResultForm({ reportId }: { reportId: string }) {
  const { toast } = useApp();
  const add = useAddLabReportResult();
  const [form, setForm] = useState({ test_name: '', value: '', unit: '', reference_range: '' });
  const [error, setError] = useState<string | null>(null);

  const submit = () => {
    setError(null);
    add.mutate(
      {
        reportId,
        test_name: form.test_name.trim(),
        value: form.value.trim() || null,
        unit: form.unit.trim() || null,
        reference_range: form.reference_range.trim() || null,
      },
      {
        onSuccess: () => {
          setForm({ test_name: '', value: '', unit: '', reference_range: '' });
          toast({ title: 'Result added', body: `${form.test_name} recorded by hand.`, tone: 'success' });
        },
        onError: (e) => setError(errMsg(e, 'Could not add the result.')),
      },
    );
  };

  return (
    <div className="rounded-xl border border-ink-200/70 p-4">
      <p className="mb-3 text-[13px] font-semibold text-ink-800">Add a result by hand</p>
      <div className="grid gap-2 sm:grid-cols-2">
        <Input placeholder="Test name*" value={form.test_name} onChange={(e) => setForm((s) => ({ ...s, test_name: e.target.value }))} />
        <Input placeholder="Value" value={form.value} onChange={(e) => setForm((s) => ({ ...s, value: e.target.value }))} />
        <Input placeholder="Unit" value={form.unit} onChange={(e) => setForm((s) => ({ ...s, unit: e.target.value }))} />
        <Input placeholder="Reference range" value={form.reference_range} onChange={(e) => setForm((s) => ({ ...s, reference_range: e.target.value }))} />
      </div>
      {error && <p className="mt-2 text-[12px] text-rose-600">{error}</p>}
      <Button
        className="mt-3"
        size="sm"
        variant="primary"
        icon={<Plus className="h-3.5 w-3.5" />}
        disabled={!form.test_name.trim()}
        loading={add.isPending}
        onClick={submit}
      >
        Add result
      </Button>
    </div>
  );
}

function ReportDetailModal({ reportId, onClose }: { reportId: string; onClose: () => void }) {
  const { toast } = useApp();
  const detail = useLabReport(reportId);
  const runExtraction = useRunLabReportExtraction();
  const [docBusy, setDocBusy] = useState(false);

  const openDocument = async () => {
    setDocBusy(true);
    try {
      const blob = await fetchLabReportDocument(reportId);
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank', 'noopener,noreferrer');
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (e) {
      toast({ title: 'Could not open document', body: errMsg(e, 'The document could not be loaded.'), tone: 'error' });
    } finally {
      setDocBusy(false);
    }
  };

  const d = detail.data;

  return (
    <Modal open onClose={onClose} title="Laboratory report" subtitle={d?.original_filename} width="max-w-4xl">
      {detail.isLoading && <p className="text-[13px] text-ink-400">Loading report…</p>}
      {detail.isError && (
        <InfoNote tone="amber" icon={<AlertTriangle className="h-4 w-4" />}>
          {errMsg(detail.error, 'This report could not be loaded.')}
        </InfoNote>
      )}
      {d && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="text-[12.5px] text-ink-500">
              <span className="font-medium text-ink-700">{d.patient.full_name}</span>{' '}
              <span className="tnum text-ink-400">· {d.patient.uhid}</span>
              <span className="mx-2 text-ink-300">|</span>
              {(d.byte_size / 1024).toFixed(0)} KB · {d.page_count ?? '?'} page(s) · uploaded {fmtDate(d.created_at)}
            </div>
            <Button size="sm" icon={<ExternalLink className="h-3.5 w-3.5" />} loading={docBusy} onClick={openDocument}>
              View document
            </Button>
          </div>

          <div className="flex flex-wrap items-center gap-2 rounded-xl border border-ink-200/70 bg-ink-50/50 px-4 py-3">
            <Badge tone={STATUS_TONE[d.extraction_status]} size="sm">{STATUS_LABEL[d.extraction_status]}</Badge>
            <span className="text-[12.5px] text-ink-500">Method: {METHOD_LABEL[d.extraction_method]}</span>
            {d.extracted_at && <span className="text-[12px] text-ink-400">· {fmtDate(d.extracted_at)}</span>}
            <span className="flex-1" />
            <Button
              size="sm"
              variant="primary"
              icon={<RefreshCw className="h-3.5 w-3.5" />}
              loading={runExtraction.isPending}
              onClick={() =>
                runExtraction.mutate(reportId, {
                  onSuccess: (res) =>
                    toast({
                      title: res.extraction_status === 'failed' ? 'Extraction could not read the document' : 'Extraction finished',
                      body:
                        res.extraction_status === 'failed'
                          ? res.extraction_error ?? 'No values were extracted.'
                          : `${res.results.length} result row(s) available for review.`,
                      tone: res.extraction_status === 'failed' ? 'error' : 'success',
                    }),
                  onError: (e) => toast({ title: 'Extraction failed', body: errMsg(e, 'Try again.'), tone: 'error' }),
                })
              }
            >
              {d.extraction_status === 'pending' ? 'Run extraction' : 'Re-run extraction'}
            </Button>
          </div>

          {d.extraction_status === 'failed' && d.extraction_error && (
            <InfoNote tone="amber" icon={<ScanLine className="h-4 w-4" />}>
              {d.extraction_error} No values were invented — enter results by hand below.
            </InfoNote>
          )}

          <div className="overflow-hidden rounded-xl border border-ink-200/70">
            <div className="hidden grid-cols-[2fr_1fr_0.8fr_1.1fr_auto] gap-2 border-b border-ink-200/70 bg-ink-50/60 px-4 py-2 md:grid">
              {['Test', 'Value', 'Unit', 'Reference range', 'Status'].map((h) => (
                <span key={h} className="text-[11px] font-semibold uppercase tracking-wide text-ink-400">{h}</span>
              ))}
            </div>
            {d.results.length === 0 ? (
              <p className="px-4 py-8 text-center text-[13px] text-ink-400">
                No results yet. Run extraction, or add rows by hand.
              </p>
            ) : (
              d.results.map((r) => <ResultRow key={r.id} reportId={reportId} r={r} />)
            )}
          </div>

          <ManualResultForm reportId={reportId} />
        </div>
      )}
    </Modal>
  );
}

export function LabReportsPanel() {
  const { toast } = useApp();
  const patients = usePatients();
  const reports = useLabReports();
  const upload = useUploadLabReport();
  const fileRef = useRef<HTMLInputElement>(null);

  const [patientId, setPatientId] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [detailReportId, setDetailReportId] = useState<string | null>(null);

  const patientName = useMemo(() => {
    const m: Record<string, string> = {};
    for (const p of patients.data ?? []) m[p.id] = p.full_name;
    return m;
  }, [patients.data]);

  const doUpload = () => {
    setUploadError(null);
    if (!patientId || !file) {
      setUploadError('Choose a patient and a file.');
      return;
    }
    upload.mutate(
      { patientId, file },
      {
        onSuccess: (report) => {
          setFile(null);
          if (fileRef.current) fileRef.current.value = '';
          toast({ title: 'Report uploaded', body: 'Open it to run extraction.', tone: 'success' });
          setDetailReportId(report.id);
        },
        onError: (e) => setUploadError(errMsg(e, 'Upload failed.')),
      },
    );
  };

  const rows = reports.data?.items ?? [];

  return (
    <Card>
      <CardHeader
        icon={<FileText className="h-4 w-4" />}
        title="Uploaded & External Reports"
        subtitle="Upload an outside-lab PDF or scan, auto-extract the results, and correct them with a full history"
      />

      <div className="space-y-4 px-5 pb-5">
        <div className="rounded-xl border border-ink-200/70 p-4">
          <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
            <Select label="Patient" value={patientId} onChange={(e) => setPatientId(e.target.value)}>
              <option value="">Select a patient…</option>
              {(patients.data ?? []).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.full_name} · {p.uhid}
                </option>
              ))}
            </Select>
            <label className="block">
              <span className="mb-1.5 block text-[13.5px] font-medium text-ink-700">Report document</span>
              <input
                ref={fileRef}
                type="file"
                accept="application/pdf,image/png,image/jpeg,image/webp,image/tiff"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="block w-full text-[13px] text-ink-600 file:mr-3 file:rounded-lg file:border-0 file:bg-ink-100 file:px-3 file:py-2 file:text-[13px] file:font-medium file:text-ink-700 hover:file:bg-ink-200"
              />
            </label>
            <Button
              variant="primary"
              icon={<Upload className="h-4 w-4" />}
              loading={upload.isPending}
              disabled={!patientId || !file}
              onClick={doUpload}
            >
              Upload
            </Button>
          </div>
          {uploadError && <p className="mt-2 text-[12.5px] text-rose-600">{uploadError}</p>}
          <p className="mt-2 text-[11.5px] text-ink-400">
            Digital PDFs are read from their text layer; scanned PDFs and images go through OCR. Unreadable
            fields are left blank and flagged — never guessed.
          </p>
        </div>

        <div className="overflow-hidden rounded-xl border border-ink-200/70">
          {reports.isLoading && <p className="px-4 py-8 text-center text-[13px] text-ink-400">Loading reports…</p>}
          {reports.isError && (
            <p className="px-4 py-8 text-center text-[13px] text-amber-700">
              {errMsg(reports.error, 'Reports could not be loaded.')}
            </p>
          )}
          {reports.data && rows.length === 0 && (
            <p className="px-4 py-10 text-center text-[13px] text-ink-400">No lab reports uploaded yet.</p>
          )}
          {rows.map((r) => (
            <button
              key={r.id}
              onClick={() => setDetailReportId(r.id)}
              className="flex w-full flex-wrap items-center justify-between gap-2 border-b border-ink-100 px-4 py-3 text-left last:border-0 hover:bg-ink-50/60"
            >
              <div className="min-w-0">
                <p className="truncate text-[13.5px] font-medium text-ink-900">{r.original_filename}</p>
                <p className="text-[12px] text-ink-500">
                  {patientName[r.patient.id] ?? r.patient.full_name}{' '}
                  <span className="tnum text-ink-400">· {r.patient.uhid}</span>
                  <span className="mx-1.5 text-ink-300">·</span>
                  {fmtDate(r.created_at)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge tone={STATUS_TONE[r.extraction_status]} size="sm">
                  {r.extraction_status === 'completed' ? (
                    <>
                      <CheckCircle2 className="mr-0.5 h-2.5 w-2.5" /> {STATUS_LABEL[r.extraction_status]}
                    </>
                  ) : (
                    STATUS_LABEL[r.extraction_status]
                  )}
                </Badge>
              </div>
            </button>
          ))}
        </div>
      </div>

      {detailReportId && (
        <ReportDetailModal reportId={detailReportId} onClose={() => setDetailReportId(null)} />
      )}
    </Card>
  );
}
