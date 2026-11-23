async function fetchAudio(text: string, signal: AbortSignal) {
  const response = await fetch("/api/speech", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
    signal,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(typeof payload.detail === "string" ? payload.detail : "Kokoro could not play this text.");
  }
  return response.blob();
}

export async function playKokoro(text: string, signal: AbortSignal, onPlaying?: () => void) {
  const chunks = (text.match(/[\s\S]{1,160}(?:[.!?](?=\s|$)|$)|[\s\S]{1,159}(?:\s|$)|[\s\S]{1,160}/gu) ?? [])
    .map((chunk) => chunk.trim())
    .filter(Boolean);
  const player = new Audio();
  // Keep one clip in reserve so synthesis can overlap playback.
  const prepare = (chunk: string) => fetchAudio(chunk, signal).then(
    (audio) => ({ audio }),
    (error: unknown) => ({ error }),
  );
  let pending = chunks.length ? prepare(chunks[0]) : undefined;
  for (let index = 0; index < chunks.length; index++) {
    if (signal.aborted || !pending) return;
    const clip = await pending;
    if (signal.aborted) return;
    if ("error" in clip) throw clip.error;
    const url = URL.createObjectURL(clip.audio);
    let stop = () => {};
    try {
      player.src = url;
      await new Promise<void>((resolve, reject) => {
        stop = () => { player.pause(); resolve(); };
        signal.addEventListener("abort", stop, { once: true });
        player.onended = () => resolve();
        player.onerror = () => reject(new Error("Could not play Kokoro audio."));
        player.play().then(() => {
          if (signal.aborted) return;
          onPlaying?.();
          pending = index + 1 < chunks.length ? prepare(chunks[index + 1]) : undefined;
        }).catch(reject);
      });
    } finally {
      signal.removeEventListener("abort", stop);
      URL.revokeObjectURL(url);
    }
  }
}
