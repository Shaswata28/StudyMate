import { useState } from "react";
import { useNavigate } from "react-router-dom";

type SignupStep = 1 | 2;

export default function Signup() {
  const navigate = useNavigate();
  const [step, setStep] = useState<SignupStep>(1);
  
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  const [grade, setGrade] = useState("");
  const [semesterType, setSemesterType] = useState("");
  const [semester, setSemester] = useState("");
  const [subject, setSubject] = useState("");

  const handleStep1Submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      alert("Passwords do not match!");
      return;
    }
    setStep(2);
  };

  const handleStep2Submit = (e: React.FormEvent) => {
    e.preventDefault();
    navigate("/onboarding");
  };

  const handleBack = () => {
    if (step === 2) {
      setStep(1);
    }
  };

  return (
    <div className="min-h-screen w-full bg-white flex items-center justify-center px-6 md:px-12">
      <div className="w-full max-w-[1400px] mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
        <div className="flex flex-col justify-center">
          <h1 className="font-koulen text-3xl md:text-4xl lg:text-[36px] tracking-[3.6px] text-black mb-8 lg:absolute lg:top-8 lg:left-20">
            StudyMate
          </h1>
          
          <h2 className="font-audiowide text-[40px] md:text-[48px] lg:text-[54px] leading-none tracking-[5.4px] text-black mb-6">
            Registration
          </h2>
          
          <p className="font-audiowide text-[20px] md:text-[24px] tracking-[2.4px] text-[#201F1F] mb-2">
            {step === 1 ? "Security" : "Academic Profile"}
          </p>
          
          <p className="font-roboto text-[18px] md:text-[20px] tracking-[0.6px] text-[#252424]">
            Step {step} of 2
          </p>
        </div>

        <div className="flex justify-center lg:justify-end">
          <div className={`w-full max-w-[412px] rounded-[30px] border border-black bg-transparent p-8 ${
            step === 1 ? "min-h-[522px]" : "min-h-[433px]"
          }`}>
            {step === 1 ? (
              <form onSubmit={handleStep1Submit} className="space-y-6">
                <div className="space-y-2">
                  <label className="font-audiowide text-[17px] tracking-[0.85px] text-black block">
                    Name
                  </label>
                  <input
                    type="text"
                    placeholder="Enter your name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="w-full h-[62px] rounded-[15px] border border-black bg-[#D9D9D9] px-4 font-roboto text-[15px] tracking-[0.45px] text-[#252424] placeholder:text-[#252424] focus:outline-none focus:ring-2 focus:ring-black"
                  />
                </div>

                <div className="space-y-2">
                  <label className="font-audiowide text-[17px] tracking-[0.85px] text-black block">
                    Email
                  </label>
                  <input
                    type="email"
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full h-[62px] rounded-[15px] border border-black bg-[#D9D9D9] px-4 font-roboto text-[15px] tracking-[0.45px] text-[#252424] placeholder:text-[#252424] focus:outline-none focus:ring-2 focus:ring-black"
                  />
                </div>

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
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-[#1E1E1E]"
                    >
                      <EyeOffIcon />
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="font-audiowide text-[17px] tracking-[0.85px] text-black block">
                    Confirm password
                  </label>
                  <div className="relative">
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="Enter password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      className="w-full h-[62px] rounded-[15px] border border-black bg-[#D9D9D9] px-4 pr-12 font-roboto text-[15px] tracking-[0.45px] text-[#252424] placeholder:text-[#252424] focus:outline-none focus:ring-2 focus:ring-black"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-[#1E1E1E]"
                    >
                      <EyeOffIcon />
                    </button>
                  </div>
                </div>

                <div className="flex justify-end pt-4">
                  <button
                    type="submit"
                    className="w-[30px] h-[30px] rounded-full flex items-center justify-center hover:bg-gray-100 transition-colors"
                  >
                    <ArrowRightCircleIcon />
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleStep2Submit} className="space-y-6">
                <div className="space-y-2">
                  <label className="font-audiowide text-[17px] tracking-[0.85px] text-black block">
                    Which grade are you in ?
                  </label>
                  <input
                    type="text"
                    placeholder="Enter your name"
                    value={grade}
                    onChange={(e) => setGrade(e.target.value)}
                    required
                    className="w-full h-[62px] rounded-[15px] border border-black bg-[#D9D9D9] px-4 font-roboto text-[15px] tracking-[0.45px] text-[#252424] placeholder:text-[#252424] focus:outline-none focus:ring-2 focus:ring-black"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="font-audiowide text-[17px] tracking-[0.85px] text-black block">
                      Semester type
                    </label>
                    <div className="relative">
                      <select
                        value={semesterType}
                        onChange={(e) => setSemesterType(e.target.value)}
                        required
                        className="w-full h-[63px] rounded-[15px] border border-black bg-[#D9D9D9] px-4 font-roboto text-[15px] tracking-[0.45px] text-[#252424] focus:outline-none focus:ring-2 focus:ring-black appearance-none"
                      >
                        <option value="">Double /Tri</option>
                        <option value="double">Double</option>
                        <option value="tri">Tri</option>
                      </select>
                      <ChevronDownIcon className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="font-audiowide text-[17px] tracking-[0.85px] text-black block">
                      Semester
                    </label>
                    <div className="relative">
                      <select
                        value={semester}
                        onChange={(e) => setSemester(e.target.value)}
                        required
                        className="w-full h-[63px] rounded-[15px] border border-black bg-[#D9D9D9] px-4 font-roboto text-[15px] tracking-[0.45px] text-[#252424] focus:outline-none focus:ring-2 focus:ring-black appearance-none"
                      >
                        <option value="">1-12</option>
                        {Array.from({ length: 12 }, (_, i) => i + 1).map((num) => (
                          <option key={num} value={num}>
                            {num}
                          </option>
                        ))}
                      </select>
                      <ChevronDownIcon className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="font-audiowide text-[17px] tracking-[0.85px] text-black block">
                    Which Subject ?
                  </label>
                  <div className="relative">
                    <select
                      value={subject}
                      onChange={(e) => setSubject(e.target.value)}
                      required
                      className="w-full h-[62px] rounded-[15px] border border-black bg-[#D9D9D9] px-4 font-roboto text-[15px] tracking-[0.45px] text-[#252424] focus:outline-none focus:ring-2 focus:ring-black appearance-none"
                    >
                      <option value="">Enter password</option>
                      <option value="math">Mathematics</option>
                      <option value="science">Science</option>
                      <option value="english">English</option>
                      <option value="history">History</option>
                    </select>
                    <ChevronDownIcon className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                  </div>
                </div>

                <div className="flex justify-between items-center pt-4">
                  <button
                    type="button"
                    onClick={handleBack}
                    className="w-[30px] h-[30px] rounded-full flex items-center justify-center hover:bg-gray-100 transition-colors"
                  >
                    <ArrowLeftCircleIcon />
                  </button>
                  <button
                    type="submit"
                    className="w-[30px] h-[30px] rounded-full flex items-center justify-center hover:bg-gray-100 transition-colors"
                  >
                    <ArrowRightCircleIcon />
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function EyeOffIcon() {
  return (
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
  );
}

function ArrowRightCircleIcon() {
  return (
    <svg
      width="30"
      height="30"
      viewBox="0 0 30 30"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <g clipPath="url(#clip0_39_137)">
        <path
          d="M15 20L20 15M20 15L15 10M20 15H10M27.5 15C27.5 21.9036 21.9036 27.5 15 27.5C8.09644 27.5 2.5 21.9036 2.5 15C2.5 8.09644 8.09644 2.5 15 2.5C21.9036 2.5 27.5 8.09644 27.5 15Z"
          stroke="#1E1E1E"
          strokeWidth="4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </g>
      <defs>
        <clipPath id="clip0_39_137">
          <rect width="30" height="30" fill="white" />
        </clipPath>
      </defs>
    </svg>
  );
}

function ArrowLeftCircleIcon() {
  return (
    <svg
      width="30"
      height="30"
      viewBox="0 0 30 30"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <g clipPath="url(#clip0_39_153)">
        <path
          d="M15 10L10 15M10 15L15 20M10 15H20M27.5 15C27.5 21.9036 21.9036 27.5 15 27.5C8.09644 27.5 2.5 21.9036 2.5 15C2.5 8.09644 8.09644 2.5 15 2.5C21.9036 2.5 27.5 8.09644 27.5 15Z"
          stroke="#1E1E1E"
          strokeWidth="4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </g>
      <defs>
        <clipPath id="clip0_39_153">
          <rect width="30" height="30" fill="white" />
        </clipPath>
      </defs>
    </svg>
  );
}

function ChevronDownIcon({ className = "" }: { className?: string }) {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path
        d="M6 9L12 15L18 9"
        stroke="#1E1E1E"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
