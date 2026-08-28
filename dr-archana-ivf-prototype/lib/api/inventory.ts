import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './client';

export type InventoryCategory = 'ivf_consumables' | 'cryogenic_supplies' | 'lab_supplies' | 'surgical_equipment';

export interface InventoryItemOut {
  id: string;
  name: string;
  category: InventoryCategory;
  unit: string;
  stock: number;
  reorder_level: number;
  location: string | null;
  supplier: string | null;
  last_restocked: string | null;
}

export function useInventoryItems(category?: InventoryCategory) {
  return useQuery({
    queryKey: ['inventory-items', category ?? 'all'],
    queryFn: () => apiFetch<InventoryItemOut[]>(`/inventory/items${category ? `?category=${category}` : ''}`),
  });
}
