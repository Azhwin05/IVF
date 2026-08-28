'use client';

import React, { useRef, useLayoutEffect, useState } from 'react';
import { useApp } from '@/lib/store';
import { navForRole, SECTIONS } from './nav';
import { cn } from '@/lib/utils';
import { Avatar } from '@/components/ui/primitives';
import { LogOut, LifeBuoy, ChevronsLeft, Command, X } from 'lucide-react';

export function Sidebar({
  collapsed,
  onToggle,
  mobileOpen,
  onCloseMobile,
}: {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}) {
  const { role, user, screen, go, logout, setPaletteOpen } = useApp();
  const listRef = useRef<HTMLDivElement>(null);
  const [indicator, setIndicator] = useState({ top: 0, height: 0, visible: false });

  const items = role ? navForRole(role) : [];

  const navigate = (id: (typeof items)[number]['id']) => {
    go(id);
    onCloseMobile();
  };

  // The active pill slides between items instead of hard-cutting
  useLayoutEffect(() => {
    const el = listRef.current?.querySelector<HTMLElement>(`[data-nav="${screen}"]`);
    if (el && listRef.current) {
      const parentTop = listRef.current.getBoundingClientRect().top;
      const r = el.getBoundingClientRect();
      setIndicator({ top: r.top - parentTop, height: r.height, visible: true });
    } else {
      setIndicator((s) => ({ ...s, visible: false }));
    }
  }, [screen, collapsed, items.length]);

  return (
    <>
      {/* Mobile / tablet backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 animate-fade-in bg-ink-950/40 backdrop-blur-[2px] lg:hidden"
          onClick={onCloseMobile}
        />
      )}

      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex h-full w-[280px] shrink-0 flex-col border-r border-ink-200/70 bg-gradient-to-b from-white to-ink-50/50 transition-transform duration-300 ease-spring',
          'lg:relative lg:z-30 lg:translate-x-0 lg:transition-[width]',
          collapsed ? 'lg:w-[76px]' : 'lg:w-[268px]',
          mobileOpen ? 'translate-x-0 shadow-pop' : '-translate-x-full'
        )}
      >
        {/* Brand */}
        <div className="flex h-[68px] shrink-0 items-center gap-3 border-b border-ink-200/60 px-5">
          <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 shadow-[0_2px_8px_-1px_rgba(5,150,105,.4)]">
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none">
              <path
                d="M12 21c-1.5-3-5-5.2-5-9a5 5 0 0110 0c0 3.8-3.5 6-5 9z"
                fill="white"
                fillOpacity="0.95"
              />
              <circle cx="12" cy="11" r="2.1" fill="#059669" />
            </svg>
          </div>
          {!collapsed && (
            <div className="min-w-0 flex-1 animate-fade-in">
              <p className="truncate font-display text-[16px] leading-tight text-ink-900">Dr. Archana</p>
              <p className="truncate text-[10.5px] font-medium uppercase tracking-[0.1em] text-brand-700">
                Clinical OS
              </p>
            </div>
          )}
          <button
            onClick={onCloseMobile}
            aria-label="Close menu"
            className="ml-auto flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-ink-400 transition-colors hover:bg-ink-100 hover:text-ink-800 lg:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

      {/* Search trigger */}
      <div className="px-3 pt-3">
        <button
          onClick={() => setPaletteOpen(true)}
          aria-label="Search"
          className={cn(
            'press flex min-h-[44px] w-full items-center gap-2 rounded-lg border border-ink-200 bg-white px-2.5 py-2 text-[14px] text-ink-500 transition-colors hover:border-ink-300 hover:text-ink-700',
            collapsed && 'justify-center px-0'
          )}
        >
          <Command className="h-4 w-4 shrink-0" />
          {!collapsed && (
            <>
              <span className="flex-1 text-left">Search…</span>
              <kbd className="rounded border border-ink-200 bg-ink-50 px-1.5 py-0.5 font-mono text-[10px] text-ink-400">
                ⌘K
              </kbd>
            </>
          )}
        </button>
      </div>

      {/* Navigation */}
      <div ref={listRef} className="scroll-area relative flex-1 px-3 py-3">
        {/* sliding active indicator */}
        {indicator.visible && (
          <div
            className="nav-indicator pointer-events-none absolute left-3 right-3 rounded-lg bg-brand-50 ring-1 ring-inset ring-brand-600/12"
            style={{ top: indicator.top, height: indicator.height }}
          />
        )}
        {indicator.visible && (
          <div
            className="nav-indicator pointer-events-none absolute left-3 w-[3px] rounded-r-full bg-brand-600"
            style={{ top: indicator.top + 8, height: Math.max(indicator.height - 16, 12) }}
          />
        )}

        {SECTIONS.map((section) => {
          const secItems = items.filter((i) => i.section === section);
          if (!secItems.length) return null;
          return (
            <div key={section} className="mb-4 last:mb-0">
              {!collapsed && (
                <p className="mb-1.5 px-2.5 text-[11.5px] font-semibold uppercase tracking-[0.13em] text-ink-500">
                  {section}
                </p>
              )}
              {collapsed && <div className="mx-2.5 mb-2 h-px bg-ink-200/70" />}
              <div className="space-y-0.5">
                {secItems.map((item) => {
                  const Icon = item.icon;
                  const active = screen === item.id;
                  return (
                    <button
                      key={item.id}
                      data-nav={item.id}
                      onClick={() => navigate(item.id)}
                      title={collapsed ? item.label : undefined}
                      aria-current={active ? 'page' : undefined}
                      className={cn(
                        'relative flex min-h-[44px] w-full items-center gap-3 rounded-lg px-2.5 py-2.5 text-[14.5px] font-medium transition-colors duration-200',
                        active ? 'text-brand-800' : 'text-ink-600 hover:text-ink-900',
                        collapsed && 'justify-center px-0'
                      )}
                    >
                      <Icon
                        className={cn(
                          'h-[19px] w-[19px] shrink-0 transition-colors',
                          active ? 'text-brand-600' : 'text-ink-400'
                        )}
                        strokeWidth={active ? 2.2 : 1.9}
                      />
                      {!collapsed && <span className="flex-1 truncate text-left">{item.label}</span>}
                      {!collapsed && item.badge && (
                        <span className="tnum rounded-full bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold text-amber-700">
                          {item.badge}
                        </span>
                      )}
                      {collapsed && item.badge && (
                        <span className="absolute right-3 top-1.5 h-1.5 w-1.5 rounded-full bg-amber-500" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="shrink-0 border-t border-ink-200/60 p-3">
        {!collapsed && user && (
          <div className="mb-2 flex items-center gap-2.5 rounded-lg bg-white p-2 ring-1 ring-ink-200/70">
            <Avatar initials={user.initials} size="sm" gradient={user.accent} />
            <div className="min-w-0 flex-1">
              <p className="truncate text-[12.5px] font-semibold text-ink-900">
                {user.name.replace('Dr. ', 'Dr. ')}
              </p>
              <p className="truncate text-[10.5px] text-ink-500">{user.title}</p>
            </div>
          </div>
        )}
        <div className={cn('flex gap-1', collapsed && 'flex-col')}>
          <button
            onClick={onToggle}
            title={collapsed ? 'Expand menu' : 'Collapse menu'}
            aria-label={collapsed ? 'Expand menu' : 'Collapse menu'}
            className="hidden min-h-[44px] flex-1 items-center justify-center gap-1.5 rounded-lg px-2 py-2 text-[13px] font-medium text-ink-500 transition-colors hover:bg-ink-100 hover:text-ink-800 lg:flex"
          >
            <ChevronsLeft className={cn('h-4 w-4 transition-transform duration-300', collapsed && 'rotate-180')} />
            {!collapsed && 'Collapse'}
          </button>
          {!collapsed && (
            <button
              title="Help"
              aria-label="Help"
              className="flex min-h-[44px] min-w-[44px] items-center justify-center rounded-lg px-2.5 py-2 text-ink-500 transition-colors hover:bg-ink-100 hover:text-ink-800"
            >
              <LifeBuoy className="h-[18px] w-[18px]" />
            </button>
          )}
          <button
            onClick={logout}
            title="Sign out"
            aria-label="Sign out"
            className="flex min-h-[44px] min-w-[44px] items-center justify-center rounded-lg px-2.5 py-2 text-ink-500 transition-colors hover:bg-rose-50 hover:text-rose-600"
          >
            <LogOut className="h-[18px] w-[18px]" />
          </button>
        </div>
      </div>
      </aside>
    </>
  );
}
