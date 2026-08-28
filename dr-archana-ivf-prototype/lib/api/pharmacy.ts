import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './client';

export interface MedicineOut {
  id: string;
  generic_name: string;
  brand_name: string | null;
  category: string | null;
  unit: string;
  reorder_level: number;
  total_available: number;
}

export interface SaleLineOut {
  medicine_id: string;
  batch_id: string;
  quantity: number;
  unit_price_paise: number;
}

export interface SaleOut {
  id: string;
  bill_number: string;
  patient_id: string;
  total_amount_paise: number;
  status: string;
  lines: SaleLineOut[];
}

export function useMedicines() {
  return useQuery({
    queryKey: ['medicines'],
    queryFn: () => apiFetch<MedicineOut[]>('/pharmacy/medicines'),
  });
}

export function usePharmacySales() {
  return useQuery({
    queryKey: ['pharmacy-sales'],
    queryFn: () => apiFetch<SaleOut[]>('/pharmacy/sales'),
  });
}
