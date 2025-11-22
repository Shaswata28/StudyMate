import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Mail, CheckCircle } from "lucide-react";
import { toast } from "@/lib/toast";

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  const validateEmail = () => {
    if (!email.trim()) {
      setError("Email is required");
      return false;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError("Please enter a valid email");
      return false;
    }
    setError("");
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateEmail()) {
      toast.error("Validation Error", error);
      return;
    }

    setIsLoading(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setIsLoading(false);
      setSubmitted(true);
      toast.success("Check your email", "Password reset link has been sent");
      setTimeout(() => navigate("/login"), 2000);
    } catch (error) {
      setIsLoading(false);
      toast.error("Error", "Failed to send reset link. Please try again.");
    }
  };

  const handleBackToLogin = () => {
    navigate("/login");
  };

  return (
    <div className="min-h-screen w-full bg-white dark:bg-slate-950 transition-colors duration-200 flex items-center justify-center px-4 sm:px-6 md:px-12 py-8">
      <div className="w-full max-w-[1400px] mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-16 items-center">
        {/* Left Side - Branding */}
        <div className="flex flex-col justify-center message-enter order-2 lg:order-1">
          <h1 className="font-koulen text-5xl sm:text-6xl md:text-7xl lg:text-[96px] leading-none tracking-[3.6px] sm:tracking-[7.2px] lg:tracking-[9.6px] text-black dark:text-white mb-4 sm:mb-6">
            StudyMate
          </h1>
          <p className="font-audiowide text-base sm:text-lg md:text-[18px] lg:text-[20px] leading-normal tracking-[1px] sm:tracking-[1.5px] lg:tracking-[2px] text-[#201F1F] dark:text-gray-300 max-w-[442px]">
            Reset your password and get back to your studies
          </p>
        </div>

        {/* Right Side - Form */}
        <div className="flex justify-center lg:justify-end message-enter order-1 lg:order-2">
          <div className="w-full max-w-[412px] rounded-[20px] sm:rounded-[30px] border-2 border-black dark:border-white bg-white dark:bg-slate-800 p-6 sm:p-8 shadow-lg hover:shadow-2xl dark:hover:shadow-2xl transition-all duration-300 ease-out">
            {!submitted ? (
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Back Button */}
                <button
                  type="button"
                  onClick={handleBackToLogin}
                  className="flex items-center gap-2 text-[#1E1E1E] dark:text-white hover:text-studymate-orange dark:hover:text-studymate-green transition-colors duration-200 mb-4"
                  aria-label="Back to login"
                >
                  <ArrowLeft className="w-4 h-4 sm:w-5 sm:h-5" strokeWidth={2} />
                  <span className="font-inter text-sm sm:text-base font-semibold">Back to Login</span>
                </button>

                {/* Title */}
                <div className="space-y-2">
                  <h2 className="font-audiowide text-2xl sm:text-3xl md:text-4xl lg:text-[36px] leading-none tracking-[1.2px] sm:tracking-[1.8px] lg:tracking-[2.4px] text-black dark:text-white">
                    Forgot Password?
                  </h2>
                  <p className="font-roboto text-sm sm:text-base text-[#201F1F] dark:text-gray-300">
                    Enter your email address and we'll send you a link to reset your password.
                  </p>
                </div>

                {/* Email Field */}
                <div className="space-y-2">
                  <label
                    htmlFor="email"
                    className="font-audiowide text-sm sm:text-base lg:text-[17px] tracking-[0.5px] sm:tracking-[0.8px] lg:tracking-[0.85px] text-black dark:text-white block font-semibold flex items-center gap-2"
                  >
                    <Mail className="w-4 h-4 sm:w-5 sm:h-5" strokeWidth={2} />
                    Email Address
                  </label>
                  <input
                    id="email"
                    type="email"
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (error) setError("");
                    }}
                    disabled={isLoading}
                    className={`w-full h-12 sm:h-[62px] rounded-[12px] sm:rounded-[15px] border-2 ${
                      error ? "border-red-500 dark:border-red-400" : "border-black dark:border-white"
                    } bg-studymate-gray dark:bg-slate-700 px-4 font-roboto text-sm sm:text-[15px] tracking-[0.3px] sm:tracking-[0.45px] text-[#252424] dark:text-white placeholder:text-[#252424] dark:placeholder:text-gray-400 focus:outline-none focus:ring-2 ${
                      error
                        ? "focus:ring-red-500 dark:focus:ring-red-400"
                        : "focus:ring-studymate-orange dark:focus:ring-studymate-green"
                    } transition-all duration-200 disabled:opacity-50`}
                  />
                  {error && <p className="text-red-500 dark:text-red-400 text-xs sm:text-sm font-roboto">{error}</p>}
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={isLoading || !email}
                  className="w-full h-12 sm:h-[62px] rounded-[12px] sm:rounded-[15px] bg-studymate-black dark:bg-white text-white dark:text-black font-audiowide text-lg sm:text-[20px] tracking-[0.5px] sm:tracking-[1px] font-bold hover:shadow-xl dark:hover:shadow-xl active:scale-95 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 btn-micro"
                  aria-busy={isLoading}
                >
                  {isLoading ? (
                    <span className="inline-flex items-center gap-2">
                      <svg
                        className="animate-spin h-5 w-5"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                      Sending...
                    </span>
                  ) : (
                    "Send Reset Link"
                  )}
                </button>

                {/* Remember Password Link */}
                <div className="text-center pt-2">
                  <span className="font-inter text-sm sm:text-base text-[#1E1E1E] dark:text-gray-400">
                    Remember your password?{" "}
                  </span>
                  <Link
                    to="/login"
                    className="font-inter text-sm sm:text-base font-bold text-studymate-orange dark:text-studymate-green hover:underline transition-all duration-200"
                  >
                    Back to Login
                  </Link>
                </div>
              </form>
            ) : (
              <div className="flex flex-col items-center justify-center space-y-6 py-8">
                <div className="animate-in fade-in scale-in-95 duration-300">
                  <CheckCircle className="w-16 h-16 sm:w-20 sm:h-20 text-green-500" strokeWidth={1.5} />
                </div>
                <div className="text-center space-y-3">
                  <h3 className="font-audiowide text-xl sm:text-2xl text-black dark:text-white tracking-[0.8px]">
                    Check Your Email
                  </h3>
                  <p className="font-roboto text-sm sm:text-base text-[#201F1F] dark:text-gray-300 max-w-xs">
                    A password reset link has been sent to <strong>{email}</strong>
                  </p>
                  <p className="font-roboto text-xs sm:text-sm text-[#201F1F] dark:text-gray-400">
                    Redirecting to login in a few seconds...
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
