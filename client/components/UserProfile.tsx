import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { LogOut, Settings, HelpCircle, Info } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";

interface UserProfileProps {
  isCollapsed: boolean;
  onProfileModalOpen?: () => void;
}

export default function UserProfile({
  isCollapsed,
  onProfileModalOpen,
}: UserProfileProps) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Extract user name from email (part before @)
  const getUserName = (email: string) => {
    const namePart = email.split('@')[0];
    // Convert to title case (e.g., "john.doe" -> "John Doe")
    return namePart
      .split(/[._-]/)
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const userName = user?.email ? getUserName(user.email) : "User";
  
  // Get initials from user name
  const initials = userName
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
      setIsOpen(false);
      navigate("/login");
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  const handleOpenModal = () => {
    setIsOpen(false);
    onProfileModalOpen?.();
  };

  return (
    <div className={`relative ${isCollapsed ? "flex justify-center" : ""}`} ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-3 p-2 rounded cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors ${
          isCollapsed ? "w-[40px] h-[40px] justify-center" : ""
        }`}
        aria-label="User profile menu"
      >
        {/* Avatar */}
        <div className="w-8 h-8 rounded-full bg-[#2C2C2C] dark:bg-slate-600 text-white flex items-center justify-center flex-shrink-0 font-audiowide text-[12px] font-bold">
          {initials}
        </div>

        {/* User Info - only show when expanded */}
        {!isCollapsed && user && (
          <div className="flex flex-col text-left overflow-hidden">
            <span className="font-audiowide text-[13px] text-black dark:text-white truncate font-semibold">
              {userName}
            </span>
            <span className="font-roboto text-[11px] text-[#666] dark:text-gray-400 truncate">
              {user.email}
            </span>
            <span className="font-audiowide text-[10px] text-[#333232] dark:text-gray-500 uppercase tracking-wider">
              Free Tier
            </span>
          </div>
        )}
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute bottom-full mb-2 left-0 w-48 bg-white dark:bg-slate-800 rounded-lg border border-black/20 dark:border-slate-600 shadow-lg dark:shadow-2xl z-50 transition-colors duration-200">
          <div className="py-2">
            {/* Settings, About, Help */}
            <button
              onClick={handleOpenModal}
              className="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors text-left border-b border-black/10 dark:border-slate-600"
            >
              <Settings className="w-5 h-5 text-[#1E1E1E] dark:text-white" strokeWidth={2} />
              <span className="font-audiowide text-[14px] text-black dark:text-white">
                Settings
              </span>
            </button>

            <button
              onClick={handleOpenModal}
              className="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors text-left border-b border-black/10 dark:border-slate-600"
            >
              <HelpCircle className="w-5 h-5 text-[#1E1E1E] dark:text-white" strokeWidth={2} />
              <span className="font-audiowide text-[14px] text-black dark:text-white">Help</span>
            </button>

            <button
              onClick={handleOpenModal}
              className="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors text-left border-b border-black/10 dark:border-slate-600"
            >
              <Info className="w-5 h-5 text-[#1E1E1E] dark:text-white" strokeWidth={2} />
              <span className="font-audiowide text-[14px] text-black dark:text-white">About</span>
            </button>

            {/* Logout */}
            <button
              onClick={handleLogout}
              className="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors text-left"
            >
              <LogOut className="w-5 h-5 text-[#1E1E1E] dark:text-white" strokeWidth={2} />
              <span className="font-audiowide text-[14px] text-black dark:text-white">
                Logout
              </span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
