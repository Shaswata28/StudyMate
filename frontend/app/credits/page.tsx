import type { Metadata } from "next";
import { ArrowUpRight, Github } from "lucide-react";
import InfoPage from "@/components/setup/InfoPage";

export const metadata: Metadata = { title: "Credits ? StudyMate" };

export default function CreditsPage() {
  return (
    <InfoPage title="Credits" summary="The people and tools behind StudyMate.">
      <section>
        <h2>Project maintainer</h2>
        <a href="https://github.com/Shaswata28" target="_blank" rel="noreferrer"
          className="mt-3 inline-flex items-center gap-3 rounded-control border border-line bg-background px-4 py-3">
          <Github aria-hidden className="size-5 shrink-0" />
          <span><span className="block font-semibold">Shaswata Das</span><span className="block text-xs">@Shaswata28</span></span>
          <ArrowUpRight aria-hidden className="size-4" />
        </a>
      </section>
      <section>
        <h2>Contributors</h2>
        <p>See the <a href="https://github.com/Shaswata28/StudyMate/graphs/contributors" target="_blank" rel="noreferrer">contributor history</a> and
          the <a href="https://github.com/Shaswata28/StudyMate" target="_blank" rel="noreferrer">StudyMate repository</a> on GitHub.</p>
      </section>
      <section>
        <h2>Project tools</h2>
        <p>StudyMate uses FastAPI and SQLite for local storage and services, Next.js for the browser interface,
          Ollama for local inference, PyMuPDF for PDF extraction, and Whisper for optional dictation.
          Instrument Serif and Instrument Sans are bundled with their font licenses.</p>
      </section>
    </InfoPage>
  );
}
