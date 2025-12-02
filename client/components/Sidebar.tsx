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
  onSearchCourseClick?: () => void;
  onProfileClick?: () => void;
}

export default function Sidebar({
  courses,
  onCourseSelect,
  isCollapsed,
  onToggle,
  onNewCourseClick,
  onSearchCourseClick,
  onProfileClick
}: SidebarProps) {
  return (
    <aside
      className={`h-screen bg-white dark:bg-slate-900 border-r border-black/10 dark:border-slate-700 flex flex-col opacity-75 dark:opacity-100 transition-all duration-300 ease-in-out ${
        isCollapsed ? 'w-[58px]' : 'w-full lg:w-[276px]'
      }`}
      role="navigation"
      aria-label="Sidebar"
    >
      {/* Sidebar Toggle */}
      <div className="p-4">
        <button
          className="p-1 hover:bg-gray-100 dark:hover:bg-slate-800 rounded transition-colors btn-micro"
          onClick={onToggle}
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-expanded={!isCollapsed}
        >
          <Menu className="w-7 h-7 text-studymate-black dark:text-white" strokeWidth={3} />
        </button>
      </div>

      {/* New Course */}
      <button
        className="px-4 py-3 flex items-center gap-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors overflow-hidden btn-micro w-full text-left"
        onClick={onNewCourseClick}
        aria-label="Create new course"
      >
        <Edit className="w-7 h-7 text-studymate-black dark:text-white flex-shrink-0" strokeWidth={3} />
        {!isCollapsed && (
          <span className="font-audiowide text-[19px] text-black dark:text-white whitespace-nowrap">
            New Course
          </span>
        )}
      </button>

      {/* Search Course */}
      <button
        className="px-4 py-3 flex items-center gap-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors overflow-hidden btn-micro w-full text-left"
        onClick={onSearchCourseClick}
        aria-label="Search course"
      >
        <Search className="w-7 h-7 text-studymate-black dark:text-white flex-shrink-0" strokeWidth={3} />
        {!isCollapsed && (
          <span className="font-audiowide text-[19px] text-black dark:text-white whitespace-nowrap">
            Search Course
          </span>
        )}
      </button>

      {/* Divider - only show when expanded */}
      {!isCollapsed && <div className="mx-4 my-4 border-t border-black/20 dark:border-slate-700" />}

      {/* Courses Section */}
      <div className="px-4 overflow-hidden">
        {!isCollapsed && (
          <h2 className="font-audiowide text-2xl text-black dark:text-white mb-4">Courses</h2>
        )}

        {/* Course List */}
        <div
          className={`space-y-2 ${isCollapsed ? 'flex flex-col items-center' : ''}`}
          role="list"
        >
          {courses.map((course) => (
            <button
              key={course.id}
              className={`flex items-center gap-3 p-2 rounded cursor-pointer transition-all duration-200 w-full ${
                course.active && !isCollapsed ? "bg-studymate-gray dark:bg-slate-700" : "hover:bg-gray-50 dark:hover:bg-slate-800"
              } ${isCollapsed ? 'justify-center' : ''} btn-micro`}
              onClick={() => onCourseSelect?.(course.id)}
              aria-label={`Select course ${course.name}`}
              aria-current={course.active ? "page" : undefined}
              role="listitem"
            >
              <div
                className={`rounded-full flex-shrink-0 ${
                  isCollapsed ? 'w-3 h-3' : 'w-3 h-3'
                }`}
                style={{ backgroundColor: course.color }}
                aria-hidden="true"
              />
              {!isCollapsed && (
                <span className="font-audiowide text-[19px] text-black dark:text-white whitespace-nowrap">
                  {course.name}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* User Profile Section */}
      <div className={`px-4 pb-6 ${isCollapsed ? 'flex justify-center' : ''}`}>
        <UserProfile
          isCollapsed={isCollapsed}
          onProfileModalOpen={onProfileClick}
        />
      </div>
    </aside>
  );
}
