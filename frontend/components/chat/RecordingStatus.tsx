"use client";

import { useEffect, useRef, useState } from "react";

const heights = [9, 15, 22, 28, 21, 15, 9];

export default function RecordingStatus({ recording, stream }: { recording: boolean; stream: MediaStream | null }) {
  const [seconds, setSeconds] = useState(0);
  const bars = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!recording) return;
    const started = Date.now();
    const timer = window.setInterval(() => setSeconds(Math.floor((Date.now() - started) / 1000)), 250);
    return () => window.clearInterval(timer);
  }, [recording]);

  useEffect(() => {
    if (!recording || !stream || !bars.current || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const context = new AudioContext();
    const source = context.createMediaStreamSource(stream);
    const analyser = context.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    const samples = new Uint8Array(analyser.frequencyBinCount);
    const elements = Array.from(bars.current.children) as HTMLElement[];
    let frame = 0;
    function draw() {
      analyser.getByteFrequencyData(samples);
      elements.forEach((element, index) => {
        const level = samples[index * 3] / 255;
        element.style.transform = `scaleY(${0.25 + 0.75 * level})`;
      });
      frame = requestAnimationFrame(draw);
    }
    draw();
    return () => {
      cancelAnimationFrame(frame);
      source.disconnect();
      void context.close();
    };
  }, [recording, stream]);

  return (
    <div className="study-enter flex h-10 shrink-0 items-center gap-2 border-r border-line pr-2 text-xs sm:pr-3">
      {recording && <span ref={bars} aria-hidden className="flex h-7 items-center gap-[3px] text-[#657354] dark:text-[#b5c0a4]">
        {heights.map((height, index) => <span key={index} className={`w-[3px] rounded-full bg-current ${stream ? "" : "listening-bar"}`}
          style={{ height, animationDelay: `${index * -85}ms` }} />)}
      </span>}
      <span role="status">{recording ? "Listening" : "Transcribing locally…"}</span>
      {recording && <span aria-hidden className="hidden text-xs sm:inline tabular-nums text-neutral-600 dark:text-neutral-300">
        {Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, "0")}
      </span>}
    </div>
  );
}
