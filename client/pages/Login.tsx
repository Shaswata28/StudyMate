import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Login attempt:", { email, password, rememberMe });
    navigate("/app");
  };

  return (
    <div className="min-h-screen w-full bg-white flex items-center justify-center px-6 md:px-12">
      <div className="w-full max-w-[1400px] mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
        {/* Left Side - Branding */}
        <div className="flex flex-col justify-center">
          <h1 className="font-koulen text-[64px] md:text-[80px] lg:text-[96px] leading-none tracking-[9.6px] text-black mb-6">
            StudyMate
          </h1>
          <p className="font-audiowide text-[18px] md:text-[20px] leading-normal tracking-[2px] text-[#201F1F] max-w-[442px]">
            The AI that understands You and Your study style
          </p>
        </div>

        {/* Right Side - Login Form */}
        <div className="flex justify-center lg:justify-end">
          <div className="w-full max-w-[412px] rounded-[30px] border border-black bg-transparent p-8">
            <form onSubmit={handleLogin} className="space-y-6">
              {/* Email Field */}
              <div className="space-y-2">
                <label className="font-audiowide text-[17px] tracking-[0.85px] text-black block">
                  Email
                </label>
                <input
                  type="email"
                  placeholder="Enter your Email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full h-[62px] rounded-[15px] border border-black bg-[#D9D9D9] px-4 font-roboto text-[15px] tracking-[0.45px] text-[#252424] placeholder:text-[#252424] focus:outline-none focus:ring-2 focus:ring-black"
                />
              </div>

              {/* Password Field */}
              <div className="space-y-2">
                <label className="font-audiowide text-[17px] tracking-[0.85px] text-black block">
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full h-[62px] rounded-[15px] border border-black bg-[#D9D9D9] px-4 pr-12 font-roboto text-[15px] tracking-[0.45px] text-[#252424] placeholder:text-[#252424] focus:outline-none focus:ring-2 focus:ring-black"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-[#1E1E1E] hover:text-black transition-colors"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    <svg
                      width="24"
                      height="24"
                      viewBox="0 0 24 24"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <g clipPath="url(#clip0_39_118)">
                        <path
                          d="M17.94 17.94C16.2306 19.243 14.1491 19.9649 12 20C5 20 1 12 1 12C2.24389 9.6819 3.96914 7.65661 6.06 6.06M9.9 4.24C10.5883 4.07888 11.2931 3.99834 12 4C19 4 23 12 23 12C22.393 13.1356 21.6691 14.2047 20.84 15.19M14.12 14.12C13.8454 14.4147 13.5141 14.6512 13.1462 14.8151C12.7782 14.9791 12.3809 15.0673 11.9781 15.0744C11.5753 15.0815 11.1752 15.0074 10.8016 14.8565C10.4281 14.7056 10.0887 14.481 9.80385 14.1962C9.51897 13.9113 9.29439 13.5719 9.14351 13.1984C8.99262 12.8248 8.91853 12.4247 8.92563 12.0219C8.93274 11.6191 9.02091 11.2218 9.18488 10.8538C9.34884 10.4859 9.58525 10.1546 9.88 9.88M1 1L23 23"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </g>
                      <defs>
                        <clipPath id="clip0_39_118">
                          <rect width="24" height="24" fill="white" />
                        </clipPath>
                      </defs>
                    </svg>
                  </button>
                </div>
              </div>

              {/* Remember Me & Forgot Password */}
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-3 cursor-pointer">
                  <div
                    className={`w-4 h-4 rounded flex items-center justify-center border transition-colors ${
                      rememberMe
                        ? "bg-[#2C2C2C] border-[#2C2C2C]"
                        : "bg-transparent border-black"
                    }`}
                    onClick={() => setRememberMe(!rememberMe)}
                  >
                    {rememberMe && (
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 16 16"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M13.3333 4L6 11.3333L2.66666 8"
                          stroke="#F5F5F5"
                          strokeWidth="1.6"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    )}
                  </div>
                  <span className="font-inter text-[16px] text-[#1E1E1E]">
                    Remember me
                  </span>
                </label>

                <button
                  type="button"
                  className="font-inter text-[16px] text-[#1E1E1E] hover:underline"
                >
                  Forgot Password ?
                </button>
              </div>

              {/* Log In Button */}
              <button
                type="submit"
                className="w-full h-[62px] rounded-[15px] bg-[#201F1F] text-white font-audiowide text-[20px] tracking-[1px] hover:bg-opacity-90 transition-colors"
              >
                Log In
              </button>

              {/* Sign Up Link */}
              <div className="text-center">
                <span className="font-inter text-[16px] text-[#1E1E1E]">
                  Don't have an account?{" "}
                </span>
                <Link
                  to="/signup"
                  className="font-inter text-[16px] text-[#08F] underline hover:no-underline"
                >
                  Sign Up
                </Link>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
