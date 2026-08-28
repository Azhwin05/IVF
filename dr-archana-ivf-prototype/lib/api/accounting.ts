import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './client';

export type EntryType = 'receipt' | 'payment';

export interface CashBookEntryOut {
  id: string;
  entry_date: string;
  particulars: string;
  entry_type: EntryType;
  mode: string;
  amount_paise: number;
}

export interface LedgerAccountOut {
  id: string;
  name: string;
  debit_paise: number;
  credit_paise: number;
  balance_paise: number;
}

export interface ProfitLossReport {
  period: string;
  revenue: Record<string, number>;
  expenses: Record<string, number>;
  net_profit_paise: number;
}

export function useCashBook(fromDate: string, toDate: string) {
  return useQuery({
    queryKey: ['cash-book', fromDate, toDate],
    queryFn: () => apiFetch<CashBookEntryOut[]>(`/accounting/cash-book?from_date=${fromDate}&to_date=${toDate}`),
  });
}

export function useLedgerAccounts() {
  return useQuery({
    queryKey: ['ledger-accounts'],
    queryFn: () => apiFetch<LedgerAccountOut[]>('/accounting/ledger'),
  });
}

export function useProfitLoss(fromDate: string, toDate: string) {
  return useQuery({
    queryKey: ['profit-loss', fromDate, toDate],
    queryFn: () => apiFetch<ProfitLossReport>(`/accounting/profit-loss?from_date=${fromDate}&to_date=${toDate}`),
  });
}
