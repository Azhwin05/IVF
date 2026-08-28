import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './client';

export type PurchaseOrderStatus = 'pending_approval' | 'approved' | 'dispatched' | 'received' | 'rejected';

export interface PurchaseOrderOut {
  id: string;
  po_number: string;
  item_description: string;
  supplier: string;
  quantity_ordered: number;
  amount_paise: number;
  status: PurchaseOrderStatus;
}

export function usePurchaseOrders() {
  return useQuery({
    queryKey: ['purchase-orders'],
    queryFn: () => apiFetch<PurchaseOrderOut[]>('/purchasing/orders'),
  });
}
