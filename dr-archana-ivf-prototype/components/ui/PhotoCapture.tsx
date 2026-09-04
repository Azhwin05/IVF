'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Camera, Upload, RotateCcw, X, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

const MAX_BYTES = 8 * 1024 * 1024; // 8 MB — comfortably under the API's 25 MB cap
const ACCEPTED = ['image/jpeg', 'image/png', 'image/webp'];

type Props = {
  /** Stable id prefix for the control's inputs/labels (must be unique per person). */
  idPrefix: string;
  /** Visible label, e.g. "Patient Photo" or "Partner Photo". */
  label: string;
  /** Currently selected image, or null. Owned by the parent so it survives step nav. */
  value: File | null;
  onChange: (file: File | null) => void;
};

/**
 * One self-contained photo control: live camera capture where the browser
 * allows it, or a file upload fallback. Preview + retake + remove. The camera
 * stream is always stopped on capture, cancel, and unmount so the device light
 * never stays on. Two of these are rendered in the couple wizard — one per
 * person — and each only ever calls its own `onChange`, so a patient photo can
 * never be attached to the partner or vice versa.
 */
export function PhotoCapture({ idPrefix, label, value, onChange }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [mode, setMode] = useState<'idle' | 'camera'>('idle');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
  }, []);

  // Keep an object URL for the current file; revoke it when it changes/unmounts.
  useEffect(() => {
    if (!value) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(value);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [value]);

  useEffect(() => stopCamera, [stopCamera]);

  const startCamera = useCallback(async () => {
    setError(null);
    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
      setError('Camera is not available on this device — upload a photo instead.');
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user' },
        audio: false,
      });
      streamRef.current = stream;
      setMode('camera');
      // videoRef is mounted by the render below; attach on the next tick.
      requestAnimationFrame(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch(() => undefined);
        }
      });
    } catch {
      setError('Camera permission was denied — upload a photo instead.');
      stopCamera();
      setMode('idle');
    }
  }, [stopCamera]);

  const capture = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setError('Could not capture the photo — try again or upload one.');
          return;
        }
        const file = new File([blob], `${idPrefix}-photo.jpg`, { type: 'image/jpeg' });
        stopCamera();
        setMode('idle');
        onChange(file);
      },
      'image/jpeg',
      0.9,
    );
  }, [idPrefix, onChange, stopCamera]);

  const cancelCamera = useCallback(() => {
    stopCamera();
    setMode('idle');
  }, [stopCamera]);

  const onFile = useCallback(
    (file: File | undefined) => {
      setError(null);
      if (!file) return;
      if (!ACCEPTED.includes(file.type)) {
        setError('Use a JPEG, PNG or WebP image.');
        return;
      }
      if (file.size > MAX_BYTES) {
        setError('That image is over 8 MB — choose a smaller one.');
        return;
      }
      onChange(file);
    },
    [onChange],
  );

  const headingId = `${idPrefix}-photo-heading`;

  return (
    <section aria-labelledby={headingId} className="rounded-xl border border-ink-200 bg-white p-4">
      <p id={headingId} className="mb-3 text-[13.5px] font-semibold text-ink-900">
        {label}
      </p>

      {value && previewUrl ? (
        <div className="flex items-start gap-4">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={previewUrl}
            alt={`${label} preview`}
            className="h-28 w-28 rounded-xl object-cover ring-1 ring-ink-200"
          />
          <div className="flex flex-col gap-2">
            <span className="inline-flex items-center gap-1.5 text-[12.5px] font-medium text-emerald-700">
              <Check className="h-3.5 w-3.5" /> Photo ready
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => { onChange(null); startCamera(); }}
                className="inline-flex min-h-[44px] items-center gap-1.5 rounded-lg border border-ink-200 px-3 text-[13px] font-medium text-ink-700 hover:border-brand-400 hover:text-brand-700"
              >
                <RotateCcw className="h-3.5 w-3.5" /> Retake
              </button>
              <button
                type="button"
                onClick={() => onChange(null)}
                className="inline-flex min-h-[44px] items-center gap-1.5 rounded-lg border border-ink-200 px-3 text-[13px] font-medium text-ink-700 hover:border-rose-300 hover:text-rose-700"
              >
                <X className="h-3.5 w-3.5" /> Remove
              </button>
            </div>
          </div>
        </div>
      ) : mode === 'camera' ? (
        <div className="space-y-3">
          <video
            ref={videoRef}
            playsInline
            muted
            aria-label={`${label} camera preview`}
            className="aspect-[4/3] w-full max-w-sm rounded-xl bg-ink-900 object-cover"
          />
          <div className="flex gap-2">
            <button
              type="button"
              onClick={capture}
              className="inline-flex min-h-[44px] items-center gap-1.5 rounded-lg bg-brand-600 px-4 text-[13px] font-semibold text-white hover:bg-brand-700"
            >
              <Camera className="h-4 w-4" /> Capture
            </button>
            <button
              type="button"
              onClick={cancelCamera}
              className="inline-flex min-h-[44px] items-center gap-1.5 rounded-lg border border-ink-200 px-4 text-[13px] font-medium text-ink-700 hover:border-ink-300"
            >
              <X className="h-4 w-4" /> Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={startCamera}
            className="inline-flex min-h-[44px] items-center gap-1.5 rounded-lg border border-ink-200 px-4 text-[13px] font-medium text-ink-700 hover:border-brand-400 hover:text-brand-700"
          >
            <Camera className="h-4 w-4" /> Use camera
          </button>
          <label
            className={cn(
              'inline-flex min-h-[44px] cursor-pointer items-center gap-1.5 rounded-lg border border-ink-200 px-4 text-[13px] font-medium text-ink-700',
              'hover:border-brand-400 hover:text-brand-700',
            )}
          >
            <Upload className="h-4 w-4" /> Upload photo
            <input
              type="file"
              accept={ACCEPTED.join(',')}
              className="hidden"
              onChange={(e) => onFile(e.target.files?.[0])}
            />
          </label>
        </div>
      )}

      {error && (
        <p role="alert" className="mt-2.5 text-[12.5px] text-rose-700">
          {error}
        </p>
      )}
    </section>
  );
}
