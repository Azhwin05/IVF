import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';

export type InvoiceStatus = 'pending' | 'partially_paid' | 'paid' | 'overridden' | 'cancelled';
export type PaymentMethod = 'cash' | 'upi' | 'card' | 'bank_transfer' | 'credit';

export interface ChargeOut {
  id: string;
  service_code: string;
  description: string;
  amount_paise: number;
  covered_by_package: boolean;
}

export interface InvoiceOut {
  id: string;
  invoice_number: string;
  patient_id: string;
  status: InvoiceStatus;
  total_amount_paise: number;
  paid_amount_paise: number;
  discount_paise: number;
  outstanding_paise: number;
  charges: ChargeOut[];
}

export interface PaymentOut {
  id: string;
  receipt_number: string;
  invoice_id: string;
  amount_paise: number;
  method: PaymentMethod;
  is_refund: boolean;
}

export function useInvoices(patientId?: string | null) {
  return useQuery({
    queryKey: ['invoices', patientId ?? 'all'],
    queryFn: () => apiFetch<InvoiceOut[]>(`/billing/invoices${patientId ? `?patient_id=${patientId}` : ''}`),
  });
}

function newIdempotencyKey() {
  return typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
}

export function useRecordPayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { invoice_id: string; amount_paise: number; method: PaymentMethod; reference?: string | null }) =>
      apiFetch<PaymentOut>('/billing/payments', { method: 'POST', body, headers: { 'Idempotency-Key': newIdempotencyKey() } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['invoices'] }),
  });
}

export function useApplyDiscount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { invoice_id: string; discount_paise: number; reason: string }) =>
      apiFetch<InvoiceOut>('/billing/discounts', { method: 'POST', body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['invoices'] }),
  });
}
