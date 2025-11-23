import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import Workspace from "@/components/Workspace";
import NewCourseModal from "@/components/NewCourseModal";
import ProfileModal from "@/components/ProfileModal";
import SearchCourseModal from "@/components/SearchCourseModal";
import MaterialsModal from "@/components/MaterialsModal";

interface Course {
  id: string;
  name: string;
  color: string;
  active?: boolean;
}

interface UploadedFile {
  id: string;
  name: string;
  type: string;
}

interface Message {
  id: string;
  text: string;
  isAI: boolean;
  timestamp?: Date;
}

export default function Dashboard() {
  const [courses, setCourses] = useState<Course[]>([
    { id: "1", name: "CSE 312", color: "#FEAE01", active: true },
    { id: "2", name: "CSE 123", color: "#1FC209", active: false },
  ]);

  const [activeCourse, setActiveCourse] = useState<Course>(courses[0]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [isMaterialsModalOpen, setIsMaterialsModalOpen] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoadingResponse, setIsLoadingResponse] = useState(false);

  const handleCourseSelect = (courseId: string) => {
    const updatedCourses = courses.map((c) => ({
      ...c,
      active: c.id === courseId,
    }));
    setCourses(updatedCourses);
    const selected = updatedCourses.find((c) => c.id === courseId);
    if (selected) {
      setActiveCourse(selected);
      // Clear conversation history when switching courses
      setMessages([]);
    }
  };

  const handleAddCourse = (courseName: string, color: string) => {
    const newCourse: Course = {
      id: Date.now().toString(),
      name: courseName,
      color: color,
      active: false,
    };

    setCourses((prev) => [...prev, newCourse]);
  };

  const handleFileUpload = (files: File[]) => {
    const newFiles = files.map((file, index) => ({
      id: `${Date.now()}-${Math.random().toString(36).substring(2, 9)}-${index}`,
      name: file.name,
      type: file.type || "application/octet-stream",
    }));

    setUploadedFiles((prev) => [...prev, ...newFiles]);

    if (!isMaterialsModalOpen) {
      setIsMaterialsModalOpen(true);
    }
  };

  const handleSendMessage = async (message: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      text: message,
      isAI: false,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoadingResponse(true);

    try {
      // Format conversation history (last 10 messages) for the API
      const history = messages.slice(-10).map((msg) => ({
        role: msg.isAI ? "model" : "user",
        content: msg.text,
      }));

      // Call FastAPI backend
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: message,
          history: history,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        // Handle error responses by displaying error as AI message
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: data.error || "Something went wrong. Please try again.",
          isAI: true,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      } else {
        // Handle success response
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          text: data.response,
          isAI: true,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, aiResponse]);
      }
    } catch (error) {
      // Handle network errors
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "I'm having trouble connecting right now. Please try again.",
        isAI: true,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoadingResponse(false);
    }
  };

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  return (
    <>
      <div className="h-screen w-screen bg-white dark:bg-slate-950 flex overflow-hidden">
        <div className="flex-shrink-0">
          <Sidebar
            courses={courses}
            onCourseSelect={handleCourseSelect}
            isCollapsed={sidebarCollapsed}
            onToggle={toggleSidebar}
            onNewCourseClick={() => setIsModalOpen(true)}
            onSearchCourseClick={() => setIsSearchModalOpen(true)}
            onProfileClick={() => setIsProfileModalOpen(true)}
          />
        </div>

        <div className="flex-1 flex flex-col overflow-hidden relative transition-all duration-300 ease-in-out">
          <Header />
          <Workspace
            courseName={activeCourse.name}
            courseColor={activeCourse.color}
            uploadedFiles={uploadedFiles}
            messages={messages}
            onSendMessage={handleSendMessage}
            onFileUpload={handleFileUpload}
            onMaterialsClick={() => setIsMaterialsModalOpen(true)}
            isLoadingResponse={isLoadingResponse}
          />
        </div>
      </div>

      <NewCourseModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleAddCourse}
      />

      <SearchCourseModal
        isOpen={isSearchModalOpen}
        onClose={() => setIsSearchModalOpen(false)}
        courses={courses}
        onCourseSelect={handleCourseSelect}
      />

      <ProfileModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
      />

      <MaterialsModal
        isOpen={isMaterialsModalOpen}
        onClose={() => setIsMaterialsModalOpen(false)}
        files={uploadedFiles}
      />
    </>
  );
}
