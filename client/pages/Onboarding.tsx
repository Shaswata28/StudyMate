import { useNavigate } from "react-router-dom";

export default function Onboarding() {
  const navigate = useNavigate();

  const handleSkip = () => {
    navigate("/app");
  };

  const handleContinue = () => {
    navigate("/questions");
  };

  return (
    <div className="min-h-screen w-full bg-white dark:bg-slate-950 transition-colors duration-200 px-6 md:px-12 lg:px-20 flex flex-col">
      <header className="w-full h-[114px] flex items-center border-b border-black/10 dark:border-slate-700">
        <h1 className="font-koulen text-3xl md:text-4xl lg:text-[36px] tracking-[3.6px] text-black dark:text-white">
          StudyMate
        </h1>
      </header>

      <div className="flex-1 flex flex-col max-w-[1200px] mx-auto pt-12 md:pt-20 w-full">
        <div className="space-y-12 mb-12 message-enter">
          <div className="space-y-4">
            <div className="flex items-center gap-3 mb-6">
              <h2 className="font-audiowide text-[24px] md:text-[28px] leading-normal tracking-[2.4px] text-black dark:text-white">
                Personalize Your Experience
              </h2>
            </div>
            <p className="font-audiowide text-[18px] md:text-[20px] leading-normal tracking-[2px] text-[#201F1F] dark:text-gray-300 ml-15">
              Answer a few quick questions so we can tailor explanations to match how you learn best.
            </p>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <span aria-hidden className="text-[32px] leading-none text-black dark:text-white">•</span>
              <p className="font-audiowide text-[18px] md:text-[20px] leading-normal tracking-[2px] text-[#201F1F] dark:text-gray-300">
                Takes just 2-3 minutes
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span aria-hidden className="text-[32px] leading-none text-black dark:text-white">•</span>
              <p className="font-audiowide text-[18px] md:text-[20px] leading-normal tracking-[2px] text-[#201F1F] dark:text-gray-300">
                You can always change your preferences later
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span aria-hidden className="text-[32px] leading-none text-black dark:text-white">•</span>
              <p className="font-audiowide text-[18px] md:text-[20px] leading-normal tracking-[2px] text-[#201F1F] dark:text-gray-300">
                We learn more from how you use the app
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4 justify-center pt-8 message-enter">
          <button
            onClick={handleSkip}
            className="w-[110px] h-[48px] rounded-[26px] border-2 border-black dark:border-white bg-transparent text-black dark:text-white font-audiowide text-[16px] tracking-[1.6px] hover:bg-gray-50 dark:hover:bg-slate-800 transition-all duration-200 btn-micro"
            aria-label="Skip onboarding questionnaire"
          >
            Skip
          </button>
          <button
            onClick={handleContinue}
            className="w-[139px] h-[48px] rounded-[26px] bg-studymate-black dark:bg-white text-white dark:text-black font-audiowide text-[16px] tracking-[1.6px] hover:shadow-lg dark:hover:shadow-lg transition-all duration-200 btn-micro"
            aria-label="Continue to questionnaire"
          >
            Continue
          </button>
        </div>
      </div>
    </div>
  );
}
