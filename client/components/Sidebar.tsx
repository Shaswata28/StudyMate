import { Menu, Edit, Search } from "lucide-react";
import UserProfile from "./UserProfile";

interface Course {
  id: string;
  name: string;
  color: string;
  active?: boolean;
}

interface SidebarProps {
  courses: Course[];
  onCourseSelect?: (courseId: string) => void;
  isCollapsed: boolean;
  onToggle: () => void;
  onNewCourseClick?: () => void;
  onProfileClick?: () => void;
}

export default function Sidebar({
  courses,
  onCourseSelect,
  isCollapsed,
  onToggle,
  onNewCourseClick,
  onProfileClick
}: SidebarProps) {
  return (
    <aside 
      className={`h-screen bg-white border-r border-black/10 flex flex-col opacity-75 transition-all duration-300 ease-in-out ${
        isCollapsed ? 'w-[58px]' : 'w-full lg:w-[276px]'
      }`}
    >
      {/* Sidebar Toggle */}
      <div className="p-4">
        <button 
          className="p-1 hover:bg-gray-100 rounded transition-colors"
          onClick={onToggle}
          aria-label="Toggle sidebar"
        >
          <Menu className="w-7 h-7 text-studymate-black" strokeWidth={3} />
        </button>
      </div>

      {/* New Course */}
      <div 
        className="px-4 py-3 flex items-center gap-3 cursor-pointer hover:bg-gray-50 transition-colors overflow-hidden"
        onClick={onNewCourseClick}
      >
        <Edit className="w-7 h-7 text-studymate-black flex-shrink-0" strokeWidth={3} />
        {!isCollapsed && (
          <span className="font-audiowide text-[19px] text-black whitespace-nowrap">
            New Course
          </span>
        )}
      </div>

      {/* Search Course */}
      <div className="px-4 py-3 flex items-center gap-3 cursor-pointer hover:bg-gray-50 transition-colors overflow-hidden">
        <Search className="w-7 h-7 text-studymate-black flex-shrink-0" strokeWidth={3} />
        {!isCollapsed && (
          <span className="font-audiowide text-[19px] text-black whitespace-nowrap">
            Search Course
          </span>
        )}
      </div>

      {/* Divider - only show when expanded */}
      {!isCollapsed && <div className="mx-4 my-4 border-t border-black/50" />}

      {/* Courses Section */}
      <div className="px-4 overflow-hidden">
        {!isCollapsed && (
          <h2 className="font-audiowide text-2xl text-black mb-4">Courses</h2>
        )}

        {/* Course List */}
        <div className={`space-y-2 ${isCollapsed ? 'flex flex-col items-center' : ''}`}>
          {courses.map((course) => (
            <div
              key={course.id}
              className={`flex items-center gap-3 p-2 rounded cursor-pointer transition-colors ${
                course.active && !isCollapsed ? "bg-studymate-gray" : "hover:bg-gray-50"
              } ${isCollapsed ? 'justify-center' : ''}`}
              onClick={() => onCourseSelect?.(course.id)}
            >
              <div
                className={`rounded-full flex-shrink-0 ${
                  isCollapsed ? 'w-3 h-3' : 'w-3 h-3'
                }`}
                style={{ backgroundColor: course.color }}
              />
              {!isCollapsed && (
                <span className="font-audiowide text-[19px] text-black whitespace-nowrap">
                  {course.name}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* User Profile Section */}
      <div className={`px-4 pb-6 ${isCollapsed ? 'flex justify-center' : ''}`}>
        <UserProfile
          userName="Arnob Das"
          userPlan="free"
          isCollapsed={isCollapsed}
          onProfileModalOpen={onProfileClick}
        />
      </div>
    </aside>
  );
}
