import { useNavigate } from "react-router-dom";
import { ArrowLeft, FileText } from "lucide-react";

export default function TermsAndConditions() {
  const navigate = useNavigate();

  const handleBack = () => {
    navigate(-1);
  };

  return (
    <div className="min-h-screen w-full bg-white dark:bg-slate-950 transition-colors duration-200">
      {/* Header */}
      <header className="h-[70px] px-6 md:px-8 lg:pl-8 lg:pr-12 flex items-center justify-between border-b border-black/10 dark:border-slate-700 bg-white dark:bg-slate-950 sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <button
            onClick={handleBack}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors btn-micro"
            aria-label="Go back"
          >
            <ArrowLeft className="w-5 h-5 sm:w-6 sm:h-6 text-black dark:text-white" strokeWidth={2} />
          </button>
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 sm:w-6 sm:h-6 text-studymate-orange dark:text-studymate-green" strokeWidth={2} />
            <h1 className="font-koulen text-3xl md:text-4xl lg:text-[32px] tracking-[3.2px] text-black dark:text-white hidden sm:block">
              TERMS & CONDITIONS
            </h1>
            <h1 className="font-koulen text-2xl tracking-[2.4px] text-black dark:text-white block sm:hidden">
              T&C
            </h1>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8 lg:px-12 py-8 md:py-12">
        <div className="space-y-8">
          {/* Last Updated */}
          <div className="bg-gray-50 dark:bg-slate-800 rounded-lg p-4 sm:p-6 border border-gray-200 dark:border-slate-700">
            <p className="font-roboto text-sm text-gray-600 dark:text-gray-400">
              <strong>Last Updated:</strong> January 2024
            </p>
          </div>

          {/* Section 1 - Introduction */}
          <section className="space-y-4">
            <h2 className="font-audiowide text-2xl sm:text-3xl tracking-[1.2px] sm:tracking-[1.5px] text-black dark:text-white flex items-center gap-2">
              <span className="text-studymate-orange dark:text-studymate-green text-3xl">1.</span>
              Introduction
            </h2>
            <p className="font-roboto text-sm sm:text-base leading-relaxed text-[#201F1F] dark:text-gray-300">
              Welcome to StudyMate ("we", "us", "our", or "Company"). StudyMate is an AI-powered educational platform designed to support your learning journey. These Terms and Conditions ("Terms") govern your use of our website and services. By accessing or using StudyMate, you agree to be bound by these Terms.
            </p>
          </section>

          {/* Section 2 - User Responsibilities */}
          <section className="space-y-4">
            <h2 className="font-audiowide text-2xl sm:text-3xl tracking-[1.2px] sm:tracking-[1.5px] text-black dark:text-white flex items-center gap-2">
              <span className="text-studymate-orange dark:text-studymate-green text-3xl">2.</span>
              User Responsibilities
            </h2>
            <div className="space-y-3">
              <p className="font-roboto text-sm sm:text-base leading-relaxed text-[#201F1F] dark:text-gray-300">
                As a user of StudyMate, you agree to:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-2">
                <li className="font-roboto text-sm sm:text-base text-[#201F1F] dark:text-gray-300">
                  Provide accurate and complete information during registration
                </li>
                <li className="font-roboto text-sm sm:text-base text-[#201F1F] dark:text-gray-300">
                  Maintain the confidentiality of your account credentials
                </li>
                <li className="font-roboto text-sm sm:text-base text-[#201F1F] dark:text-gray-300">
                  Use the service only for lawful purposes
                </li>
                <li className="font-roboto text-sm sm:text-base text-[#201F1F] dark:text-gray-300">
                  Not engage in any form of harassment, abuse, or discriminatory behavior
                </li>
              </ul>
            </div>
          </section>

          {/* Section 3 - Intellectual Property */}
          <section className="space-y-4">
            <h2 className="font-audiowide text-2xl sm:text-3xl tracking-[1.2px] sm:tracking-[1.5px] text-black dark:text-white flex items-center gap-2">
              <span className="text-studymate-orange dark:text-studymate-green text-3xl">3.</span>
              Intellectual Property Rights
            </h2>
            <p className="font-roboto text-sm sm:text-base leading-relaxed text-[#201F1F] dark:text-gray-300">
              All content, features, and functionality of StudyMate, including but not limited to text, graphics, logos, images, and software, are the exclusive property of StudyMate or its content suppliers and are protected by international copyright, trademark, and other intellectual property laws.
            </p>
            <p className="font-roboto text-sm sm:text-base leading-relaxed text-[#201F1F] dark:text-gray-300">
              You are granted a limited, non-exclusive, non-transferable license to use StudyMate for your personal, educational purposes only. Reproduction, modification, or distribution of any content without permission is strictly prohibited.
            </p>
          </section>

          {/* Section 4 - Limitation of Liability */}
          <section className="space-y-4">
            <h2 className="font-audiowide text-2xl sm:text-3xl tracking-[1.2px] sm:tracking-[1.5px] text-black dark:text-white flex items-center gap-2">
              <span className="text-studymate-orange dark:text-studymate-green text-3xl">4.</span>
              Limitation of Liability
            </h2>
            <p className="font-roboto text-sm sm:text-base leading-relaxed text-[#201F1F] dark:text-gray-300">
              To the fullest extent permitted by law, StudyMate shall not be liable for any indirect, incidental, special, consequential, or punitive damages, including but not limited to loss of profits, data, or use, arising from or connected with your use of the service.
            </p>
            <p className="font-roboto text-sm sm:text-base leading-relaxed text-[#201F1F] dark:text-gray-300">
              StudyMate provides the service "as is" without warranties of any kind, either express or implied.
            </p>
          </section>

          {/* Section 5 - User Content */}
          <section className="space-y-4">
            <h2 className="font-audiowide text-2xl sm:text-3xl tracking-[1.2px] sm:tracking-[1.5px] text-black dark:text-white flex items-center gap-2">
              <span className="text-studymate-orange dark:text-studymate-green text-3xl">5.</span>
              User-Generated Content
            </h2>
            <p className="font-roboto text-sm sm:text-base leading-relaxed text-[#201F1F] dark:text-gray-300">
              Any content you submit, upload, or create on StudyMate remains your intellectual property. However, by using our service, you grant StudyMate a worldwide, non-exclusive, royalty-free license to use, reproduce, and distribute your content as necessary to provide and improve our services.
            </p>
          </section>

          {/* Section 6 - Account Termination */}
          <section className="space-y-4">
            <h2 className="font-audiowide text-2xl sm:text-3xl tracking-[1.2px] sm:tracking-[1.5px] text-black dark:text-white flex items-center gap-2">
              <span className="text-studymate-orange dark:text-studymate-green text-3xl">6.</span>
              Account Termination
            </h2>
            <p className="font-roboto text-sm sm:text-base leading-relaxed text-[#201F1F] dark:text-gray-300">
              StudyMate reserves the right to suspend or terminate your account at any time if you violate these Terms or engage in any prohibited conduct. Upon termination, your access to the service will be immediately revoked.
            </p>
          </section>

          {/* Section 7 - Changes to Terms */}
          <section className="space-y-4">
            <h2 className="font-audiowide text-2xl sm:text-3xl tracking-[1.2px] sm:tracking-[1.5px] text-black dark:text-white flex items-center gap-2">
              <span className="text-studymate-orange dark:text-studymate-green text-3xl">7.</span>
              Modifications to Terms
            </h2>
            <p className="font-roboto text-sm sm:text-base leading-relaxed text-[#201F1F] dark:text-gray-300">
              StudyMate may modify these Terms at any time. Changes will be effective immediately upon posting to the website. Your continued use of the service after any modifications constitutes your acceptance of the new Terms.
            </p>
          </section>

          {/* Section 8 - Governing Law */}
          <section className="space-y-4">
            <h2 className="font-audiowide text-2xl sm:text-3xl tracking-[1.2px] sm:tracking-[1.5px] text-black dark:text-white flex items-center gap-2">
              <span className="text-studymate-orange dark:text-studymate-green text-3xl">8.</span>
              Governing Law
            </h2>
            <p className="font-roboto text-sm sm:text-base leading-relaxed text-[#201F1F] dark:text-gray-300">
              These Terms and your use of StudyMate are governed by and construed in accordance with the laws of the jurisdiction in which StudyMate operates, without regard to its conflict of law provisions.
            </p>
          </section>

          {/* Section 9 - Contact Us */}
          <section className="space-y-4">
            <h2 className="font-audiowide text-2xl sm:text-3xl tracking-[1.2px] sm:tracking-[1.5px] text-black dark:text-white flex items-center gap-2">
              <span className="text-studymate-orange dark:text-studymate-green text-3xl">9.</span>
              Contact Us
            </h2>
            <p className="font-roboto text-sm sm:text-base leading-relaxed text-[#201F1F] dark:text-gray-300">
              If you have any questions about these Terms and Conditions, please contact us at:
            </p>
            <div className="bg-gray-50 dark:bg-slate-800 rounded-lg p-4 space-y-2 border border-gray-200 dark:border-slate-700">
              <p className="font-roboto text-sm font-semibold text-[#201F1F] dark:text-white">StudyMate Support</p>
              <p className="font-roboto text-sm text-[#201F1F] dark:text-gray-300">Email: support@studymate.com</p>
              <p className="font-roboto text-sm text-[#201F1F] dark:text-gray-300">Website: www.studymate.com</p>
            </div>
          </section>

          {/* Bottom CTA */}
          <div className="bg-studymate-orange/10 dark:bg-studymate-green/10 rounded-lg p-6 border border-studymate-orange/20 dark:border-studymate-green/20 mt-8">
            <p className="font-roboto text-sm sm:text-base text-[#201F1F] dark:text-gray-300">
              By continuing to use StudyMate, you acknowledge that you have read, understood, and agree to be bound by these Terms and Conditions.
            </p>
          </div>

          {/* Spacing at bottom */}
          <div className="h-8" />
        </div>
      </div>
    </div>
  );
}
