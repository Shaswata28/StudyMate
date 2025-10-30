import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import Workspace from "@/components/Workspace";
import NewCourseModal from "@/components/NewCourseModal";
import ProfileModal from "@/components/ProfileModal";

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
}

export default function Dashboard() {
  const [courses, setCourses] = useState<Course[]>([
    { id: "1", name: "CSE 312", color: "#FEAE01", active: true },
    { id: "2", name: "CSE 123", color: "#1FC209", active: false },
  ]);

  const [activeCourse, setActiveCourse] = useState<Course>(courses[0]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [materialsPanelOpen, setMaterialsPanelOpen] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);

  const handleCourseSelect = (courseId: string) => {
    const updatedCourses = courses.map((c) => ({
      ...c,
      active: c.id === courseId,
    }));
    setCourses(updatedCourses);
    const selected = updatedCourses.find((c) => c.id === courseId);
    if (selected) {
      setActiveCourse(selected);
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
    const newFiles = files.map((file) => ({
      id: Date.now().toString() + Math.random(),
      name: file.name,
      type: file.type || "application/octet-stream",
    }));

    setUploadedFiles((prev) => [...prev, ...newFiles]);
    
    if (!materialsPanelOpen) {
      setMaterialsPanelOpen(true);
    }
  };

  const handleSendMessage = (message: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      text: message,
      isAI: false,
    };

    const aiResponse: Message = {
      id: (Date.now() + 1).toString(),
      text: `This is a sample AI based response on the uploaded material. For more accurate response please connect backend API.\n• Sample list 1\n• Sample list 2\nplease leave a review for better response`,
      isAI: true,
    };

    setMessages((prev) => [...prev, userMessage, aiResponse]);
  };

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const toggleMaterialsPanel = () => {
    setMaterialsPanelOpen(!materialsPanelOpen);
  };

  return (
    <>
      <div className="h-screen w-screen bg-white flex overflow-hidden">
        <div className="flex-shrink-0">
          <Sidebar
            courses={courses}
            onCourseSelect={handleCourseSelect}
            isCollapsed={sidebarCollapsed}
            onToggle={toggleSidebar}
            onNewCourseClick={() => setIsModalOpen(true)}
            onProfileClick={() => setIsProfileModalOpen(true)}
          />
        </div>

        <div className="flex-1 flex flex-col overflow-hidden relative">
          <Header />
          <Workspace
            courseName={activeCourse.name}
            courseColor={activeCourse.color}
            subtitle="Upload course materials to get started"
            uploadedFiles={uploadedFiles}
            messages={messages}
            onSendMessage={handleSendMessage}
            onFileUpload={handleFileUpload}
            materialsPanelOpen={materialsPanelOpen}
            onMaterialsToggle={toggleMaterialsPanel}
          />
        </div>
      </div>

      <NewCourseModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleAddCourse}
      />

      <ProfileModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
      />
    </>
  );
}
