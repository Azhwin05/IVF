import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';

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
