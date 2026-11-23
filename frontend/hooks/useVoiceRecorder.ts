"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";

async function toWav(recording: Blob) {
  const context = new AudioContext();
  try {
    const audio = await context.decodeAudioData(await recording.arrayBuffer());
    const resampler = new OfflineAudioContext(1, Math.max(1, Math.ceil(audio.duration * 16000)), 16000);
    const source = resampler.createBufferSource();
    source.buffer = audio;
    source.connect(resampler.destination);
    source.start();
    const samples = (await resampler.startRendering()).getChannelData(0);
    const wav = new DataView(new ArrayBuffer(44 + samples.length * 2));
    for (const [offset, label] of [[0, "RIFF"], [8, "WAVEfmt "], [36, "data"]] as const) {
      for (let index = 0; index < label.length; index++) wav.setUint8(offset + index, label.charCodeAt(index));
    }
    wav.setUint32(4, wav.byteLength - 8, true);
    wav.setUint32(16, 16, true);
    wav.setUint16(20, 1, true);
    wav.setUint16(22, 1, true);
    wav.setUint32(24, 16000, true);
    wav.setUint32(28, 32000, true);
    wav.setUint16(32, 2, true);
    wav.setUint16(34, 16, true);
    wav.setUint32(40, samples.length * 2, true);
    samples.forEach((sample, index) => wav.setInt16(44 + index * 2, Math.max(-1, Math.min(1, sample)) * 32767, true));
    return new Blob([wav.buffer], { type: "audio/wav" });
  } finally {
    await context.close();
  }
}

export function useVoiceRecorder(onTranscript: (text: string) => void, whisperAvailable: boolean) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingStream, setRecordingStream] = useState<MediaStream | null>(null);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [preview, setPreview] = useState("");
  const discarded = useRef(false);
  const sendOnComplete = useRef<((text: string) => void) | null>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const recognition = useRef<any>(null);
  const starting = useRef(false);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      recognition.current?.abort();
      if (recorder.current?.state === "recording") recorder.current.stop();
    };
  }, []);

  function complete(transcript: string) {
    const send = sendOnComplete.current;
    sendOnComplete.current = null;
    setPreview("");
    if (!mounted.current || discarded.current) return;
    if (transcript) (send ?? onTranscript)(transcript);
    else if (send) toast.error("No speech detected.");
  }

  function finishRecording(send?: (text: string) => void) {
    if (!isRecording || sendOnComplete.current || (!recorder.current && !recognition.current)) return;
    sendOnComplete.current = send ?? null;
    setIsRecording(false);
    setIsTranscribing(true);
    if (recorder.current?.state === "recording") recorder.current.stop();
    else recognition.current?.stop();
  }

  function discardRecording() {
    discarded.current = true;
    sendOnComplete.current = null;
    setPreview("");
    if (recorder.current?.state === "recording") recorder.current.stop();
    recognition.current?.abort();
    setIsRecording(false);
  }

  async function startWhisper() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    if (!mounted.current) {
      stream.getTracks().forEach((track) => track.stop());
      return;
    }
    let session;
    try {
      session = new MediaRecorder(stream);
      session.start();
    } catch (error) {
      stream.getTracks().forEach((track) => track.stop());
      throw error;
    }
    recorder.current = session;
    setRecordingStream(stream);
    setIsRecording(true);
    const chunks: Blob[] = [];
    const stop = () => { if (session.state === "recording") session.stop(); };
    const timer = window.setTimeout(stop, 55_000);
    session.ondataavailable = (event) => { if (event.data.size) chunks.push(event.data); };
    session.onstop = async () => {
      clearTimeout(timer);
      stream.getTracks().forEach((track) => track.stop());
      recorder.current = null;
      if (!mounted.current) return;
      setIsRecording(false);
      setRecordingStream(null);
      if (discarded.current) return;
      setIsTranscribing(true);
      try {
        const wave = await toWav(new Blob(chunks, { type: session.mimeType }));
        const result = await api.transcribe(wave);
        complete(result.text);
      } catch (error) {
        sendOnComplete.current = null;
        if (mounted.current && !discarded.current) toast.error(error instanceof Error ? error.message : "Could not transcribe the recording.");
      } finally {
        if (mounted.current) setIsTranscribing(false);
      }
    };
  }

  async function startRecording() {
    if (recorder.current || recognition.current) return;
    if (starting.current || isTranscribing) return;

    const speech = window as typeof window & { SpeechRecognition?: any; webkitSpeechRecognition?: any };
    const SpeechRecognition = speech.SpeechRecognition ?? speech.webkitSpeechRecognition;

    starting.current = true;
    discarded.current = false;
    const options = { langs: ["en-US"], processLocally: true };
    try {
      if (whisperAvailable) {
        await startWhisper();
        return;
      }
      if (!SpeechRecognition?.available || !("processLocally" in SpeechRecognition.prototype)) {
        toast.error("On-device dictation is unavailable. See voice setup in Settings.");
        return;
      }
      let status = await SpeechRecognition.available(options);
      if (status === "downloadable") {
        toast.info("Downloading the English voice input pack...");
        if (await SpeechRecognition.install(options)) status = "available";
      }
      if (status !== "available") {
        toast.error("The English on-device voice input pack is unavailable.");
        return;
      }
      if (!mounted.current) return;

      const session = new SpeechRecognition();
      session.lang = "en-US";
      session.processLocally = true;
      session.continuous = true;
      session.interimResults = true;
      let finalText = "";
      session.onresult = (event: any) => {
        const results = Array.from(event.results) as { isFinal: boolean; 0: { transcript: string } }[];
        finalText = results.filter((result) => result.isFinal).map((result) => result[0].transcript).join(" ").trim();
        if (!discarded.current) setPreview(results.map((result) => result[0].transcript).join(" ").trim());
      };
      session.onerror = () => {
        sendOnComplete.current = null;
        if (mounted.current && !discarded.current) toast.error("Voice input stopped. Check microphone access and try again.");
      };
      session.onend = () => {
        recognition.current = null;
        if (!mounted.current) return;
        setIsRecording(false);
        setIsTranscribing(false);
        complete(finalText);
      };
      session.start();
      recognition.current = session;
      setIsRecording(true);
    } catch {
      toast.error("Could not start on-device voice input.");
    } finally {
      starting.current = false;
    }
  }

  return { isRecording, isTranscribing, recordingStream, preview, startRecording, finishRecording, discardRecording };
}
