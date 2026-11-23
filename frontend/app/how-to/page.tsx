import InfoPage from "@/components/setup/InfoPage";

export const metadata = { title: "How to | StudyMate" };
export default function HowToPage() {
  return (
    <InfoPage title="How to" summary="Follow a walkthrough and open its example to see the result.">
      <section>
        <h2>Draw a flowchart in chat</h2>
        <ol className="list-decimal space-y-2 pl-5">
          <li>Open a course and ask the tutor directly. Try <em>“Draw a flowchart showing how a Python web framework handles a request, from the browser to the router, view, and response.”</em> You can start without uploading notes.</li>
          <li>The drawing appears in the reply. Choose <strong>Save diagram</strong> to keep it in the course.</li>
          <li>Open <strong>Materials → Created</strong> and select the diagram. Choose <strong>SVG</strong> for a scalable drawing or <strong>PNG</strong> for an image you can paste into an assignment.</li>
        </ol>
        <p className="mt-3">If the preview fails, try asking for a simpler drawing with four steps and short labels. If you know Mermaid, you can also use <strong>Edit Mermaid → Preview diagram</strong> in the reply.</p>
        <details className="tutorial-example mt-3"><summary className="cursor-pointer text-accent">See example</summary><img className="mt-2 w-full rounded-control" loading="lazy" src="/how-to/course-chat.png" alt="Flowchart displayed in a course chat" /></details>
      </section>
      <section>
        <h2>Make a diagram from your notes</h2>
        <p>In <strong>Materials</strong>, tick the checkbox beside a <strong>Ready</strong> file and choose <strong>Diagram from source</strong>. Choose <strong>Flowchart</strong> to show steps and decisions, or <strong>Sequence diagram</strong> to show who sends what to whom. You can narrow the topic before choosing <strong>Generate diagram</strong>.</p>
        <details className="tutorial-example mt-3"><summary className="cursor-pointer text-accent">See example</summary><img className="mt-2 w-full rounded-control" loading="lazy" src="/how-to/diagram-editor.png" alt="Sequence diagram with export controls" /></details>
      </section>
      <section>
        <h2>Create and review flashcards or a quiz</h2>
        <ol className="list-decimal space-y-2 pl-5">
          <li>In <strong>Materials</strong>, tick one or more <strong>Ready</strong> files, then choose <strong>Create study items</strong>. You can also choose <strong>Study items</strong> beneath a tutor reply that cites your notes.</li>
          <li>Choose <strong>Flashcards</strong> or <strong>Multiple-choice quiz</strong>, then <strong>Generate</strong>.</li>
          <li>For a card, recall the answer first, then choose <strong>Show answer</strong> and mark <strong>Again</strong> or <strong>Remembered</strong>. For a quiz, select an answer to see feedback.</li>
        </ol>
        <p className="mt-3">Return to <strong>Materials → Created → Flashcards and quizzes</strong> to find your items. <strong>Study overview → Flashcards due today</strong> shows which courses have cards ready for review.</p>
        <details className="tutorial-example mt-3"><summary className="cursor-pointer text-accent">See example</summary><img className="mt-2 w-full rounded-control" loading="lazy" src="/how-to/flashcard-review.png" alt="Flashcard answer and recall controls" /></details>
      </section>
    </InfoPage>
  );
}
