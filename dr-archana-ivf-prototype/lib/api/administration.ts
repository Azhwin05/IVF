import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './client';

export interface ProcedureChargeOut {
  id: string;
  service_code: string;
  procedure_name: string;
  charge_paise: number;
  is_active: boolean;
}

export interface PackageOut {
  id: string;
  name: string;
  price_paise: number;
  validity_description: string | null;
  is_active: boolean;
}

export interface LabTestOut {
  id: string;
  test_name: string;
  price_paise: number;
  turnaround_time: string;
  sample_type: string | null;
  is_active: boolean;
}

export function useProcedureCharges() {
  return useQuery({
    queryKey: ['procedure-charges'],
    queryFn: () => apiFetch<ProcedureChargeOut[]>('/administration/procedure-charges'),
  });
}

export function usePackages() {
  return useQuery({
    queryKey: ['packages'],
    queryFn: () => apiFetch<PackageOut[]>('/administration/packages'),
  });
}

export function useLabTestCatalogue() {
  return useQuery({
    queryKey: ['lab-test-catalogue'],
    queryFn: () => apiFetch<LabTestOut[]>('/administration/lab-tests'),
  });
}
