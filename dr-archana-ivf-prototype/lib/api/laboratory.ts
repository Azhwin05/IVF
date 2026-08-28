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
