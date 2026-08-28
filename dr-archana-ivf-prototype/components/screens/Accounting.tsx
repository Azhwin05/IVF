'use client';

import React, { useState } from 'react';
import { useApp } from '@/lib/store';
import { CASH_BOOK, GST_SUMMARY, PROFIT_LOSS, LEDGER_ACCOUNTS } from '@/lib/data';
import { cn, formatINR } from '@/lib/utils';
import { Card, CardHeader, Badge, Button, SectionTitle, Tabs, InfoNote } from '@/components/ui/primitives';
import { BarChart } from '@/components/ui/charts';
import { useCashBook, useLedgerAccounts, useProfitLoss } from '@/lib/api/accounting';
import { Wallet, Receipt, TrendingUp, TrendingDown, Download, FileSpreadsheet, ScrollText } from 'lucide-react';

function monthRange() {
  const now = new Date();
  const from = new Date(now.getFullYear(), now.getMonth(), 1);
  return { from: from.toISOString().slice(0, 10), to: now.toISOString().slice(0, 10) };
}

export function Accounting() {
  const { toast } = useApp();
  const [tab, setTab] = useState('cashbook');
  const { from, to } = monthRange();

  const cashBookQuery = useCashBook(from, to);
  const ledgerQuery = useLedgerAccounts();
  const profitLossQuery = useProfitLoss(from, to);

  const hasRealCashBook = (cashBookQuery.data ?? []).length > 0;
  const hasRealLedger = (ledgerQuery.data ?? []).length > 0;
  const hasRealPnL = !!profitLossQuery.data && Object.keys(profitLossQuery.data.revenue).length > 0;

  const cashBook = hasRealCashBook
    ? (() => {
        let running = 0;
        return [...(cashBookQuery.data ?? [])].reverse().map((c) => {
          running += c.amount_paise;
          return {
            date: new Date(c.entry_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }),
            particulars: c.particulars,
            type: c.entry_type === 'receipt' ? 'Receipt' : 'Payment',
            mode: c.mode,
            amount: Math.round(c.amount_paise / 100),
            balance: Math.round(running / 100),
          };
        }).reverse();
      })()
    : CASH_BOOK;

  const ledger = hasRealLedger
    ? (ledgerQuery.data ?? []).map((a) => ({ name: a.name, debit: Math.round(a.debit_paise / 100), credit: Math.round(a.credit_paise / 100), balance: Math.round(a.balance_paise / 100) }))
    : LEDGER_ACCOUNTS;

  const revenueBreakdown = hasRealPnL
    ? Object.entries(profitLossQuery.data!.revenue).map(([label, paise]) => ({ label: label.replace(/_/g, ' '), value: Math.round(paise / 100) }))
    : PROFIT_LOSS.revenue;
  const expenseBreakdown = hasRealPnL
    ? Object.entries(profitLossQuery.data!.expenses).map(([label, paise]) => ({ label: label.replace(/_/g, ' '), value: Math.round(paise / 100) }))
    : PROFIT_LOSS.expenses;

  const totalRevenue = revenueBreakdown.reduce((s, r) => s + r.value, 0);
  const totalExpenses = expenseBreakdown.reduce((s, e) => s + e.value, 0);
  const netProfit = totalRevenue - totalExpenses;

  return (
    <div className="screen-enter mx-auto max-w-[1400px] space-y-5 p-4 sm:p-6 lg:p-8">
      <SectionTitle
        eyebrow="Management"
        title="Accounting"
        description="Cash book, ledger, GST filings and profit & loss"
        action={
          <Button
            icon={<Download className="h-4 w-4" />}
            onClick={() => toast({ title: 'Export queued', body: 'Financial statements exported as PDF.', tone: 'success' })}
          >
            Export Statements
          </Button>
        }
      />

      <div className="grid gap-3.5 sm:grid-cols-3">
        <Card className="p-4">
          <p className="text-[12.5px] font-medium uppercase tracking-[0.06em] text-ink-400">Revenue (MTD)</p>
          <p className="tnum tracking-display mt-1.5 flex items-center gap-1.5 text-[24px] font-semibold text-emerald-700">
            <TrendingUp className="h-5 w-5" /> {formatINR(totalRevenue, true)}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-[12.5px] font-medium uppercase tracking-[0.06em] text-ink-400">Expenses (MTD)</p>
          <p className="tnum tracking-display mt-1.5 flex items-center gap-1.5 text-[24px] font-semibold text-rose-600">
            <TrendingDown className="h-5 w-5" /> {formatINR(totalExpenses, true)}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-[12.5px] font-medium uppercase tracking-[0.06em] text-ink-400">Net Profit (MTD)</p>
          <p className="tnum tracking-display mt-1.5 text-[24px] font-semibold text-ink-900">{formatINR(netProfit, true)}</p>
        </Card>
      </div>

      <Card className="overflow-hidden">
        <div className="px-4 pt-2">
          <Tabs
            tabs={[
              { id: 'cashbook', label: 'Cash Book' },
              { id: 'ledger', label: 'General Ledger' },
              { id: 'pnl', label: 'Profit & Loss' },
              { id: 'gst', label: 'GST' },
            ]}
            active={tab}
            onChange={setTab}
          />
        </div>

        {tab === 'cashbook' && (
          <div className="animate-fade-up overflow-hidden">
            <div className="hidden grid-cols-[100px_2fr_1fr_1fr_1fr_1fr] gap-4 border-b border-ink-200/70 bg-ink-50/60 px-5 py-2.5 md:grid">
              {['Date', 'Particulars', 'Type', 'Mode', 'Amount', 'Balance'].map((h) => (
                <span key={h} className="text-[12px] font-semibold uppercase tracking-[0.09em] text-ink-400">
                  {h}
                </span>
              ))}
            </div>
            <div className="stagger">
              {cashBook.map((c, i) => (
                <div
                  key={i}
                  style={{ ['--i' as string]: i }}
                  className="flex flex-col gap-1.5 border-b border-ink-100 px-4 py-3 last:border-0 hover:bg-ink-50/60 sm:px-5 md:grid md:grid-cols-[100px_2fr_1fr_1fr_1fr_1fr] md:items-center md:gap-4"
                >
                  <span className="tnum text-[12.5px] text-ink-500">{c.date}</span>
                  <span className="text-[13.5px] font-medium text-ink-800">{c.particulars}</span>
                  <div>
                    <Badge tone={c.type === 'Receipt' ? 'completed' : 'attention'} size="sm">
                      {c.type}
                    </Badge>
                  </div>
                  <span className="text-[13px] text-ink-500">{c.mode}</span>
                  <span className={cn('tnum text-[14px] font-semibold', c.amount >= 0 ? 'text-emerald-700' : 'text-rose-600')}>
                    {c.amount >= 0 ? '+' : ''}
                    {formatINR(c.amount)}
                  </span>
                  <span className="tnum text-[13.5px] font-medium text-ink-900">{formatINR(c.balance)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === 'ledger' && (
          <div className="animate-fade-up overflow-hidden">
            <div className="hidden grid-cols-[2fr_1fr_1fr_1fr] gap-4 border-b border-ink-200/70 bg-ink-50/60 px-5 py-2.5 md:grid">
              {['Account', 'Debit', 'Credit', 'Balance'].map((h) => (
                <span key={h} className="text-[12px] font-semibold uppercase tracking-[0.09em] text-ink-400">
                  {h}
                </span>
              ))}
            </div>
            <div className="stagger">
              {ledger.map((a, i) => (
                <div
                  key={a.name}
                  style={{ ['--i' as string]: i }}
                  className="flex flex-col gap-1.5 border-b border-ink-100 px-4 py-3 last:border-0 hover:bg-ink-50/60 sm:px-5 md:grid md:grid-cols-[2fr_1fr_1fr_1fr] md:items-center md:gap-4"
                >
                  <span className="text-[13.5px] font-medium text-ink-800">{a.name}</span>
                  <span className="tnum text-[13.5px] text-ink-600">{formatINR(a.debit)}</span>
                  <span className="tnum text-[13.5px] text-ink-600">{formatINR(a.credit)}</span>
                  <span className={cn('tnum text-[14px] font-semibold', a.balance >= 0 ? 'text-emerald-700' : 'text-rose-600')}>
                    {formatINR(a.balance)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === 'pnl' && (
          <div className="animate-fade-up grid gap-6 p-5 lg:grid-cols-2">
            <div>
              <p className="mb-3 text-[13px] font-semibold uppercase tracking-[0.08em] text-brand-700">Revenue</p>
              {revenueBreakdown.map((r) => (
                <div key={r.label} className="flex items-center justify-between border-b border-ink-100 py-2.5 last:border-0">
                  <span className="text-[13.5px] text-ink-600">{r.label}</span>
                  <span className="tnum text-[14px] font-medium text-ink-900">{formatINR(r.value)}</span>
                </div>
              ))}
              <div className="mt-2 flex items-center justify-between border-t-2 border-brand-200 pt-2.5">
                <span className="text-[13.5px] font-semibold text-ink-900">Total Revenue</span>
                <span className="tnum text-[14px] font-bold text-brand-700">{formatINR(totalRevenue)}</span>
              </div>
              <div className="mt-4">
                <BarChart data={revenueBreakdown.map((r) => ({ label: r.label.split(' ')[0], value: Math.round(r.value / 1000) }))} height={140} suffix="K" />
              </div>
            </div>
            <div>
              <p className="mb-3 text-[13px] font-semibold uppercase tracking-[0.08em] text-rose-600">Expenses</p>
              {expenseBreakdown.map((e) => (
                <div key={e.label} className="flex items-center justify-between border-b border-ink-100 py-2.5 last:border-0">
                  <span className="text-[13.5px] text-ink-600">{e.label}</span>
                  <span className="tnum text-[14px] font-medium text-ink-900">{formatINR(e.value)}</span>
                </div>
              ))}
              <div className="mt-2 flex items-center justify-between border-t-2 border-rose-200 pt-2.5">
                <span className="text-[13.5px] font-semibold text-ink-900">Total Expenses</span>
                <span className="tnum text-[14px] font-bold text-rose-600">{formatINR(totalExpenses)}</span>
              </div>
              <div className="mt-4">
                <BarChart data={expenseBreakdown.map((e) => ({ label: e.label.split(' ')[0], value: Math.round(e.value / 1000) }))} height={140} color="#E11D48" suffix="K" />
              </div>
            </div>
          </div>
        )}

        {tab === 'gst' && (
          <div className="animate-fade-up p-5">
            <div className="grid gap-3.5 sm:grid-cols-3">
              <Card className="p-4">
                <p className="text-[12px] font-medium uppercase tracking-[0.06em] text-ink-400">Output GST</p>
                <p className="tnum mt-1.5 text-[22px] font-semibold text-ink-900">{formatINR(GST_SUMMARY.outputGST)}</p>
              </Card>
              <Card className="p-4">
                <p className="text-[12px] font-medium uppercase tracking-[0.06em] text-ink-400">Input GST</p>
                <p className="tnum mt-1.5 text-[22px] font-semibold text-ink-900">{formatINR(GST_SUMMARY.inputGST)}</p>
              </Card>
              <Card className="p-4">
                <p className="text-[12px] font-medium uppercase tracking-[0.06em] text-ink-400">Net Payable</p>
                <p className="tnum mt-1.5 text-[22px] font-semibold text-amber-700">{formatINR(GST_SUMMARY.netPayable)}</p>
              </Card>
            </div>
            <div className="mt-4">
              <InfoNote tone="amber" icon={<ScrollText className="h-4 w-4" />}>
                GST filing for <span className="font-medium">{GST_SUMMARY.period}</span> is currently{' '}
                <span className="font-medium">{GST_SUMMARY.filingStatus}</span>.
              </InfoNote>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
