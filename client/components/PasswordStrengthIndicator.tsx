export function getPasswordStrength(password: string): {
    score: number;
    label: string;
    color: string;
  } {
    let score = 0;
  
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[^a-zA-Z\d]/.test(password)) score++;
  
    const strength = Math.min(Math.ceil((score / 5) * 4), 4);
  
    const strengthMap = {
      0: { label: "Very Weak", color: "bg-red-500" },
      1: { label: "Weak", color: "bg-orange-500" },
      2: { label: "Fair", color: "bg-yellow-500" },
      3: { label: "Good", color: "bg-blue-500" },
      4: { label: "Strong", color: "bg-green-500" },
    };
  
    return {
      score: strength,
      label: strengthMap[strength].label,
      color: strengthMap[strength].color,
    };
  }
  
  interface PasswordStrengthIndicatorProps {
    password: string;
  }
  
  export default function PasswordStrengthIndicator({
    password,
  }: PasswordStrengthIndicatorProps) {
    if (!password) return null;
  
    const { score, label, color } = getPasswordStrength(password);
  
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-audiowide tracking-[0.6px] text-[#666] dark:text-gray-400">
            Password Strength
          </span>
          <span
            className={`text-xs font-audiowide tracking-[0.6px] ${
              score === 0
                ? "text-red-500"
                : score === 1
                ? "text-orange-500"
                : score === 2
                ? "text-yellow-600"
                : score === 3
                ? "text-blue-600"
                : "text-green-600"
            }`}
          >
            {label}
          </span>
        </div>
        <div className="h-2 bg-gray-200 dark:bg-slate-600 rounded-full overflow-hidden">
          <div
            className={`h-full ${color} transition-all duration-300 ease-out`}
            style={{ width: `${((score + 1) / 5) * 100}%` }}
          />
        </div>
      </div>
    );
  }
  