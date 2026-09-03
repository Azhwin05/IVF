'use client';

import React from 'react';
import { useApp } from '@/lib/store';
import { usePreferences, preferenceClasses } from '@/lib/preferences';
import type { TextScale, Density, SidebarSections } from '@/lib/preferences';
import { navForRole, SCREEN_TITLES } from '@/components/layout/nav';
import { cn } from '@/lib/utils';
import {
  Card,
  CardHeader,
  Badge,
  Button,
  SectionTitle,
  Select,
  Switch,
  SegmentedControl,
  SettingRow,
  InfoNote,
} from '@/components/ui/primitives';
import {
  Type,
  Rows,
  Contrast,
  Zap,
  PanelLeft,
  Clock,
  LogIn,
  RotateCcw,
  Eye,
  Monitor,
} from 'lucide-react';

/** A miniature of the real interface that re-renders under whatever the
 *  staff member has just selected, so the effect of a setting is visible
 *  before they go back to a clinical screen and discover it. */
function LivePreview() {
  const { prefs } = usePreferences();
  return (
    <div className={cn('rounded-xl border border-ink-200 bg-ink-50/60 p-4', preferenceClasses(prefs))}>
      <div className="rounded-lg border border-ink-200 bg-white">
        <div className="flex items-center justify-between border-b border-ink-100 px-4 py-3">
          <div>
            <p className="text-[14.5px] font-semibold text-ink-900">Priya Raman</p>
            <p className="text-[12.5px] text-ink-500">DAIVF-2026-00428 · Stimulation Day 8</p>
          </div>
          <Badge tone="active" size="sm">
            Active cycle
          </Badge>
        </div>
        {[
          { l: 'Estradiol (E2)', v: '1,240 pg/mL', t: 'completed' as const, s: 'Normal' },
          { l: 'LH', v: '4.2 mIU/mL', t: 'attention' as const, s: 'Review' },
        ].map((r) => (
          <div key={r.l} className="flex items-center justify-between border-b border-ink-100 px-4 py-3 last:border-0">
            <span className="text-[14px] text-ink-800">{r.l}</span>
            <div className="flex items-center gap-3">
              <span className="tnum text-[14px] font-semibold text-ink-900">{r.v}</span>
              <Badge tone={r.t} size="sm">
                {r.s}
              </Badge>
            </div>
          </div>
        ))}
      </div>
      <p className="mt-2.5 text-[12px] text-ink-400">
        This preview uses your current settings. Nothing here is real patient data.
      </p>
    </div>
  );
}

export function Settings() {
  const { role, toast } = useApp();
  const { prefs, setPref, reset } = usePreferences();

  // Only offer landing screens this role can actually open — otherwise a
  // staff member could pin themselves to a permission-denied screen.
  const startScreenOptions = role ? navForRole(role) : [];

  return (
    <div className="screen-enter mx-auto max-w-[1000px] space-y-5 p-4 sm:p-6 lg:p-8">
      <SectionTitle
        eyebrow="Preferences"
        title="User Interface"
        description="Change how this system looks and behaves for you. These settings apply to your account on this device only — they do not affect your colleagues or any clinical record."
        action={
          <Button
            icon={<RotateCcw className="h-4 w-4" />}
            onClick={() => {
              reset();
              toast({ title: 'Settings reset', body: 'Interface preferences are back to their defaults.', tone: 'info' });
            }}
          >
            Reset to defaults
          </Button>
        }
      />

      <div className="grid gap-5 lg:grid-cols-[1fr_340px]">
        <div className="space-y-5">
          {/* ---------------- READABILITY ---------------- */}
          <Card className="overflow-hidden">
            <CardHeader
              icon={<Eye className="h-4 w-4" />}
              title="Readability"
              subtitle="Make text and content easier to read"
            />
            <SettingRow
              icon={<Type className="h-4 w-4" />}
              title="Text size"
              description="Increases the size of everything on screen. Useful on tablets and larger displays."
              control={
                <SegmentedControl<TextScale>
                  label="Text size"
                  value={prefs.textScale}
                  onChange={(v) => setPref('textScale', v)}
                  options={[
                    { id: 'standard', label: 'Standard' },
                    { id: 'large', label: 'Large' },
                    { id: 'xl', label: 'Extra large' },
                  ]}
                />
              }
            />
            <SettingRow
              icon={<Rows className="h-4 w-4" />}
              title="Display density"
              description="Compact fits more rows on screen for scanning long lists. Comfortable leaves more breathing room."
              control={
                <SegmentedControl<Density>
                  label="Display density"
                  value={prefs.density}
                  onChange={(v) => setPref('density', v)}
                  options={[
                    { id: 'comfortable', label: 'Comfortable' },
                    { id: 'compact', label: 'Compact' },
                  ]}
                />
              }
            />
            <SettingRow
              icon={<Contrast className="h-4 w-4" />}
              title="High contrast"
              description="Darkens text and strengthens borders for bright clinic lighting or washed-out screens."
              control={
                <Switch
                  label="High contrast"
                  checked={prefs.highContrast}
                  onChange={(v) => setPref('highContrast', v)}
                />
              }
            />
            <SettingRow
              icon={<Zap className="h-4 w-4" />}
              title="Reduce motion"
              description="Turns off sliding and fading animations. Screens change instantly instead."
              control={
                <Switch
                  label="Reduce motion"
                  checked={prefs.reduceMotion}
                  onChange={(v) => setPref('reduceMotion', v)}
                />
              }
            />
          </Card>

          {/* ---------------- LAYOUT ---------------- */}
          <Card className="overflow-hidden">
            <CardHeader
              icon={<Monitor className="h-4 w-4" />}
              title="Layout & navigation"
              subtitle="Control what the menu and top bar show"
            />
            <SettingRow
              icon={<PanelLeft className="h-4 w-4" />}
              title="Menu sections"
              description="Keep every section of the left menu open, or show only the section you are currently working in."
              control={
                <SegmentedControl<SidebarSections>
                  label="Menu sections"
                  value={prefs.sidebarSections}
                  onChange={(v) => setPref('sidebarSections', v)}
                  options={[
                    { id: 'active-only', label: 'Current only' },
                    { id: 'all-open', label: 'All open' },
                  ]}
                />
              }
            />
            <SettingRow
              icon={<Clock className="h-4 w-4" />}
              title="Show date and time"
              description="Adds the date and a live clock to the top bar. Off by default to keep the bar uncluttered."
              control={
                <Switch
                  label="Show date and time"
                  checked={prefs.showClock}
                  onChange={(v) => setPref('showClock', v)}
                />
              }
            />
            <SettingRow
              icon={<LogIn className="h-4 w-4" />}
              title="Screen after sign-in"
              description="Choose which screen opens when you sign in, instead of the default for your role."
              control={
                <div className="w-full sm:w-[220px]">
                  <Select
                    aria-label="Screen after sign-in"
                    value={prefs.startScreen}
                    onChange={(e) => setPref('startScreen', e.target.value)}
                  >
                    <option value="role-default">Default for my role</option>
                    {startScreenOptions.map((n) => (
                      <option key={n.id} value={n.id}>
                        {SCREEN_TITLES[n.id]}
                      </option>
                    ))}
                  </Select>
                </div>
              }
            />
          </Card>

          <InfoNote tone="brand" icon={<Monitor className="h-4 w-4" />}>
            These preferences are stored in this browser. Signing in on a different computer or
            tablet starts from the defaults again, and clearing browser data resets them.
          </InfoNote>
        </div>

        {/* ---------------- PREVIEW ---------------- */}
        <div className="lg:sticky lg:top-6 lg:self-start">
          <Card className="p-4">
            <p className="mb-3 text-[12px] font-semibold uppercase tracking-[0.09em] text-ink-400">
              Live preview
            </p>
            <LivePreview />
          </Card>
        </div>
      </div>
    </div>
  );
}
