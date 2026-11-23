import type { Metadata } from "next";
import Link from "next/link";
import InfoPage from "@/components/setup/InfoPage";

export const metadata: Metadata = { title: "Help · StudyMate" };

export default function HelpPage() {
  return (
    <InfoPage title="Help" summary="Start a course, draw a process in chat, or turn your notes into practice questions.">
      <section>
        <h2>Start a study session</h2>
        <p>In the workspace, select <strong>New course</strong>, give it a name, and choose a subject profile.
          Open the course to start chatting. Resume previous sessions from <strong>Study overview</strong>.</p>
      </section>
      <section>
        <h2>Set up the local tutor</h2>
        <p>Open your profile in the left sidebar, then go to <strong>Local setup</strong>. Choose
          <strong> Download &amp; use</strong> beside a tutor model. StudyMate can set up Ollama on supported devices.
          Once the runtime and model are installed, you can generate replies offline.</p>
        <p className="mt-2"><Link href="/settings?section=setup">Open Local setup</Link></p>
      </section>
      <section>
        <h2>Add PDFs and notes</h2>
        <p>Open the Materials panel and drop in files or browse for them. Wait until a file shows
          <strong> Ready</strong> before asking the tutor about it. If processing fails, check the message beside
          the file and use <strong>Retry processing</strong>. Scanned PDFs may need Tesseract or a searchable copy.</p>
      </section>
      <section><h2>Study tools</h2><Link href="/how-to">How to create diagrams, flashcards, and quizzes</Link></section>
      <section>
        <h2>Dictate a question</h2>
        <p>Allow the browser to use your microphone when prompted. If on-device browser recognition is unavailable,
          check <strong>Voice input</strong> in Local setup for the optional Whisper model.</p>
      </section>
      <section>
        <h2>Report a problem</h2>
        <p>Include your operating system, what you were doing, and the error message. Leave personal notes and chats
          out of the report.</p>
        <p className="mt-2"><a href="https://github.com/Shaswata28/StudyMate/issues" target="_blank" rel="noreferrer">StudyMate issues on GitHub</a></p>
      </section>
    </InfoPage>
  );
}
