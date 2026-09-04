'use client';

import React, { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, CheckCircle2, Download, FileText, Loader2 } from 'lucide-react';

import { Badge, Button, Card, CardHeader, Select } from '@/components/ui/primitives';
import { useApp } from '@/lib/store';
import { ApiError } from '@/lib/api/client';
import { usePatients } from '@/lib/api/patients';
import {
  fetchReportJobResult,
  useReportJob,
  useSubmitReportJob,
  type ReportJobStatus,
} from '@/lib/api/reports';

/** Lifecycle labels + design-system tone for each async report-job state. */
const STATE: Record<
  ReportJobStatus,
  { label: string; tone: 'scheduled' | 'active' | 'completed' | 'critical' }
> = {
  queued: { label: 'Queued', tone: 'scheduled' },
  running: { label: 'Running', tone: 'active' },
  succeeded: { label: 'Completed', tone: 'completed' },
  failed: { label: 'Failed', tone: 'critical' },
};

/**
 * Compact "Patient Report" section for the Reports & Analytics screen. Wraps the
 * already-implemented async report-job pipeline: submit -> poll status
 * (queued -> running -> completed / failed) -> download the artifact. All API
 * calls go through the existing hooks in lib/api/reports.ts — nothing new
 * server-side.
 */
export function PatientReportCard() {
  const { toast } = useApp();
  const queryClient = useQueryClient();
  const patients = usePatients();
  const submit = useSubmitReportJob();

  const [patientId, setPatientId] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);

  // Polls GET /reports/jobs/{id} every 1.5s and stops itself on a terminal state.
  const job = useReportJob(jobId);
  const status = job.data?.status ?? null;
  const inFlight =
    submit.isPending || (jobId !== null && status !== 'succeeded' && status !== 'failed');

  const generate = () => {
    setError(null);
    if (!patientId) {
      setError('Select a patient first.');
      return;
    }
    submit.mutate(
      { report_type: 'patient_summary', parameters: { patient_id: patientId } },
      {
        onSuccess: (created) => {
          // Seed the poll query with the freshly-queued job so the lifecycle
          // starts visibly at "Queued" instead of a blank frame while the
          // first GET is in flight. Same query key as useReportJob().
          queryClient.setQueryData(['report-job', created.id], created);
          setJobId(created.id);
        },
        onError: (e) =>
          setError(e instanceof ApiError ? e.message : 'Could not start the report.'),
      },
    );
  };

  const download = async () => {
    if (!jobId) return;
    setDownloading(true);
    try {
      const blob = await fetchReportJobResult(jobId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `patient-summary-${jobId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 30_000);
      toast({ title: 'Report downloaded', tone: 'success' });
    } catch (e) {
      toast({
        title: 'Download failed',
        body: e instanceof ApiError ? e.message : 'Please try again.',
        tone: 'error',
      });
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Card>
      <CardHeader
        icon={<FileText className="h-4 w-4" />}
        title="Patient Report"
        subtitle="Generate a detailed report from the patient's available clinical records."
      />
      <div className="flex flex-col gap-3 px-5 pb-5 sm:flex-row sm:flex-wrap sm:items-end">
        <div className="sm:w-72">
          <Select
            label="Patient"
            value={patientId}
            disabled={inFlight}
            onChange={(e) => {
              setPatientId(e.target.value);
              setJobId(null);
              setError(null);
            }}
          >
            <option value="">Select a patient…</option>
            {(patients.data ?? []).map((p) => (
              <option key={p.id} value={p.id}>
                {p.full_name} · {p.uhid}
              </option>
            ))}
          </Select>
        </div>

        <Button
          variant="primary"
          icon={<FileText className="h-4 w-4" />}
          disabled={!patientId || inFlight}
          loading={submit.isPending}
          onClick={generate}
        >
          Generate Report
        </Button>

        {jobId && status && (
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={STATE[status].tone} size="sm" dot={status !== 'running'}>
              {status === 'running' && <Loader2 className="mr-0.5 h-2.5 w-2.5 animate-spin" />}
              {status === 'succeeded' && <CheckCircle2 className="mr-0.5 h-2.5 w-2.5" />}
              {status === 'failed' && <AlertTriangle className="mr-0.5 h-2.5 w-2.5" />}
              {STATE[status].label}
            </Badge>

            {status === 'succeeded' && (
              <>
                <span className="text-[12.5px] font-medium text-ink-600">Report ready</span>
                <Button
                  size="sm"
                  icon={<Download className="h-3.5 w-3.5" />}
                  loading={downloading}
                  onClick={download}
                >
                  Download Report
                </Button>
              </>
            )}

            {status === 'failed' && (
              <span className="text-[12.5px] text-rose-600">
                {job.data?.error ?? 'Report generation failed.'}
              </span>
            )}
          </div>
        )}
      </div>

      {error && <p className="-mt-2 px-5 pb-4 text-[12.5px] text-rose-600">{error}</p>}
    </Card>
  );
}
