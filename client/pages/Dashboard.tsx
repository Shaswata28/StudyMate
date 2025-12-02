import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import Workspace from "@/components/Workspace";
import NewCourseModal from "@/components/NewCourseModal";
import ProfileModal from "@/components/ProfileModal";
import SearchCourseModal from "@/components/SearchCourseModal";
import MaterialsModal from "@/components/MaterialsModal";
import { API_BASE_URL } from "@/lib/constants";

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
  file?: File; // Store the actual File object for sending to API
}

interface Message {
  id: string;
  text: string;
  isAI: boolean;
  timestamp?: Date;
  attachments?: { name: string; type: string }[]; // Files attached to this message
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
  const [pendingFiles, setPendingFiles] = useState<UploadedFile[]>([]); // Files waiting to be sent
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
      file: file, // Store the actual File object
    }));

    setUploadedFiles((prev) => [...prev, ...newFiles]);
    setPendingFiles((prev) => [...prev, ...newFiles]); // Add to pending files
  };

  const handleRemoveFile = (fileId: string) => {
    setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
    setPendingFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const handleRemovePendingFile = (fileId: string) => {
    setPendingFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const convertFileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const base64 = reader.result as string;
        // Remove the data:image/jpeg;base64, prefix
        const base64Data = base64.split(',')[1];
        resolve(base64Data);
      };
      reader.onerror = (error) => reject(error);
    });
  };

  const handleSendMessage = async (message: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      text: message,
      isAI: false,
      timestamp: new Date(),
      attachments: pendingFiles.map((f) => ({ name: f.name, type: f.type })),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoadingResponse(true);

    try {
      // Format conversation history (last 10 messages) for the API
      const history = messages.slice(-10).map((msg) => ({
        role: msg.isAI ? "model" : "user",
        content: msg.text,
      }));

      // Convert pending files to base64 attachments
      const attachments = await Promise.all(
        pendingFiles
          .filter((f) => f.file) // Only process files with File object
          .map(async (f) => ({
            filename: f.name,
            mime_type: f.type,
            data: await convertFileToBase64(f.file!),
          }))
      );

      // Clear pending files after converting
      setPendingFiles([]);

      // Call FastAPI backend
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: message,
          history: history,
          attachments: attachments.length > 0 ? attachments : undefined,
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
            pendingFiles={pendingFiles}
            messages={messages}
            onSendMessage={handleSendMessage}
            onFileUpload={handleFileUpload}
            onRemovePendingFile={handleRemovePendingFile}
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
        onRemoveFile={handleRemoveFile}
      />
    </>
  );
}
