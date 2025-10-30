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
    <div className="min-h-screen w-full bg-white px-6 md:px-12 lg:px-20">
      <header className="w-full h-[114px] flex items-center">
        <h1 className="font-koulen text-3xl md:text-4xl lg:text-[36px] tracking-[3.6px] text-black">
          StudyMate
        </h1>
      </header>

      <div className="max-w-[1200px] mx-auto pt-12 md:pt-20">
        <div className="space-y-8 mb-12">
          <div>
            <h2 className="font-audiowide text-[20px] md:text-[24px] leading-normal tracking-[2.4px] text-black">
              Help us personalize your learning experience!
              <br />
              Answer these questions so we can tailor explanations to match how you learn best.
            </h2>
          </div>

          <div>
            <p className="font-audiowide text-[20px] md:text-[24px] leading-normal tracking-[2.4px] text-black">
              You can skip this and we'll learn your preferences as you use the app,
              <br />
              but answering now gives us a head start!
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 justify-center pt-8">
          <button
            onClick={handleSkip}
            className="w-[110px] h-[48px] rounded-[26px] border border-black bg-transparent text-black font-audiowide text-[16px] tracking-[1.6px] hover:bg-gray-50 transition-colors"
          >
            Skip
          </button>
          <button
            onClick={handleContinue}
            className="w-[139px] h-[48px] rounded-[26px] bg-black text-white font-audiowide text-[16px] tracking-[1.6px] hover:bg-opacity-90 transition-colors"
          >
            Continue
          </button>
        </div>
      </div>
    </div>
  );
}
