import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Eye, EyeOff, ChevronDown, ArrowLeft, ArrowRight, Check } from "lucide-react";
import { toast } from "@/lib/toast";
import PasswordStrengthIndicator from "@/components/PasswordStrengthIndicator";

type SignupStep = 1 | 2;

interface Step1Errors {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  terms?: string;
}

export default function Signup() {
  const navigate = useNavigate();
  const [step, setStep] = useState<SignupStep>(1);
  const [showStepAnimation, setShowStepAnimation] = useState(false);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [step1Errors, setStep1Errors] = useState<Step1Errors>({});

  const [grade, setGrade] = useState("");
  const [semesterType, setSemesterType] = useState("");
  const [semester, setSemester] = useState("");
  const [subject, setSubject] = useState("");
  const [step2Errors, setStep2Errors] = useState<{
    grade?: string;
    semesterType?: string;
    semester?: string;
    subject?: string;
  }>({});

  const validateStep1 = (): boolean => {
    const errors: Step1Errors = {};

    if (!name.trim()) {
      errors.name = "Name is required";
    } else if (name.length < 2) {
      errors.name = "Name must be at least 2 characters";
    }

    if (!email.trim()) {
      errors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = "Please enter a valid email";
    }

    if (!password.trim()) {
      errors.password = "Password is required";
    } else if (password.length < 8) {
      errors.password = "Password must be at least 8 characters";
    }

    if (!confirmPassword.trim()) {
      errors.confirmPassword = "Please confirm your password";
    } else if (password !== confirmPassword) {
      errors.confirmPassword = "Passwords do not match";
    }

    if (!acceptTerms) {
      errors.terms = "You must accept the Terms and Conditions";
    }

    setStep1Errors(errors);
    return Object.keys(errors).length === 0;
  };

  const validateStep2 = (): boolean => {
    const errors: typeof step2Errors = {};

    if (!grade.trim()) {
      errors.grade = "Grade is required";
    }

    if (!semesterType) {
      errors.semesterType = "Semester type is required";
    }

    if (!semester) {
      errors.semester = "Semester is required";
    }

    if (!subject) {
      errors.subject = "Subject is required";
    }

    setStep2Errors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleStep1Submit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateStep1()) {
      Object.entries(step1Errors).forEach(([field, message]) => {
        if (message) toast.error("Validation Error", message);
      });
      return;
    }

    setShowStepAnimation(true);
    setTimeout(() => {
      setShowStepAnimation(false);
      setStep(2);
    }, 600);
  };

  const handleStep2Submit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateStep2()) {
      Object.entries(step2Errors).forEach(([field, message]) => {
        if (message) toast.error("Validation Error", message);
      });
      return;
    }

    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      toast.success("Signup successful!", "Redirecting to onboarding...");
      setTimeout(() => navigate("/onboarding"), 600);
    }, 1000);
  };

  const handleBack = () => {
    if (step === 2) {
      setShowStepAnimation(true);
      setTimeout(() => {
        setShowStepAnimation(false);
        setStep(1);
      }, 600);
    }
  };

  return (
    <div className="min-h-screen w-full bg-white dark:bg-slate-950 transition-colors duration-200 flex items-center justify-center px-4 sm:px-6 md:px-12 py-8">
      <div className="w-full max-w-[1400px] mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8 lg:gap-16 items-center">
        <div className="flex flex-col justify-center message-enter order-2 lg:order-1">
          <h1 className="font-koulen text-4xl sm:text-5xl md:text-5xl lg:text-[36px] tracking-[2.4px] sm:tracking-[3.2px] lg:tracking-[3.6px] text-black dark:text-white mb-6 sm:mb-8 lg:absolute lg:top-8 lg:left-20 transition-colors duration-200">
            StudyMate
          </h1>

          <h2 className="font-audiowide text-3xl sm:text-4xl md:text-5xl lg:text-[54px] leading-none tracking-[2.4px] sm:tracking-[3.6px] lg:tracking-[5.4px] text-black dark:text-white mb-4 sm:mb-6 transition-colors duration-200">
            Registration
          </h2>

          <p className="font-audiowide text-lg sm:text-xl md:text-2xl lg:text-[24px] tracking-[1.2px] sm:tracking-[1.8px] lg:tracking-[2.4px] text-[#201F1F] dark:text-gray-300 mb-2 transition-colors duration-200">
            {step === 1 ? "Security" : "Academic Profile"}
          </p>

          <div className="flex items-center gap-3">
            <p className="font-roboto text-sm sm:text-base md:text-lg lg:text-[20px] tracking-[0.4px] sm:tracking-[0.5px] lg:tracking-[0.6px] text-[#252424] dark:text-gray-400 transition-colors duration-200">
              Step {step} of 2
            </p>
            {step === 2 && (
              <div className="animate-in fade-in slide-in-from-left-2 duration-500">
                <Check className="w-5 h-5 sm:w-6 sm:h-6 text-green-500" strokeWidth={3} />
              </div>
            )}
          </div>
        </div>

        <div className="flex justify-center lg:justify-end message-enter order-1 lg:order-2">
          <div
            className={`w-full max-w-[412px] rounded-[20px] sm:rounded-[30px] border-2 border-black dark:border-white bg-white dark:bg-slate-800 p-6 sm:p-8 shadow-lg hover:shadow-2xl dark:hover:shadow-2xl transition-all duration-300 ease-out ${
              showStepAnimation ? "animate-out fade-out slide-out-to-right-2 duration-300" : "animate-in fade-in slide-in-from-left-2 duration-300"
            }`}
          >
            {step === 1 ? (
              <form onSubmit={handleStep1Submit} className="space-y-4 sm:space-y-5">
                <div className="space-y-2">
                  <label
                    htmlFor="name"
                    className="font-audiowide text-sm sm:text-base lg:text-[17px] tracking-[0.5px] sm:tracking-[0.8px] lg:tracking-[0.85px] text-black dark:text-white block font-semibold"
                  >
                    Name
                  </label>
                  <input
                    id="name"
                    type="text"
                    placeholder="Enter your name"
                    value={name}
                    onChange={(e) => {
                      setName(e.target.value);
                      if (step1Errors.name) setStep1Errors({ ...step1Errors, name: undefined });
                    }}
                    disabled={isLoading}
                    className={`w-full h-12 sm:h-[62px] rounded-[12px] sm:rounded-[15px] border-2 ${
                      step1Errors.name
                        ? "border-red-500 dark:border-red-400"
                        : "border-black dark:border-white"
                    } bg-studymate-gray dark:bg-slate-700 px-4 font-roboto text-sm sm:text-[15px] tracking-[0.3px] sm:tracking-[0.45px] text-[#252424] dark:text-white placeholder:text-[#252424] dark:placeholder:text-gray-400 focus:outline-none focus:ring-2 ${
                      step1Errors.name
                        ? "focus:ring-red-500 dark:focus:ring-red-400"
                        : "focus:ring-studymate-orange dark:focus:ring-studymate-green"
                    } transition-all duration-200 disabled:opacity-50`}
                  />
                  {step1Errors.name && (
                    <p className="text-red-500 dark:text-red-400 text-xs sm:text-sm font-roboto">
                      {step1Errors.name}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <label
                    htmlFor="email"
                    className="font-audiowide text-sm sm:text-base lg:text-[17px] tracking-[0.5px] sm:tracking-[0.8px] lg:tracking-[0.85px] text-black dark:text-white block font-semibold"
                  >
                    Email
                  </label>
                  <input
                    id="email"
                    type="email"
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (step1Errors.email) setStep1Errors({ ...step1Errors, email: undefined });
                    }}
                    disabled={isLoading}
                    className={`w-full h-12 sm:h-[62px] rounded-[12px] sm:rounded-[15px] border-2 ${
                      step1Errors.email
                        ? "border-red-500 dark:border-red-400"
                        : "border-black dark:border-white"
                    } bg-studymate-gray dark:bg-slate-700 px-4 font-roboto text-sm sm:text-[15px] tracking-[0.3px] sm:tracking-[0.45px] text-[#252424] dark:text-white placeholder:text-[#252424] dark:placeholder:text-gray-400 focus:outline-none focus:ring-2 ${
                      step1Errors.email
                        ? "focus:ring-red-500 dark:focus:ring-red-400"
                        : "focus:ring-studymate-orange dark:focus:ring-studymate-green"
                    } transition-all duration-200 disabled:opacity-50`}
                  />
                  {step1Errors.email && (
                    <p className="text-red-500 dark:text-red-400 text-xs sm:text-sm font-roboto">
                      {step1Errors.email}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <label
                    htmlFor="password"
                    className="font-audiowide text-sm sm:text-base lg:text-[17px] tracking-[0.5px] sm:tracking-[0.8px] lg:tracking-[0.85px] text-black dark:text-white block font-semibold"
                  >
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
                        if (step1Errors.password)
                          setStep1Errors({ ...step1Errors, password: undefined });
                      }}
                      disabled={isLoading}
                      className={`w-full h-12 sm:h-[62px] rounded-[12px] sm:rounded-[15px] border-2 ${
                        step1Errors.password
                          ? "border-red-500 dark:border-red-400"
                          : "border-black dark:border-white"
                      } bg-studymate-gray dark:bg-slate-700 px-4 pr-12 font-roboto text-sm sm:text-[15px] tracking-[0.3px] sm:tracking-[0.45px] text-[#252424] dark:text-white placeholder:text-[#252424] dark:placeholder:text-gray-400 focus:outline-none focus:ring-2 ${
                        step1Errors.password
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
                  {password && <PasswordStrengthIndicator password={password} />}
                  {step1Errors.password && (
                    <p className="text-red-500 dark:text-red-400 text-xs sm:text-sm font-roboto">
                      {step1Errors.password}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <label
                    htmlFor="confirm-password"
                    className="font-audiowide text-sm sm:text-base lg:text-[17px] tracking-[0.5px] sm:tracking-[0.8px] lg:tracking-[0.85px] text-black dark:text-white block font-semibold"
                  >
                    Confirm password
                  </label>
                  <div className="relative">
                    <input
                      id="confirm-password"
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="Re-enter password"
                      value={confirmPassword}
                      onChange={(e) => {
                        setConfirmPassword(e.target.value);
                        if (step1Errors.confirmPassword)
                          setStep1Errors({ ...step1Errors, confirmPassword: undefined });
                      }}
                      disabled={isLoading}
                      className={`w-full h-12 sm:h-[62px] rounded-[12px] sm:rounded-[15px] border-2 ${
                        step1Errors.confirmPassword
                          ? "border-red-500 dark:border-red-400"
                          : "border-black dark:border-white"
                      } bg-studymate-gray dark:bg-slate-700 px-4 pr-12 font-roboto text-sm sm:text-[15px] tracking-[0.3px] sm:tracking-[0.45px] text-[#252424] dark:text-white placeholder:text-[#252424] dark:placeholder:text-gray-400 focus:outline-none focus:ring-2 ${
                        step1Errors.confirmPassword
                          ? "focus:ring-red-500 dark:focus:ring-red-400"
                          : "focus:ring-studymate-orange dark:focus:ring-studymate-green"
                      } transition-all duration-200 disabled:opacity-50`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      disabled={isLoading}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-[#1E1E1E] dark:text-white hover:text-black dark:hover:text-gray-300 transition-colors btn-micro disabled:opacity-50"
                      aria-label={
                        showConfirmPassword ? "Hide password" : "Show password"
                      }
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="w-5 h-5 sm:w-6 sm:h-6" strokeWidth={2} />
                      ) : (
                        <Eye className="w-5 h-5 sm:w-6 sm:h-6" strokeWidth={2} />
                      )}
                    </button>
                  </div>
                  {step1Errors.confirmPassword && (
                    <p className="text-red-500 dark:text-red-400 text-xs sm:text-sm font-roboto">
                      {step1Errors.confirmPassword}
                    </p>
                  )}
                </div>

                <div className="space-y-3">
                  <label className="flex items-start gap-3 cursor-pointer group">
                    <input
                      type="checkbox"
                      checked={acceptTerms}
                      onChange={(e) => {
                        setAcceptTerms(e.target.checked);
                        if (step1Errors.terms) setStep1Errors({ ...step1Errors, terms: undefined });
                      }}
                      disabled={isLoading}
                      className="w-5 h-5 mt-0.5 rounded border-2 border-black dark:border-white bg-transparent checked:bg-studymate-black dark:checked:bg-white focus:ring-2 focus:ring-studymate-orange dark:focus:ring-studymate-green transition-all duration-200 flex-shrink-0 disabled:opacity-50"
                      aria-label="Accept terms and conditions"
                    />
                    <span className="font-roboto text-sm sm:text-[15px] tracking-[0.3px] sm:tracking-[0.45px] text-[#252424] dark:text-white">
                      I agree to the{" "}
                      <Link
                        to="/terms"
                        className="font-semibold text-studymate-orange dark:text-studymate-green hover:underline transition-colors duration-200"
                        onClick={(e) => {
                          if (isLoading) e.preventDefault();
                        }}
                      >
                        Terms and Conditions
                      </Link>
                    </span>
                  </label>
                  {step1Errors.terms && (
                    <p className="text-red-500 dark:text-red-400 text-xs sm:text-sm font-roboto">
                      {step1Errors.terms}
                    </p>
                  )}
                </div>

                <div className="flex justify-end pt-4">
                  <button
                    type="submit"
                    disabled={isLoading || !name || !email || !password || !confirmPassword || !acceptTerms}
                    className="w-12 h-12 sm:w-[50px] sm:h-[50px] rounded-full flex items-center justify-center bg-studymate-black dark:bg-white text-white dark:text-black hover:shadow-xl active:scale-95 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 btn-micro"
                    aria-label="Next step"
                  >
                    <ArrowRight className="w-5 h-5 sm:w-6 sm:h-6" strokeWidth={2} />
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleStep2Submit} className="space-y-4 sm:space-y-5">
                <div className="space-y-2">
                  <label
                    htmlFor="grade"
                    className="font-audiowide text-sm sm:text-base lg:text-[17px] tracking-[0.5px] sm:tracking-[0.8px] lg:tracking-[0.85px] text-black dark:text-white block font-semibold"
                  >
                    Which grade are you in?
                  </label>
                  <input
                    id="grade"
                    type="text"
                    placeholder="Enter your grade"
                    value={grade}
                    onChange={(e) => {
                      setGrade(e.target.value);
                      if (step2Errors.grade) setStep2Errors({ ...step2Errors, grade: undefined });
                    }}
                    disabled={isLoading}
                    className={`w-full h-12 sm:h-[62px] rounded-[12px] sm:rounded-[15px] border-2 ${
                      step2Errors.grade
                        ? "border-red-500 dark:border-red-400"
                        : "border-black dark:border-white"
                    } bg-studymate-gray dark:bg-slate-700 px-4 font-roboto text-sm sm:text-[15px] tracking-[0.3px] sm:tracking-[0.45px] text-[#252424] dark:text-white placeholder:text-[#252424] dark:placeholder:text-gray-400 focus:outline-none focus:ring-2 ${
                      step2Errors.grade
                        ? "focus:ring-red-500 dark:focus:ring-red-400"
                        : "focus:ring-studymate-orange dark:focus:ring-studymate-green"
                    } transition-all duration-200 disabled:opacity-50`}
                  />
                  {step2Errors.grade && (
                    <p className="text-red-500 dark:text-red-400 text-xs sm:text-sm font-roboto">
                      {step2Errors.grade}
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3 sm:gap-4">
                  <div className="space-y-2">
                    <label
                      htmlFor="semester-type"
                      className="font-audiowide text-sm sm:text-base lg:text-[17px] tracking-[0.5px] sm:tracking-[0.8px] lg:tracking-[0.85px] text-black dark:text-white block font-semibold"
                    >
                      Semester type
                    </label>
                    <div className="relative">
                      <select
                        id="semester-type"
                        value={semesterType}
                        onChange={(e) => {
                          setSemesterType(e.target.value);
                          if (step2Errors.semesterType)
                            setStep2Errors({ ...step2Errors, semesterType: undefined });
                        }}
                        disabled={isLoading}
                        className={`w-full h-12 sm:h-[63px] rounded-[12px] sm:rounded-[15px] border-2 ${
                          step2Errors.semesterType
                            ? "border-red-500 dark:border-red-400"
                            : "border-black dark:border-white"
                        } bg-studymate-gray dark:bg-slate-700 px-4 font-roboto text-sm sm:text-[15px] tracking-[0.3px] sm:tracking-[0.45px] text-[#252424] dark:text-white focus:outline-none focus:ring-2 ${
                          step2Errors.semesterType
                            ? "focus:ring-red-500 dark:focus:ring-red-400"
                            : "focus:ring-studymate-orange dark:focus:ring-studymate-green"
                        } transition-all duration-200 appearance-none disabled:opacity-50`}
                      >
                        <option value="" disabled>
                          Type
                        </option>
                        <option value="double">Double</option>
                        <option value="tri">Tri</option>
                      </select>
                      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none w-4 h-4 sm:w-6 sm:h-6 text-[#1E1E1E] dark:text-white" strokeWidth={2} />
                    </div>
                    {step2Errors.semesterType && (
                      <p className="text-red-500 dark:text-red-400 text-xs sm:text-sm font-roboto">
                        {step2Errors.semesterType}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <label
                      htmlFor="semester"
                      className="font-audiowide text-sm sm:text-base lg:text-[17px] tracking-[0.5px] sm:tracking-[0.8px] lg:tracking-[0.85px] text-black dark:text-white block font-semibold"
                    >
                      Semester
                    </label>
                    <div className="relative">
                      <select
                        id="semester"
                        value={semester}
                        onChange={(e) => {
                          setSemester(e.target.value);
                          if (step2Errors.semester)
                            setStep2Errors({ ...step2Errors, semester: undefined });
                        }}
                        disabled={isLoading}
                        className={`w-full h-12 sm:h-[63px] rounded-[12px] sm:rounded-[15px] border-2 ${
                          step2Errors.semester
                            ? "border-red-500 dark:border-red-400"
                            : "border-black dark:border-white"
                        } bg-studymate-gray dark:bg-slate-700 px-4 font-roboto text-sm sm:text-[15px] tracking-[0.3px] sm:tracking-[0.45px] text-[#252424] dark:text-white focus:outline-none focus:ring-2 ${
                          step2Errors.semester
                            ? "focus:ring-red-500 dark:focus:ring-red-400"
                            : "focus:ring-studymate-orange dark:focus:ring-studymate-green"
                        } transition-all duration-200 appearance-none disabled:opacity-50`}
                      >
                        <option value="" disabled>
                          No
                        </option>
                        {Array.from({ length: 12 }, (_, i) => i + 1).map((num) => (
                          <option key={num} value={num}>
                            {num}
                          </option>
                        ))}
                      </select>
                      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none w-4 h-4 sm:w-6 sm:h-6 text-[#1E1E1E] dark:text-white" strokeWidth={2} />
                    </div>
                    {step2Errors.semester && (
                      <p className="text-red-500 dark:text-red-400 text-xs sm:text-sm font-roboto">
                        {step2Errors.semester}
                      </p>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <label
                    htmlFor="subject"
                    className="font-audiowide text-sm sm:text-base lg:text-[17px] tracking-[0.5px] sm:tracking-[0.8px] lg:tracking-[0.85px] text-black dark:text-white block font-semibold"
                  >
                    Which Subject?
                  </label>
                  <div className="relative">
                    <select
                      id="subject"
                      value={subject}
                      onChange={(e) => {
                        setSubject(e.target.value);
                        if (step2Errors.subject)
                          setStep2Errors({ ...step2Errors, subject: undefined });
                      }}
                      disabled={isLoading}
                      className={`w-full h-12 sm:h-[62px] rounded-[12px] sm:rounded-[15px] border-2 ${
                        step2Errors.subject
                          ? "border-red-500 dark:border-red-400"
                          : "border-black dark:border-white"
                      } bg-studymate-gray dark:bg-slate-700 px-4 font-roboto text-sm sm:text-[15px] tracking-[0.3px] sm:tracking-[0.45px] text-[#252424] dark:text-white focus:outline-none focus:ring-2 ${
                        step2Errors.subject
                          ? "focus:ring-red-500 dark:focus:ring-red-400"
                          : "focus:ring-studymate-orange dark:focus:ring-studymate-green"
                      } transition-all duration-200 appearance-none disabled:opacity-50`}
                    >
                      <option value="" disabled>
                        Subject
                      </option>
                      <option value="math">Mathematics</option>
                      <option value="science">Science</option>
                      <option value="english">English</option>
                      <option value="history">History</option>
                    </select>
                    <ChevronDown className="absolute right-3 sm:right-4 top-1/2 -translate-y-1/2 pointer-events-none w-4 h-4 sm:w-6 sm:h-6 text-[#1E1E1E] dark:text-white" strokeWidth={2} />
                  </div>
                  {step2Errors.subject && (
                    <p className="text-red-500 dark:text-red-400 text-xs sm:text-sm font-roboto">
                      {step2Errors.subject}
                    </p>
                  )}
                </div>

                <div className="flex justify-between items-center gap-3 pt-4">
                  <button
                    type="button"
                    onClick={handleBack}
                    disabled={isLoading}
                    className="w-12 h-12 sm:w-[50px] sm:h-[50px] rounded-full flex items-center justify-center bg-studymate-black dark:bg-white text-white dark:text-black hover:shadow-xl active:scale-95 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 btn-micro"
                    aria-label="Previous step"
                  >
                    <ArrowLeft className="w-5 h-5 sm:w-6 sm:h-6" strokeWidth={2} />
                  </button>
                  <button
                    type="submit"
                    disabled={
                      isLoading || !grade || !semesterType || !semester || !subject
                    }
                    className="w-12 h-12 sm:w-[50px] sm:h-[50px] rounded-full flex items-center justify-center bg-studymate-black dark:bg-white text-white dark:text-black hover:shadow-xl active:scale-95 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 btn-micro"
                    aria-label="Complete signup"
                    aria-busy={isLoading}
                  >
                    {isLoading ? (
                      <svg
                        className="animate-spin h-5 w-5 sm:h-6 sm:w-6"
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
                    ) : (
                      <ArrowRight className="w-5 h-5 sm:w-6 sm:h-6" strokeWidth={2} />
                    )}
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
