import { useState } from "react";
import { X } from "lucide-react";

type TabType = "settings" | "about" | "help";

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ProfileModal({ isOpen, onClose }: ProfileModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>("settings");
  const [expandedFAQ, setExpandedFAQ] = useState<number | null>(0);

  if (!isOpen) return null;

  const faqs = [
    {
      question: "How do I create a new course?",
      answer:
        "Click on 'New Course' in the sidebar to create a new course. You can customize the course name and color to organize your subjects.",
    },
    {
      question: "How can I upload course materials?",
      answer:
        "In the workspace, use the attachment button in the chat input area to upload your PDFs, documents, or other study materials. The materials will be organized in the materials panel.",
    },
    {
      question: "How does StudyMate personalize learning?",
      answer:
        "During signup, you answer questions about your learning preferences. StudyMate uses this information to tailor explanations and study materials to match your style.",
    },
    {
      question: "Can I change my learning preferences later?",
      answer:
        "Yes! You can update your learning preferences anytime in the Settings. StudyMate will also learn from your interactions in the app.",
    },
    {
      question: "How do I organize multiple courses?",
      answer:
        "Use the course list in the sidebar to manage all your courses. Click on any course to switch between them, and use the color coding to visually organize them.",
    },
    {
      question: "Is my data secure?",
      answer:
        "Yes, StudyMate takes data security seriously. All your personal information and course materials are encrypted and stored securely.",
    },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[9999] p-4">
      <div className="bg-white rounded-lg w-full max-w-[700px] max-h-[80vh] overflow-hidden flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-black/10">
          <h2 className="font-audiowide text-[24px] tracking-[2.4px] text-black">
            {activeTab === "settings" && "Settings"}
            {activeTab === "about" && "About StudyMate"}
            {activeTab === "help" && "Help & Support"}
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
            aria-label="Close modal"
          >
            <X className="w-6 h-6 text-black" strokeWidth={2} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-black/10 px-6">
          <button
            onClick={() => setActiveTab("settings")}
            className={`px-4 py-3 font-audiowide text-[14px] tracking-[1.4px] border-b-2 transition-colors ${
              activeTab === "settings"
                ? "border-black text-black"
                : "border-transparent text-[#666] hover:text-black"
            }`}
          >
            Settings
          </button>
          <button
            onClick={() => setActiveTab("about")}
            className={`px-4 py-3 font-audiowide text-[14px] tracking-[1.4px] border-b-2 transition-colors ${
              activeTab === "about"
                ? "border-black text-black"
                : "border-transparent text-[#666] hover:text-black"
            }`}
          >
            About
          </button>
          <button
            onClick={() => setActiveTab("help")}
            className={`px-4 py-3 font-audiowide text-[14px] tracking-[1.4px] border-b-2 transition-colors ${
              activeTab === "help"
                ? "border-black text-black"
                : "border-transparent text-[#666] hover:text-black"
            }`}
          >
            Help
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {/* Settings Tab */}
          {activeTab === "settings" && (
            <div className="space-y-6">
              {/* Account Settings */}
              <div>
                <h3 className="font-audiowide text-[16px] tracking-[1.6px] text-black mb-4">
                  Account Settings
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="font-audiowide text-[13px] tracking-[1.3px] text-[#201F1F] block mb-2">
                      Full Name
                    </label>
                    <input
                      type="text"
                      defaultValue="Arnob Das"
                      className="w-full px-3 py-2 border border-black rounded font-roboto text-[13px] focus:outline-none focus:ring-2 focus:ring-black"
                    />
                  </div>
                  <div>
                    <label className="font-audiowide text-[13px] tracking-[1.3px] text-[#201F1F] block mb-2">
                      Email
                    </label>
                    <input
                      type="email"
                      defaultValue="arnob@example.com"
                      className="w-full px-3 py-2 border border-black rounded font-roboto text-[13px] focus:outline-none focus:ring-2 focus:ring-black"
                    />
                  </div>
                </div>
              </div>

              {/* Notification Settings */}
              <div>
                <h3 className="font-audiowide text-[16px] tracking-[1.6px] text-black mb-4">
                  Notifications
                </h3>
                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      defaultChecked
                      className="w-4 h-4 rounded accent-black"
                    />
                    <span className="font-audiowide text-[13px] tracking-[1.3px] text-black">
                      Email notifications
                    </span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      defaultChecked
                      className="w-4 h-4 rounded accent-black"
                    />
                    <span className="font-audiowide text-[13px] tracking-[1.3px] text-black">
                      Progress updates
                    </span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      className="w-4 h-4 rounded accent-black"
                    />
                    <span className="font-audiowide text-[13px] tracking-[1.3px] text-black">
                      Course announcements
                    </span>
                  </label>
                </div>
              </div>

              {/* Privacy Settings */}
              <div>
                <h3 className="font-audiowide text-[16px] tracking-[1.6px] text-black mb-4">
                  Privacy
                </h3>
                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="radio"
                      name="privacy"
                      defaultChecked
                      className="w-4 h-4 accent-black"
                    />
                    <span className="font-audiowide text-[13px] tracking-[1.3px] text-black">
                      Public profile
                    </span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="radio"
                      name="privacy"
                      className="w-4 h-4 accent-black"
                    />
                    <span className="font-audiowide text-[13px] tracking-[1.3px] text-black">
                      Private profile
                    </span>
                  </label>
                </div>
              </div>

              {/* Save Button */}
              <button className="w-full px-4 py-2 bg-black text-white font-audiowide text-[13px] tracking-[1.3px] rounded hover:bg-opacity-90 transition-colors">
                Save Changes
              </button>
            </div>
          )}

          {/* About Tab */}
          {activeTab === "about" && (
            <div className="space-y-5">
              <section>
                <h3 className="font-audiowide text-[16px] tracking-[1.6px] text-black mb-2">
                  What is StudyMate?
                </h3>
                <p className="font-roboto text-[13px] leading-relaxed text-[#404040]">
                  StudyMate is an AI-powered learning companion designed to help
                  students personalize their study experience.
                </p>
              </section>

              <section>
                <h3 className="font-audiowide text-[16px] tracking-[1.6px] text-black mb-2">
                  Our Mission
                </h3>
                <p className="font-roboto text-[13px] leading-relaxed text-[#404040]">
                  We believe every student learns differently. Our mission is to provide
                  an intelligent learning platform that adapts to your unique learning
                  style.
                </p>
              </section>

              <section>
                <h3 className="font-audiowide text-[16px] tracking-[1.6px] text-black mb-2">
                  Key Features
                </h3>
                <ul className="font-roboto text-[13px] leading-relaxed text-[#404040] space-y-1">
                  <li>• AI-powered course management</li>
                  <li>• Adaptive learning based on preferences</li>
                  <li>• Personalized explanations</li>
                  <li>• Progress tracking and insights</li>
                  <li>• Multi-material support</li>
                </ul>
              </section>

              <section>
                <h3 className="font-audiowide text-[16px] tracking-[1.6px] text-black mb-2">
                  Version
                </h3>
                <p className="font-roboto text-[13px] text-[#404040]">
                  StudyMate v1.0.0
                </p>
              </section>

              <section>
                <h3 className="font-audiowide text-[16px] tracking-[1.6px] text-black mb-2">
                  Contact
                </h3>
                <p className="font-roboto text-[13px] text-[#404040]">
                  Email:{" "}
                  <a
                    href="mailto:support@studymate.com"
                    className="text-blue-600 hover:underline"
                  >
                    support@studymate.com
                  </a>
                </p>
              </section>
            </div>
          )}

          {/* Help Tab */}
          {activeTab === "help" && (
            <div className="space-y-3">
              <h3 className="font-audiowide text-[16px] tracking-[1.6px] text-black mb-4">
                Frequently Asked Questions
              </h3>

              {faqs.map((faq, index) => (
                <div
                  key={index}
                  className="border border-black/20 rounded overflow-hidden"
                >
                  <button
                    onClick={() =>
                      setExpandedFAQ(expandedFAQ === index ? null : index)
                    }
                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors text-left"
                  >
                    <span className="font-audiowide text-[13px] tracking-[1.3px] text-black">
                      {faq.question}
                    </span>
                    <svg
                      className={`w-4 h-4 transition-transform flex-shrink-0 ml-2 ${
                        expandedFAQ === index ? "rotate-180" : ""
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 14l-7 7m0 0l-7-7m7 7V3"
                      />
                    </svg>
                  </button>

                  {expandedFAQ === index && (
                    <div className="px-4 py-3 bg-gray-50 border-t border-black/20">
                      <p className="font-roboto text-[12px] leading-relaxed text-[#404040]">
                        {faq.answer}
                      </p>
                    </div>
                  )}
                </div>
              ))}

              <div className="mt-6 p-4 bg-gray-50 rounded">
                <p className="font-audiowide text-[14px] tracking-[1.4px] text-black mb-3">
                  Still need help?
                </p>
                <a
                  href="mailto:support@studymate.com"
                  className="inline-block px-4 py-2 bg-black text-white font-audiowide text-[12px] tracking-[1.2px] rounded hover:bg-opacity-90 transition-colors"
                >
                  Contact Support
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
