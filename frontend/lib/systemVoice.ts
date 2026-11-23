export type VoiceMode = "system" | "chrome" | "kokoro";

const voicePreference = "studymate-read-aloud-voice";

export function getVoiceMode(): VoiceMode {
  const mode = window.localStorage.getItem(voicePreference);
  return mode === "chrome" || mode === "kokoro" ? mode : "system";
}

export function setVoiceMode(mode: VoiceMode) {
  window.localStorage.setItem(voicePreference, mode);
}

export function findEnglishVoice(engine: SpeechSynthesis | undefined, mode: VoiceMode) {
  if (mode === "kokoro") return undefined;
  return engine?.getVoices().find((voice) =>
    /^en(?:[-_]|$)/i.test(voice.lang) &&
    (mode === "system" ? voice.localService : !voice.localService && /^Google\b/i.test(voice.name)),
  );
}
