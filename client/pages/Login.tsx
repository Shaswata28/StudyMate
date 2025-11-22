import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";
import { toast } from "@/lib/toast";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});

  const validateForm = () => {
    const newErrors: { email?: string; password?: string } = {};

    if (!email.trim()) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = "Please enter a valid email";
    }

    if (!password.trim()) {
      newErrors.password = "Password is required";
    } else if (password.length < 6) {
      newErrors.password = "Password must be at least 6 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      if (errors.email) toast.error("Validation Error", errors.email);
      if (errors.password) toast.error("Validation Error", errors.password);
      return;
    }

    setIsLoading(true);
    console.log("Login attempt:", { email, password, rememberMe });

    try {
      // Simulate login delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      setIsLoading(false);
      toast.success("Login successful!", "Redirecting to dashboard...");
      setTimeout(() => navigate("/app"), 600);
    } catch (error) {
      setIsLoading(false);
      toast.error("Login failed", "Please check your credentials and try again");
    }
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
            The AI that understands You and Your study style
          </p>
        </div>

        {/* Right Side - Login Form */}
        <div className="flex justify-center lg:justify-end message-enter order-1 lg:order-2">
          <div className="w-full max-w-[412px] rounded-[20px] sm:rounded-[30px] border-2 border-black dark:border-white bg-white dark:bg-slate-800 p-6 sm:p-8 shadow-lg hover:shadow-2xl dark:hover:shadow-2xl transition-all duration-300 ease-out">
            <form onSubmit={handleLogin} className="space-y-5 sm:space-y-6">
              {/* Email Field */}
              <div className="space-y-2">
                <label htmlFor="email" className="font-audiowide text-sm sm:text-base lg:text-[17px] tracking-[0.5px] sm:tracking-[0.8px] lg:tracking-[0.85px] text-black dark:text-white block font-semibold">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  placeholder="Enter your Email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (errors.email) setErrors({ ...errors, email: undefined });
                  }}
                  disabled={isLoading}
                  className={`w-full h-12 sm:h-[62px] rounded-[12px] sm:rounded-[15px] border-2 ${
                    errors.email
                      ? "border-red-500 dark:border-red-400"
                      : "border-black dark:border-white"
                  } bg-studymate-gray dark:bg-slate-700 px-4 font-roboto text-sm sm:text-[15px] tracking-[0.3px] sm:tracking-[0.45px] text-[#252424] dark:text-white placeholder:text-[#252424] dark:placeholder:text-gray-400 focus:outline-none focus:ring-2 ${
                    errors.email
                      ? "focus:ring-red-500 dark:focus:ring-red-400"
                      : "focus:ring-studymate-orange dark:focus:ring-studymate-green"
                  } transition-all duration-200 disabled:opacity-50`}
                />
                {errors.email && (
                  <p className="text-red-500 dark:text-red-400 text-xs sm:text-sm font-roboto">
                    {errors.email}
                  </p>
                )}
              </div>

              {/* Password Field */}
              <div className="space-y-2">
                <label htmlFor="password" className="font-audiowide text-sm sm:text-base lg:text-[17px] tracking-[0.5px] sm:tracking-[0.8px] lg:tracking-[0.85px] text-black dark:text-white block font-semibold">
                  Password
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (errors.password) setErrors({ ...errors, password: undefined });
                    }}
                    disabled={isLoading}
                    className={`w-full h-12 sm:h-[62px] rounded-[12px] sm:rounded-[15px] border-2 ${
                      errors.password
                        ? "border-red-500 dark:border-red-400"
                        : "border-black dark:border-white"
                    } bg-studymate-gray dark:bg-slate-700 px-4 pr-12 font-roboto text-sm sm:text-[15px] tracking-[0.3px] sm:tracking-[0.45px] text-[#252424] dark:text-white placeholder:text-[#252424] dark:placeholder:text-gray-400 focus:outline-none focus:ring-2 ${
                      errors.password
                        ? "focus:ring-red-500 dark:focus:ring-red-400"
                        : "focus:ring-studymate-orange dark:focus:ring-studymate-green"
                    } transition-all duration-200 disabled:opacity-50`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    disabled={isLoading}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-[#1E1E1E] dark:text-white hover:text-black dark:hover:text-gray-300 transition-colors btn-micro disabled:opacity-50"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? (
                      <EyeOff className="w-5 h-5 sm:w-6 sm:h-6" strokeWidth={2} />
                    ) : (
                      <Eye className="w-5 h-5 sm:w-6 sm:h-6" strokeWidth={2} />
                    )}
                  </button>
                </div>
                {errors.password && (
                  <p className="text-red-500 dark:text-red-400 text-xs sm:text-sm font-roboto">
                    {errors.password}
                  </p>
                )}
              </div>

              {/* Remember Me & Forgot Password */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-0">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 rounded border-2 border-black dark:border-white bg-transparent checked:bg-studymate-black dark:checked:bg-white focus:ring-2 focus:ring-studymate-orange transition-all duration-200"
                    aria-label="Remember me"
                  />
                  <span className="font-inter text-sm sm:text-base text-[#1E1E1E] dark:text-white">
                    Remember me
                  </span>
                </label>

                <Link
                  to="/forgot-password"
                  className="font-inter text-sm sm:text-base text-[#1E1E1E] dark:text-white hover:text-studymate-orange dark:hover:text-studymate-green font-semibold transition-colors duration-200"
                >
                  Forgot Password?
                </Link>
              </div>

              {/* Log In Button */}
              <button
                type="submit"
                disabled={isLoading || !email || !password}
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
                    Logging in...
                  </span>
                ) : (
                  "Log In"
                )}
              </button>

              {/* Sign Up Link - Enhanced Visual Hierarchy */}
              <div className="flex flex-col items-center gap-3 pt-2">
                <div className="text-center">
                  <span className="font-inter text-sm sm:text-base text-[#1E1E1E] dark:text-gray-400">
                    Don't have an account?{" "}
                  </span>
                  <Link
                    to="/signup"
                    className="font-inter text-sm sm:text-base font-bold text-studymate-orange dark:text-studymate-green hover:underline transition-all duration-200"
                  >
                    Create one
                  </Link>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
