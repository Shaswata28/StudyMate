import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import Workspace from "@/components/Workspace";
import NewCourseModal from "@/components/NewCourseModal";
import ProfileModal from "@/components/ProfileModal";
import SearchCourseModal from "@/components/SearchCourseModal";
import MaterialsModal from "@/components/MaterialsModal";
import ConfirmationModal from "@/components/ConfirmationModal";
import { API_BASE_URL } from "@/lib/constants";
import { courseService } from "@/lib/courses";
import { useAuth } from "@/hooks/use-auth";
import { toast } from "@/lib/toast";
import { apiService, transformChatHistory, transformMaterials } from "@/lib/api";
import { authService } from "@/lib/auth";

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
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [courses, setCourses] = useState<Course[]>([]);
  const [activeCourse, setActiveCourse] = useState<Course | null>(null);
  const [isLoadingCourses, setIsLoadingCourses] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [isMaterialsModalOpen, setIsMaterialsModalOpen] = useState(false);
  const [isDeleteCourseModalOpen, setIsDeleteCourseModalOpen] = useState(false);
  const [isDeleteMaterialModalOpen, setIsDeleteMaterialModalOpen] = useState(false);
  const [courseToDelete, setCourseToDelete] = useState<Course | null>(null);
  const [materialToDelete, setMaterialToDelete] = useState<UploadedFile | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [pendingFiles, setPendingFiles] = useState<UploadedFile[]>([]); // Files waiting to be sent
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoadingResponse, setIsLoadingResponse] = useState(false);
  
  // Loading states for chat history and materials
  const [isLoadingChatHistory, setIsLoadingChatHistory] = useState(false);
  const [isLoadingMaterials, setIsLoadingMaterials] = useState(false);
  const [chatHistoryError, setChatHistoryError] = useState<string | null>(null);
  const [materialsError, setMaterialsError] = useState<string | null>(null);

  // Color palette for courses
  const courseColors = ["#FEAE01", "#1FC209", "#FF6B6B", "#4ECDC4", "#95E1D3", "#F38181"];

  // Load courses on mount
  useEffect(() => {
    loadCourses();
  }, []);

  // Load chat history when active course changes
  useEffect(() => {
    if (!activeCourse) {
      // Clear chat history when no course is active
      setMessages([]);
      return;
    }

    // Create AbortController for cleanup
    const abortController = new AbortController();

    // Clear previous chat history before loading new one
    setMessages([]);
    
    // Load chat history for the active course
    loadChatHistory(activeCourse.id, abortController.signal);

    // Cleanup function to abort pending requests
    return () => {
      abortController.abort();
    };
  }, [activeCourse?.id]);

  // Load materials when active course changes
  useEffect(() => {
    if (!activeCourse) {
      // Clear materials when no course is active
      setUploadedFiles([]);
      return;
    }

    // Create AbortController for cleanup
    const abortController = new AbortController();
    
    // Load materials for the active course
    loadMaterials(activeCourse.id, abortController.signal);

    // Cleanup function to abort pending requests
    return () => {
      abortController.abort();
    };
  }, [activeCourse?.id]);

  const loadCourses = async () => {
    try {
      setIsLoadingCourses(true);
      const apiCourses = await courseService.getCourses();
      
      // Convert API courses to UI courses with colors
      const uiCourses: Course[] = apiCourses.map((course, index) => ({
        id: course.id,
        name: course.name,
        color: courseColors[index % courseColors.length],
        active: false,
      }));

      setCourses(uiCourses);
      
      // Set first course as active if available
      if (uiCourses.length > 0) {
        const firstCourse = { ...uiCourses[0], active: true };
        setCourses(prev => prev.map((c, i) => i === 0 ? firstCourse : c));
        setActiveCourse(firstCourse);
      }
      
      // Log success for debugging
      console.log(`Successfully loaded ${uiCourses.length} courses`);
    } catch (error) {
      // Log detailed error for debugging
      console.error('Failed to load courses:', {
        error: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
      });
      
      // Handle different error types
      if (error instanceof Error) {
        const errorMessage = error.message;
        
        // Authentication errors (401/403) - redirect to login
        if (errorMessage.includes('Session expired') || 
            errorMessage.includes('Authentication failed') ||
            errorMessage.includes('permission')) {
          toast.error('Session expired. Please log in again.');
          authService.logout();
          navigate('/login');
          return;
        }
        
        // Network errors
        if (errorMessage.includes('Network error') || 
            errorMessage.includes('connection') ||
            errorMessage.includes('fetch')) {
          toast.error('Unable to connect. Please check your internet connection.');
        }
        // Server errors
        else if (errorMessage.includes('Something went wrong') || 
                 errorMessage.includes('500') ||
                 errorMessage.includes('503')) {
          toast.error('Something went wrong. Please try again.');
        }
        // Generic errors
        else {
          toast.error('Failed to load courses. Please try again.');
        }
      } else {
        toast.error('Failed to load courses. Please try again.');
      }
    } finally {
      setIsLoadingCourses(false);
    }
  };

  /**
   * Load chat history for a specific course
   * Fetches chat history from the backend and transforms it to frontend format
   */
  const loadChatHistory = async (courseId: string, signal?: AbortSignal) => {
    try {
      setIsLoadingChatHistory(true);
      setChatHistoryError(null);
      
      // Fetch chat history from API
      const chatHistoryRecords = await apiService.getChatHistory(courseId, signal);
      
      // Transform backend format to frontend Message format
      const transformedMessages = transformChatHistory(chatHistoryRecords);
      
      // Update messages state
      setMessages(transformedMessages);
      
      // Log success for debugging
      console.log(`Successfully loaded ${transformedMessages.length} messages for course ${courseId}`);
    } catch (error) {
      // Ignore abort errors (they're expected when switching courses)
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Chat history fetch aborted (course switched)');
        return;
      }
      
      // Log detailed error for debugging
      console.error('Failed to load chat history:', {
        courseId,
        error: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
      });
      
      // Handle different error types
      if (error instanceof Error) {
        const errorMessage = error.message;
        
        // Authentication errors (401/403) - redirect to login
        if (errorMessage.includes('Session expired') || 
            errorMessage.includes('Authentication failed') ||
            errorMessage.includes('permission')) {
          toast.error('Session expired. Please log in again.');
          authService.logout();
          navigate('/login');
          return;
        }
        
        // Network errors
        if (errorMessage.includes('Network error') || 
            errorMessage.includes('connection') ||
            errorMessage.includes('fetch')) {
          setChatHistoryError('Unable to connect. Please check your internet connection.');
          toast.error('Unable to connect. Please check your internet connection.');
        }
        // Not found errors
        else if (errorMessage.includes('not found')) {
          setChatHistoryError('Course not found.');
          toast.error('Course not found.');
        }
        // Server errors
        else if (errorMessage.includes('Something went wrong') || 
                 errorMessage.includes('500') ||
                 errorMessage.includes('503')) {
          setChatHistoryError('Something went wrong. Please try again.');
          toast.error('Something went wrong. Please try again.');
        }
        // Generic errors
        else {
          setChatHistoryError(errorMessage);
          toast.error(errorMessage);
        }
      } else {
        // Unknown error type
        const genericError = 'Failed to load chat history. Please try again.';
        setChatHistoryError(genericError);
        toast.error(genericError);
      }
      
      // Clear messages on error
      setMessages([]);
    } finally {
      setIsLoadingChatHistory(false);
    }
  };

  /**
   * Load materials for a specific course
   * Fetches materials from the backend and transforms them to frontend format
   */
  const loadMaterials = async (courseId: string, signal?: AbortSignal) => {
    try {
      setIsLoadingMaterials(true);
      setMaterialsError(null);
      
      // Fetch materials from API
      const materialRecords = await apiService.getMaterials(courseId, signal);
      
      // Transform backend format to frontend UploadedFile format
      const transformedMaterials = transformMaterials(materialRecords);
      
      // Update uploaded files state
      setUploadedFiles(transformedMaterials);
      
      // Log success for debugging with material IDs
      console.log(`Successfully loaded ${transformedMaterials.length} materials for course ${courseId}`);
      console.log('Material IDs:', transformedMaterials.map(m => ({ id: m.id, name: m.name })));
    } catch (error) {
      // Ignore abort errors (they're expected when switching courses)
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Materials fetch aborted (course switched)');
        return;
      }
      
      // Log detailed error for debugging
      console.error('Failed to load materials:', {
        courseId,
        error: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
      });
      
      // Handle different error types
      if (error instanceof Error) {
        const errorMessage = error.message;
        
        // Authentication errors (401/403) - redirect to login
        if (errorMessage.includes('Session expired') || 
            errorMessage.includes('Authentication failed') ||
            errorMessage.includes('permission')) {
          toast.error('Session expired. Please log in again.');
          authService.logout();
          navigate('/login');
          return;
        }
        
        // Network errors
        if (errorMessage.includes('Network error') || 
            errorMessage.includes('connection') ||
            errorMessage.includes('fetch')) {
          setMaterialsError('Unable to connect. Please check your internet connection.');
          toast.error('Unable to connect. Please check your internet connection.');
        }
        // Not found errors
        else if (errorMessage.includes('not found')) {
          setMaterialsError('Course not found.');
          toast.error('Course not found.');
        }
        // Server errors
        else if (errorMessage.includes('Something went wrong') || 
                 errorMessage.includes('500') ||
                 errorMessage.includes('503')) {
          setMaterialsError('Something went wrong. Please try again.');
          toast.error('Something went wrong. Please try again.');
        }
        // Generic errors
        else {
          setMaterialsError(errorMessage);
          toast.error(errorMessage);
        }
      } else {
        // Unknown error type
        const genericError = 'Failed to load materials. Please try again.';
        setMaterialsError(genericError);
        toast.error(genericError);
      }
      
      // Clear materials on error
      setUploadedFiles([]);
    } finally {
      setIsLoadingMaterials(false);
    }
  };

  /**
   * Retry loading chat history for the active course
   */
  const retryChatHistory = () => {
    if (activeCourse) {
      console.log('Retrying chat history load for course:', activeCourse.id);
      loadChatHistory(activeCourse.id);
    }
  };

  /**
   * Retry loading materials for the active course
   */
  const retryMaterials = () => {
    if (activeCourse) {
      console.log('Retrying materials load for course:', activeCourse.id);
      loadMaterials(activeCourse.id);
    }
  };

  const handleCourseSelect = (courseId: string) => {
    const updatedCourses = courses.map((c) => ({
      ...c,
      active: c.id === courseId,
    }));
    setCourses(updatedCourses);
    const selected = updatedCourses.find((c) => c.id === courseId);
    if (selected) {
      setActiveCourse(selected);
      // Note: Chat history and materials will be cleared and reloaded by useEffect hooks
    }
  };

  const handleAddCourse = async (courseName: string, color: string) => {
    try {
      // Create course via API
      const apiCourse = await courseService.createCourse({ name: courseName });
      
      // Add to UI with the provided color
      const newCourse: Course = {
        id: apiCourse.id,
        name: apiCourse.name,
        color: color,
        active: false,
      };

      setCourses((prev) => [...prev, newCourse]);
      toast.success(`Course "${courseName}" created successfully!`);
      
      // Log success for debugging
      console.log(`Successfully created course: ${courseName} (${apiCourse.id})`);
    } catch (error) {
      // Log detailed error for debugging
      console.error('Failed to create course:', {
        courseName,
        error: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
      });
      
      // Handle different error types
      if (error instanceof Error) {
        const errorMessage = error.message;
        
        // Authentication errors (401/403) - redirect to login
        if (errorMessage.includes('Session expired') || 
            errorMessage.includes('Authentication failed') ||
            errorMessage.includes('permission')) {
          toast.error('Session expired. Please log in again.');
          authService.logout();
          navigate('/login');
          return;
        }
        
        // Network errors
        if (errorMessage.includes('Network error') || 
            errorMessage.includes('connection') ||
            errorMessage.includes('fetch')) {
          toast.error('Unable to connect. Please check your internet connection.');
        }
        // Server errors
        else if (errorMessage.includes('Something went wrong') || 
                 errorMessage.includes('500') ||
                 errorMessage.includes('503')) {
          toast.error('Something went wrong. Please try again.');
        }
        // Generic errors
        else {
          toast.error('Failed to create course. Please try again.');
        }
      } else {
        toast.error('Failed to create course. Please try again.');
      }
    }
  };

  const handleDeleteCourse = (courseId: string) => {
    // Find the course to get its name
    const course = courses.find((c) => c.id === courseId);
    if (course) {
      setCourseToDelete(course);
      setIsDeleteCourseModalOpen(true);
    }
  };

  const confirmDeleteCourse = async () => {
    if (!courseToDelete) return;

    const courseId = courseToDelete.id;
    const courseName = courseToDelete.name;

    // Optimistically remove from UI
    setCourses((prev) => prev.filter((c) => c.id !== courseId));
    
    // If the deleted course was active, clear it
    if (activeCourse?.id === courseId) {
      setActiveCourse(null);
      setMessages([]);
      setUploadedFiles([]);
    }

    try {
      // Delete from backend
      const token = authService.getAccessToken();
      const response = await fetch(`${API_BASE_URL}/courses/${courseId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        // Handle authentication errors
        if (response.status === 401 || response.status === 403) {
          toast.error('Session expired. Please log in again.');
          authService.logout();
          navigate('/login');
          return;
        }
        throw new Error("Failed to delete course");
      }

      toast.success(`"${courseName}" deleted successfully`);
      console.log(`Course deleted: ${courseId}`);
    } catch (error) {
      console.error("Failed to delete course:", error);
      toast.error(`Failed to delete "${courseName}"`);
      
      // Restore the course in UI if deletion failed
      setCourses((prev) => [...prev, courseToDelete]);
      // If it was the active course, restore it
      if (activeCourse?.id === courseId) {
        setActiveCourse(courseToDelete);
      }
    }
  };

  const handleFileUpload = (files: File[]) => {
    // Keep files as pending attachments - they will be sent with the next message
    // This prevents immediate processing by brain.py
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
    // Find the file to get its name
    const file = uploadedFiles.find((f) => f.id === fileId);
    if (file) {
      setMaterialToDelete(file);
      setIsDeleteMaterialModalOpen(true);
    }
  };

  const confirmDeleteMaterial = async () => {
    if (!materialToDelete) return;

    const fileId = materialToDelete.id;
    const fileName = materialToDelete.name;

    // Check if this is a pending file (temporary ID) or a saved material (UUID)
    // Pending files have format: {timestamp}-{random}-{index} (e.g., 1733654321000-abc123-0)
    // Saved materials have UUID format (e.g., 651b0234-b8d6-472c-b15d-013668541286)
    // Key difference: pending files start with a 13-digit timestamp
    const isPendingFile = /^\d{13}-/.test(fileId);
    
    console.log('Delete material:', { fileId, fileName, isPendingFile });

    // Optimistically remove from UI
    setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
    setPendingFiles((prev) => prev.filter((f) => f.id !== fileId));

    try {
      // Only call backend if this is a real material (not a pending file)
      if (!isPendingFile) {
        // Delete from backend
        const token = authService.getAccessToken();
        const url = `${API_BASE_URL}/materials/${fileId}`;
        
        console.log('Calling DELETE endpoint:', url);
        
        const response = await fetch(url, {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        console.log('DELETE response:', {
          status: response.status,
          statusText: response.statusText,
          ok: response.ok
        });

        if (!response.ok) {
          // Handle authentication errors
          if (response.status === 401 || response.status === 403) {
            toast.error('Session expired. Please log in again.');
            authService.logout();
            navigate('/login');
            return;
          }
          
          const errorText = await response.text();
          console.error('DELETE failed:', errorText);
          throw new Error(`Failed to delete material: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();
        console.log('DELETE success:', result);
        
        toast.success(`${fileName} deleted successfully`);
        console.log(`Material deleted: ${fileId}`);
      } else {
        console.log('Skipping backend delete for pending file');
      }
    } catch (error) {
      console.error("Failed to delete material:", error);
      toast.error(`Failed to delete ${fileName}`);
      
      // Restore the file in UI if deletion failed
      setUploadedFiles((prev) => [...prev, materialToDelete]);
    }
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

      // Save reference to pending files before clearing
      const filesToSend = pendingFiles.filter((f) => f.file);
      
      // Convert pending files to base64 attachments
      const attachments = await Promise.all(
        filesToSend.map(async (f) => ({
          filename: f.name,
          mime_type: f.type,
          data: await convertFileToBase64(f.file!),
        }))
      );

      // Clear pending files after converting
      setPendingFiles([]);

      // Get authentication token
      const token = authService.getAccessToken();
      
      // Call FastAPI backend with course-specific endpoint to save chat history
      // Use course-specific endpoint if we have an active course, otherwise use general endpoint
      const endpoint = activeCourse 
        ? `${API_BASE_URL}/courses/${activeCourse.id}/chat`
        : `${API_BASE_URL}/chat`;
      
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
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

        // Save attachments as materials after successful message send
        // This ensures materials are only saved when actually used
        if (attachments.length > 0 && activeCourse) {
          for (const attachment of attachments) {
            try {
              // Find the original file from the saved reference
              const originalFile = filesToSend.find(f => f.name === attachment.filename);
              if (originalFile && originalFile.file) {
                // Upload to materials endpoint
                const formData = new FormData();
                formData.append('file', originalFile.file);

                const materialResponse = await fetch(
                  `${API_BASE_URL}/courses/${activeCourse.id}/materials`,
                  {
                    method: 'POST',
                    headers: {
                      'Authorization': `Bearer ${token}`,
                    },
                    body: formData,
                  }
                );

                if (materialResponse.ok) {
                  const uploadedMaterial = await materialResponse.json();
                  console.log(`Material saved: ${uploadedMaterial.name} (${uploadedMaterial.id})`);
                  
                  // Update the uploaded file with the real material ID
                  setUploadedFiles((prev) =>
                    prev.map((f) =>
                      f.name === attachment.filename && f.file
                        ? {
                            id: uploadedMaterial.id,
                            name: uploadedMaterial.name,
                            type: uploadedMaterial.file_type,
                          }
                        : f
                    )
                  );
                } else {
                  console.warn(`Failed to save material: ${attachment.filename}`);
                }
              }
            } catch (error) {
              console.error(`Error saving material ${attachment.filename}:`, error);
              // Don't fail the whole message send if material save fails
            }
          }
        }
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
            onCourseDelete={handleDeleteCourse}
            isCollapsed={sidebarCollapsed}
            onToggle={toggleSidebar}
            onNewCourseClick={() => setIsModalOpen(true)}
            onSearchCourseClick={() => setIsSearchModalOpen(true)}
            onProfileClick={() => setIsProfileModalOpen(true)}
          />
        </div>

        <div className="flex-1 flex flex-col overflow-hidden relative transition-all duration-300 ease-in-out">
          <Header 
            courseName={activeCourse?.name}
            courseColor={activeCourse?.color}
            uploadedFiles={uploadedFiles}
            onMaterialsClick={activeCourse ? () => setIsMaterialsModalOpen(true) : undefined}
          />
          {isLoadingCourses ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-studymate-black dark:border-white mx-auto mb-4"></div>
                <p className="font-audiowide text-[14px] tracking-[1.4px] text-black/60 dark:text-white/60">
                  Loading courses...
                </p>
              </div>
            </div>
          ) : !activeCourse ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center max-w-md px-4">
                <h2 className="font-audiowide text-[24px] tracking-[2.4px] text-black dark:text-white mb-4">
                  No Courses Yet
                </h2>
                <p className="font-roboto text-[14px] text-black/60 dark:text-white/60 mb-6">
                  Create your first course to get started with StudyMate
                </p>
                <button
                  onClick={() => setIsModalOpen(true)}
                  className="px-6 py-3 bg-studymate-black dark:bg-white text-white dark:text-black font-audiowide text-[13px] tracking-[1.3px] rounded hover:shadow-lg transition-all duration-200"
                >
                  Create Course
                </button>
              </div>
            </div>
          ) : (
            <Workspace
              courseName={activeCourse.name}
              courseColor={activeCourse.color}
              uploadedFiles={uploadedFiles}
              pendingFiles={pendingFiles}
              messages={messages}
              onSendMessage={handleSendMessage}
              onFileUpload={handleFileUpload}
              onRemovePendingFile={handleRemovePendingFile}
              isLoadingResponse={isLoadingResponse}
              isLoadingChatHistory={isLoadingChatHistory}
              isLoadingMaterials={isLoadingMaterials}
              chatHistoryError={chatHistoryError}
              materialsError={materialsError}
              onRetryChatHistory={retryChatHistory}
              onRetryMaterials={retryMaterials}
            />
          )}
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
        isLoadingMaterials={isLoadingMaterials}
        materialsError={materialsError}
        onRetryMaterials={retryMaterials}
      />

      <ConfirmationModal
        isOpen={isDeleteCourseModalOpen}
        onClose={() => {
          setIsDeleteCourseModalOpen(false);
          setCourseToDelete(null);
        }}
        onConfirm={confirmDeleteCourse}
        title="Delete Course?"
        message={`Are you sure you want to delete "${courseToDelete?.name}"? This will permanently delete all chat history and materials for this course. This action cannot be undone.`}
        confirmText="Delete Course"
        cancelText="Cancel"
        variant="danger"
      />

      <ConfirmationModal
        isOpen={isDeleteMaterialModalOpen}
        onClose={() => {
          setIsDeleteMaterialModalOpen(false);
          setMaterialToDelete(null);
        }}
        onConfirm={confirmDeleteMaterial}
        title="Delete Material?"
        message={`Are you sure you want to delete "${materialToDelete?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </>
  );
}
