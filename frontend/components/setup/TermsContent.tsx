import InfoPage from "@/components/setup/InfoPage";


export default function TermsContent({ onboarding = false }: { onboarding?: boolean }) {
  return (
    <InfoPage backHref={onboarding ? "/onboarding" : undefined} backLabel={onboarding ? "Back to onboarding" : undefined} title="Terms and conditions" summary="These terms cover your use of the local StudyMate application.">
      <section>
        <h2>Using StudyMate</h2>
        <p>StudyMate is a study aid. Check important answers against course materials and other reliable sources.
          Follow your institution?s academic integrity rules when using or submitting work made with the app.</p>
      </section>
      <section>
        <h2>Materials you add</h2>
        <p>Only add files you have permission to use. Follow any copyright, confidentiality, or course-sharing rules
          that apply to those files.</p>
      </section>
      <section>
        <h2>Local data and backups</h2>
        <p>Your profile, courses, materials, and chats are saved on your device. Keep a backup of anything you want
          to retain. Deleting a course removes its materials, chats, and saved answers from StudyMate.</p>
      </section>
      <section>
        <h2>Downloads and external tools</h2>
        <p>The app may connect to external providers when you download a runtime or model, or open an external link.
          Those downloads and services have their own terms and licenses.</p>
      </section>
    </InfoPage>
  );
}
