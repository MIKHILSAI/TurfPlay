"use client";

import { Mic, MicOff, Loader2 } from "lucide-react";

export function VoiceButton({
  recording,
  transcribing,
  onStart,
  onStop,
}: {
  recording: boolean;
  transcribing: boolean;
  onStart: () => void;
  onStop: () => void;
}) {
  if (transcribing) {
    return (
      <button disabled className="p-2 rounded-full bg-muted">
        <Loader2 className="h-5 w-5 animate-spin" />
      </button>
    );
  }

  return (
    <button
      onClick={recording ? onStop : onStart}
      className={`p-2 rounded-full transition ${
        recording
          ? "bg-red-500 text-white animate-pulse"
          : "bg-muted hover:bg-muted/80"
      }`}
      aria-label={recording ? "Stop recording" : "Start recording"}
    >
      {recording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
    </button>
  );
}