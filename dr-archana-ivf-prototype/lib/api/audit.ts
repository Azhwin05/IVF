import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './client';

export interface AuditEventOut {
  id: string;
  timestamp: string;
  actor_id: string | null;
  actor_role: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  reason: string | null;
  source_ip: string | null;
}

export function useAuditEvents(q?: string) {
  return useQuery({
    queryKey: ['audit-events', q ?? ''],
    queryFn: () => apiFetch<AuditEventOut[]>(`/audit${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  });
}
