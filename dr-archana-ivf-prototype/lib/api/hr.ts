import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';

export type LeaveStatus = 'pending' | 'approved' | 'rejected';

export interface EmployeeOut {
  id: string;
  full_name: string;
  department: string;
  designation: string;
  phone: string | null;
  joined_date: string;
  leave_balance_days: number;
}

export interface LeaveRequestOut {
  id: string;
  employee_id: string;
  leave_type: string;
  from_date: string;
  to_date: string;
  status: LeaveStatus;
}

export function useEmployees() {
  return useQuery({
    queryKey: ['employees'],
    queryFn: () => apiFetch<EmployeeOut[]>('/hr/employees'),
  });
}

export function useLeaveRequests() {
  return useQuery({
    queryKey: ['leave-requests'],
    queryFn: () => apiFetch<LeaveRequestOut[]>('/hr/leave-requests'),
  });
}

export function useDecideLeaveRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ leaveId, approve }: { leaveId: string; approve: boolean }) =>
      apiFetch<LeaveRequestOut>(`/hr/leave-requests/${leaveId}/decide?approve=${approve}`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leave-requests'] });
      queryClient.invalidateQueries({ queryKey: ['employees'] });
    },
  });
}
