import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Mail } from "lucide-react";

export default function Index() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [emailSubmitted, setEmailSubmitted] = useState(false);

  const handleGoogleSignIn = () => {
    console.log("Continue with Google");
  };

  const handleEmailContinue = () => {
    if (email.trim()) {
      setEmailSubmitted(true);
      console.log("Continue with email:", email);
      setTimeout(() => {
        navigate("/login");
      }, 800);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleEmailContinue();
    }
  };

  return (
    <div className="min-h-screen w-full bg-white dark:bg-slate-950 transition-colors duration-200">
      {/* Header */}
      <header className="w-full h-[114px] flex items-center justify-between px-6 md:px-12 lg:px-20 border-b border-black/10 dark:border-slate-700">
        <h1 className="font-koulen text-3xl md:text-4xl lg:text-[36px] tracking-[3.6px] text-black dark:text-white animate-float-up">
          StudyMate
        </h1>

        <div className="flex items-center gap-4 md:gap-6">
          <button
            onClick={() => navigate("/login")}
            className="w-[110px] h-[48px] rounded-[26px] bg-[#201F1F] dark:bg-white text-white dark:text-black font-audiowide text-[16px] tracking-[1.6px] hover:bg-opacity-90 dark:hover:bg-opacity-80 transition-all duration-200 btn-micro"
            aria-label="Log in"
          >
            Log In
          </button>
          <button
            onClick={() => navigate("/signup")}
            className="w-[110px] h-[48px] rounded-[26px] border-2 border-black dark:border-white bg-transparent text-black dark:text-white font-audiowide text-[16px] tracking-[1.6px] hover:bg-gray-50 dark:hover:bg-slate-900 transition-all duration-200 btn-micro"
            aria-label="Sign up"
          >
            Sign Up
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="w-full px-6 md:px-12 lg:px-20 py-8 md:py-12">
        <div className="max-w-[1400px] mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16">
          {/* Left Side - Content */}
          <div className="flex flex-col justify-start pt-4 md:pt-8 message-enter">
            {/* Main Heading */}
            <h2 className="font-audiowide text-[40px] md:text-[48px] lg:text-[54px] leading-[1.2] tracking-[5.4px] text-black dark:text-white mb-6">
              Ask
              <br />
              Learn
              <br />
              Master
            </h2>

            {/* Subtitle */}
            <p className="font-audiowide text-[18px] md:text-[20px] leading-normal tracking-[2px] text-[#201F1F] dark:text-gray-300 mb-8 max-w-[442px]">
              The AI that understands You and Your study style
            </p>

            {/* Quick Login Form */}
            <div className="w-full max-w-[375px] rounded-[30px] border-2 border-black dark:border-white bg-transparent p-6 md:p-7 hover:shadow-lg dark:hover:shadow-2xl transition-all duration-300">
              {/* Continue with Google Button */}
              <button
                onClick={handleGoogleSignIn}
                className="w-full h-[48px] rounded-[15px] border-2 border-black dark:border-white bg-transparent dark:hover:bg-slate-800 flex items-center justify-center gap-3 hover:bg-gray-50 transition-all duration-200 btn-micro mb-6"
                aria-label="Sign in with Google"
              >
                <img
                  src="https://api.builder.io/api/v1/image/assets/TEMP/28fa6a883a8372c911a20ade166edf603df76d76?width=52"
                  alt="Google logo"
                  className="w-[26px] h-[26px]"
                  loading="lazy"
                />
                <span className="font-roboto text-[15px] tracking-[0.45px] text-[#252424] dark:text-white">
                  Continue with Google
                </span>
              </button>

              {/* OR Divider */}
              <div className="w-full flex items-center justify-center my-6">
                <span className="font-audiowide text-[16px] tracking-[0.8px] text-black dark:text-white">
                  OR
                </span>
              </div>

              {/* Email Input */}
              <div className="relative mb-6">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-studymate-darkgray dark:text-gray-400" strokeWidth={2} />
                <input
                  type="email"
                  placeholder="Enter your Email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="w-full h-[48px] rounded-[15px] border-2 border-black dark:border-white bg-studymate-gray dark:bg-slate-800 px-4 pl-10 font-roboto text-[15px] tracking-[0.45px] text-[#252424] dark:text-white placeholder:text-[#252424] dark:placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-studymate-orange dark:focus:ring-studymate-green transition-all duration-200"
                  aria-label="Email address"
                />
              </div>

              {/* Continue with Email Button */}
              <button
                onClick={handleEmailContinue}
                disabled={emailSubmitted || !email.trim()}
                className={`w-full h-[48px] rounded-[15px] border-2 border-black dark:border-white bg-transparent font-roboto text-[15px] tracking-[0.45px] text-[#252424] dark:text-white transition-all duration-200 btn-micro mb-6 disabled:opacity-50 disabled:cursor-not-allowed ${
                  emailSubmitted ? "animate-pulse" : ""
                }`}
                aria-label="Continue with email"
                aria-busy={emailSubmitted}
              >
                {emailSubmitted ? "Processing..." : "Continue with Email"}
              </button>

              {/* Privacy Policy */}
              <p className="text-center font-audiowide text-[14px] text-[#1E1E1E] dark:text-gray-400">
                By continuing, you acknowledge our{" "}
                <button className="underline cursor-pointer hover:opacity-70 transition-opacity font-bold dark:text-white">
                  Privacy Policy
                </button>
              </p>
            </div>
          </div>

          {/* Right Side - Decorative */}
          <div className="hidden lg:flex items-center justify-center">
            <div className="w-full h-96 bg-gradient-to-br from-studymate-orange/10 to-studymate-green/10 dark:from-studymate-orange/5 dark:to-studymate-green/5 rounded-2xl flex items-center justify-center border-2 border-studymate-orange/20 dark:border-studymate-green/20 animate-bounce-subtle">
              <div className="text-center">
                <div className="text-6xl mb-4">✨</div>
                <p className="font-audiowide text-lg text-black dark:text-white">
                  Personalized Learning
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
