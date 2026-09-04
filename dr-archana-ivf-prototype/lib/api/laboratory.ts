import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch, apiFetchBlob, apiUpload } from './client';

export type LabOrderStatus = 'ordered' | 'sample_collected' | 'in_progress' | 'report_ready' | 'delivered';
export type LabOrderSource = 'internal_lab' | 'external_lab';
export type LabOrderPriority = 'routine' | 'urgent';

export interface LabOrderOut {
  id: string;
  order_number: string;
  patient_id: string;
  ordered_by_id: string;
  test_name: string;
  sample_type: string | null;
  source: LabOrderSource;
  external_lab_name: string | null;
  priority: LabOrderPriority;
  status: LabOrderStatus;
  created_at: string;
}

export function useLabOrders(status?: LabOrderStatus) {
  return useQuery({
    queryKey: ['lab-orders', status ?? 'all'],
    queryFn: () => apiFetch<LabOrderOut[]>(`/laboratory/orders${status ? `?status=${status}` : ''}`),
  });
}

export function useCreateLabOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      patient_id: string;
      test_name: string;
      test_catalogue_id?: string | null;
      sample_type?: string | null;
      source?: LabOrderSource;
      external_lab_name?: string | null;
      priority?: LabOrderPriority;
    }) => apiFetch<LabOrderOut>('/laboratory/orders', { method: 'POST', body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lab-orders'] }),
  });
}

export function useUpdateLabOrderStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ orderId, status }: { orderId: string; status: LabOrderStatus }) =>
      apiFetch<LabOrderOut>(`/laboratory/orders/${orderId}/status`, { method: 'POST', body: { status } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lab-orders'] }),
  });
}

// ---- Structured lab results ----

export type LabResultFlag = 'normal' | 'low' | 'high' | 'critical';

export interface LabResultOut {
  id: string;
  order_id: string;
  parameter_name: string;
  value: string;
  unit: string | null;
  reference_range: string | null;
  flag: LabResultFlag;
  entered_by_id: string;
  created_at: string;
}

export function useLabResults(orderId: string | null) {
  return useQuery({
    queryKey: ['lab-results', orderId],
    queryFn: () => apiFetch<LabResultOut[]>(`/laboratory/orders/${orderId}/results`),
    enabled: !!orderId,
  });
}

export function useAddLabResult() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ orderId, ...body }: { orderId: string; parameter_name: string; value: string; unit?: string | null; reference_range?: string | null; flag?: LabResultFlag }) =>
      apiFetch<LabResultOut>(`/laboratory/orders/${orderId}/results`, { method: 'POST', body }),
    onSuccess: (_, vars) => queryClient.invalidateQueries({ queryKey: ['lab-results', vars.orderId] }),
  });
}

// ===========================================================================
// Outside-lab report ingestion: upload a PDF / scanned image, run OCR /
// PDF-text extraction, review the structured results, and correct them with a
// full append-only history. Independent of the /orders workflow above.
// ===========================================================================

export type LabDocumentKind = 'digital_pdf' | 'scanned_pdf' | 'image' | 'unknown';
export type LabExtractionStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type LabExtractionMethod =
  | 'native_pdf_text'
  | 'ocr'
  | 'ai_vision'
  | 'manual'
  | 'none';
export type LabEntryOrigin = 'extracted' | 'manual';
export type LabNormalizationMatch = 'exact_alias' | 'unmatched' | 'manual';
export type LabResultValidationStatus = 'ok' | 'needs_review' | 'not_extracted';
export type LabCorrectionField = 'test_name' | 'value' | 'unit' | 'reference_range';

export interface LabReportPatientRef {
  id: string;
  uhid: string;
  full_name: string;
}

export interface LabReportResult {
  id: string;
  report_id: string;
  test_name: string | null;
  value: string | null;
  unit: string | null;
  reference_range: string | null;
  // Exactly what extraction produced. Null on every field for a hand-added row.
  extracted_test_name: string | null;
  extracted_value: string | null;
  extracted_unit: string | null;
  extracted_reference_range: string | null;
  entry_origin: LabEntryOrigin;
  normalization_match: LabNormalizationMatch;
  normalization_note: string | null;
  validation_status: LabResultValidationStatus;
  validation_notes: string[];
  source_snippet: string | null;
  source_location: string | null;
  confidence: number | null;
  created_at: string;
  updated_at: string;
}

export interface LabReportSummary {
  id: string;
  patient: LabReportPatientRef;
  original_filename: string;
  content_type: string;
  byte_size: number;
  document_kind: LabDocumentKind;
  extraction_status: LabExtractionStatus;
  extraction_method: LabExtractionMethod;
  extraction_error: string | null;
  page_count: number | null;
  extracted_at: string | null;
  created_at: string;
}

export interface LabReportDetail extends LabReportSummary {
  results: LabReportResult[];
}

export interface LabReportPage {
  items: LabReportSummary[];
  next_cursor: string | null;
  has_more: boolean;
}

export interface LabReportResultCorrection {
  id: string;
  result_id: string;
  field: LabCorrectionField;
  previous_value: string | null;
  new_value: string | null;
  corrected_by_id: string;
  reason: string | null;
  created_at: string;
}

export function useLabReports(patientId?: string | null) {
  return useQuery({
    queryKey: ['lab-reports', patientId ?? 'all'],
    queryFn: () =>
      apiFetch<LabReportPage>(
        `/laboratory/reports${patientId ? `?patient_id=${encodeURIComponent(patientId)}` : ''}`,
      ),
  });
}

export function useLabReport(reportId: string | null) {
  return useQuery({
    queryKey: ['lab-report', reportId],
    queryFn: () => apiFetch<LabReportDetail>(`/laboratory/reports/${reportId}`),
    enabled: !!reportId,
  });
}

export function useUploadLabReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ patientId, file }: { patientId: string; file: File }) => {
      const form = new FormData();
      form.append('patient_id', patientId);
      form.append('file', file);
      return apiUpload<LabReportDetail>('/laboratory/reports', form);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lab-reports'] }),
  });
}

export function useRunLabReportExtraction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (reportId: string) =>
      apiFetch<LabReportDetail>(`/laboratory/reports/${reportId}/extraction`, { method: 'POST' }),
    onSuccess: (data) => {
      queryClient.setQueryData(['lab-report', data.id], data);
      queryClient.invalidateQueries({ queryKey: ['lab-reports'] });
    },
  });
}

export function useAddLabReportResult() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      reportId,
      ...body
    }: {
      reportId: string;
      test_name: string;
      value?: string | null;
      unit?: string | null;
      reference_range?: string | null;
    }) => apiFetch<LabReportResult>(`/laboratory/reports/${reportId}/results`, { method: 'POST', body }),
    onSuccess: (_, vars) =>
      queryClient.invalidateQueries({ queryKey: ['lab-report', vars.reportId] }),
  });
}

export function useCorrectLabReportResult(reportId: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      resultId,
      ...body
    }: {
      resultId: string;
      test_name?: string | null;
      value?: string | null;
      unit?: string | null;
      reference_range?: string | null;
      reason?: string | null;
    }) =>
      apiFetch<LabReportResult>(`/laboratory/reports/results/${resultId}`, {
        method: 'PATCH',
        body,
      }),
    onSuccess: (_, vars) => {
      if (reportId) queryClient.invalidateQueries({ queryKey: ['lab-report', reportId] });
      queryClient.invalidateQueries({ queryKey: ['lab-result-corrections', vars.resultId] });
    },
  });
}

export function useLabReportResultCorrections(resultId: string | null) {
  return useQuery({
    queryKey: ['lab-result-corrections', resultId],
    queryFn: () =>
      apiFetch<LabReportResultCorrection[]>(`/laboratory/reports/results/${resultId}/corrections`),
    enabled: !!resultId,
  });
}

/** Fetches the stored report document as a Blob for in-tab preview / download. */
export function fetchLabReportDocument(reportId: string): Promise<Blob> {
  return apiFetchBlob(`/laboratory/reports/${reportId}/document`);
}
