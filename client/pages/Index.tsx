import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Index() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");

  const handleGoogleSignIn = () => {
    console.log("Continue with Google");
  };

  const handleEmailContinue = () => {
    console.log("Continue with email:", email);
  };

  return (
    <div className="min-h-screen w-full bg-white">
      {/* Header */}
      <header className="w-full h-[114px] flex items-center justify-between px-6 md:px-12 lg:px-20">
        <h1 className="font-koulen text-3xl md:text-4xl lg:text-[36px] tracking-[3.6px] text-black">
          StudyMate
        </h1>

        <div className="flex items-center gap-4 md:gap-6">
          <button
            onClick={() => navigate("/login")}
            className="w-[110px] h-[48px] rounded-[26px] bg-[#201F1F] text-white font-audiowide text-[16px] tracking-[1.6px] hover:bg-opacity-90 transition-colors"
          >
            Log In
          </button>
          <button
            onClick={() => navigate("/signup")}
            className="w-[110px] h-[48px] rounded-[26px] border border-black bg-transparent text-black font-audiowide text-[16px] tracking-[1.6px] hover:bg-gray-50 transition-colors"
          >
            Sign Up
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="w-full px-6 md:px-12 lg:px-20 py-8 md:py-12">
        <div className="max-w-[1400px] mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16">
          {/* Left Side - Content */}
          <div className="flex flex-col justify-start pt-4 md:pt-8">
            {/* Main Heading */}
            <h2 className="font-audiowide text-[40px] md:text-[48px] lg:text-[54px] leading-[1.2] tracking-[5.4px] text-black mb-6">
              Ask
              <br />
              Learn
              <br />
              Master
            </h2>

            {/* Subtitle */}
            <p className="font-audiowide text-[18px] md:text-[20px] leading-normal tracking-[2px] text-[#201F1F] mb-8 max-w-[442px]">
              The AI that understands You and Your study style
            </p>

            {/* Quick Login Form */}
            <div className="w-full max-w-[375px] rounded-[30px] border border-black bg-transparent p-6 md:p-7">
              {/* Continue with Google Button */}
              <button
                onClick={handleGoogleSignIn}
                className="w-full h-[48px] rounded-[15px] border border-black bg-transparent flex items-center justify-center gap-3 hover:bg-gray-50 transition-colors mb-6"
              >
                <img
                  src="https://api.builder.io/api/v1/image/assets/TEMP/28fa6a883a8372c911a20ade166edf603df76d76?width=52"
                  alt="Google logo"
                  className="w-[26px] h-[26px]"
                />
                <span className="font-roboto text-[15px] tracking-[0.45px] text-[#252424]">
                  Continue with Google
                </span>
              </button>

              {/* OR Divider */}
              <div className="w-full flex items-center justify-center my-6">
                <span className="font-audiowide text-[16px] tracking-[0.8px] text-black">
                  OR
                </span>
              </div>

              {/* Email Input */}
              <input
                type="email"
                placeholder="Enter your Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full h-[48px] rounded-[15px] border border-black bg-[#D9D9D9] px-4 font-roboto text-[15px] tracking-[0.45px] text-[#252424] placeholder:text-[#252424] focus:outline-none focus:ring-2 focus:ring-black mb-6"
              />

              {/* Continue with Email Button */}
              <button
                onClick={handleEmailContinue}
                className="w-full h-[48px] rounded-[15px] border border-black bg-transparent font-roboto text-[15px] tracking-[0.45px] text-[#252424] hover:bg-gray-50 transition-colors mb-6"
              >
                Continue with Email
              </button>

              {/* Privacy Policy */}
              <p className="text-center font-audiowide text-[14px] text-[#1E1E1E]">
                By continuing, you acknowledge our{" "}
                <span className="underline cursor-pointer">Privacy Policy</span>
              </p>
            </div>
          </div>

          {/* Right Side - Empty for Image */}
          <div className="hidden lg:flex items-center justify-center">
            {/* Image placeholder - will be added later */}
          </div>
        </div>
      </div>
    </div>
  );
}
