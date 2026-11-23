"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useStore, Course } from "@/store/useStore";
import { api, type CourseSource, type DiagramOrigin } from "@/lib/api";
import { toast } from "sonner";

import Sidebar from "@/components/dashboard/Sidebar";
import Header from "@/components/dashboard/Header";
import ChatContainer from "@/components/chat/ChatContainer";
import ChatInput from "@/components/chat/ChatInput";
import NewCourseModal from "@/components/modals/NewCourseModal";
import MaterialsSidebar from "@/components/dashboard/MaterialsSidebar";
import DiagramStudio, { type DiagramSelection } from "@/components/dashboard/DiagramStudio";
import PracticeStudio from "@/components/dashboard/PracticeStudio";
import StudyOverview from "@/components/dashboard/StudyOverview";
import SearchCourseModal from "@/components/modals/SearchCourseModal";
import MessageBubble, { MessageProps } from "@/components/chat/MessageBubble";

export default function WorkspacePage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { activeCourse, setActiveCourse, isMaterialsOpen, setIsMaterialsOpen } = useStore();

  const [practice, setPractice] = useState<{ courseId: string; origin?: DiagramOrigin }>();
  const [diagram, setDiagram] = useState<DiagramSelection>();
  const [savedCourseId, setSavedCourseId] = useState<string>();
  const [source, setSource] = useState<CourseSource | null>(null);
  const [newReplyId, setNewReplyId] = useState<string>();
  const [coursesVisible, setCoursesVisible] = useState(true);

  useEffect(() => {
    setCoursesVisible(matchMedia("(min-width: 1280px)").matches);
  }, []);

  const courseId = activeCourse?.id;
  useEffect(() => {
    setDiagram(undefined);
    setSource(null);
    setIsMaterialsOpen(!!courseId && matchMedia("(min-width: 1280px)").matches);
  }, [courseId, setIsMaterialsOpen]);

  const view = courseId && savedCourseId === courseId ? "saved" : "chat";

  function selectCourse(course: Course) {
    setSavedCourseId(undefined);
    setActiveCourse(course);
    if (!matchMedia("(min-width: 1280px)").matches) setCoursesVisible(false);
  }

  function collapsePanels() {
    setCoursesVisible(false);
    setIsMaterialsOpen(false);
  }

  function openSource(next: CourseSource) {
    setSource(next);
    setIsMaterialsOpen(true);
  }

  const uploads = useRef(new WeakMap<File, { courseId: string; id: string }>());
  const sendLock = useRef(false);
  const [pending, setPending] = useState<{ courseId: string; message: MessageProps } | null>(null);

  const { data: profile, isError: profileError, refetch: retryProfile } = useQuery({
    queryKey: ["profile"], queryFn: api.getProfile,
  });
  const { data: settings } = useQuery({ queryKey: ["settings"], queryFn: api.getSettings });
  useEffect(() => {
    if (profile === null) router.replace("/onboarding");
  }, [profile, router]);

  // 1. Fetch courses
  const { data: courses = [], isPending: coursesPending } = useQuery({
    queryKey: ["courses"],
    queryFn: api.listCourses,
    enabled: !!profile,
  });

  // 2. Fetch Chat History when active course changes
  const { data: historyData, isError: historyError, isPending: historyPending, refetch: reloadHistory } = useQuery({
    queryKey: ["chat_history", activeCourse?.id],
    queryFn: () => (activeCourse ? api.getChatHistory(activeCourse.id) : Promise.resolve([])),
    enabled: !!activeCourse,
  });

  const messages: MessageProps[] = (historyData ?? []).flatMap((record) =>
    record.history.map((message, index) => ({
      id: `${record.id}-${index}`,
      role: message.role === "user" ? "user" : "model",
      content: message.content,
      timestamp: record.created_at,
      turnId: record.id,
      bookmarked: Boolean(record.bookmarked),
      sources: message.sources,
    })),
  );
  const sendingInActiveCourse = pending !== null && pending.courseId === activeCourse?.id;
  if (pending && sendingInActiveCourse) messages.push(pending.message);

  const bookmarks = useMutation({
    mutationFn: ({ course, id, saved }: { course: string; id: number; saved: boolean }) => api.setBookmark(course, id, saved),
    onSuccess: (_, { course }) => queryClient.invalidateQueries({ queryKey: ["chat_history", course] }),
    onError: (error) => toast.error(error.message),
  });
  const saveAnswer = (id: number, saved: boolean) => {
    if (courseId && !bookmarks.isPending) bookmarks.mutate({ course: courseId, id, saved });
  };

  // 3. Course Mutations
  const createCourseMutation = useMutation({
    mutationFn: (data: Omit<Course, "id">) => api.createCourse(data),
    onSuccess: (newCourse) => {
      queryClient.invalidateQueries({ queryKey: ["courses"] });
      queryClient.invalidateQueries({ queryKey: ["study"] });
      selectCourse(newCourse);
      toast.success(`Course "${newCourse.name}" created!`);
    },
    onError: (err: any) => toast.error(err.message || "Failed to create course"),
  });

  const deleteDialog = useRef<HTMLDialogElement>(null);
  const [courseToDelete, setCourseToDelete] = useState<Course>();
  useEffect(() => {
    const dialog = deleteDialog.current;
    if (courseToDelete && dialog && !dialog.open) dialog.showModal();
  }, [courseToDelete]);

  const deleteCourseMutation = useMutation({
    mutationFn: (id: string) => api.deleteCourse(id),
    onSuccess: (_, deletedId) => {
      queryClient.setQueryData<Course[]>(["courses"], (list) => list?.filter((course) => course.id !== deletedId));
      queryClient.invalidateQueries({ queryKey: ["courses"] });
      if (activeCourse?.id === deletedId) {
        setActiveCourse(null);
      }
      queryClient.invalidateQueries({ queryKey: ["study"] });
      deleteDialog.current?.close();
      toast.success("Course deleted");
    },
    onError: (err: any) => toast.error(err.message || "Failed to delete course"),
  });

  // 4. Send Message Handler
  const handleSendMessage = async (userText: string, files?: File[]) => {
    if (sendLock.current) return false;
    if (!activeCourse) {
      toast.error("Please select or create a course first.");
      return false;
    }

    sendLock.current = true;
    const courseId = activeCourse.id;
    const message: MessageProps = {
      id: `user-${Date.now()}`,
      role: "user",
      content: userText,
    };
    setPending({ courseId, message });

    try {
      const file = files?.[0];
      let attachment;
      let materialId;
      if (file && file.type.startsWith("image/") && settings?.vision_enabled) {
        const reader = new FileReader();
        const base64 = await new Promise<string>((resolve, reject) => {
          reader.onerror = () => reject(new Error("Could not read the attachment."));
          reader.onload = () => resolve(String(reader.result).split(",")[1]);
          reader.readAsDataURL(file);
        });
        attachment = { filename: file.name, mime_type: file.type, data: base64 };
      } else if (file) {
        const cached = uploads.current.get(file);
        if (cached?.courseId === courseId) {
          materialId = cached.id;
        } else {
          const material = await api.uploadMaterial(courseId, file);
          materialId = material.id;
          uploads.current.set(file, { courseId, id: material.id });
          void queryClient.invalidateQueries({ queryKey: ["materials", courseId] });
          void queryClient.invalidateQueries({ queryKey: ["study"] });
        }
      }
      if (materialId) {
        const material = (await api.listMaterials(courseId)).find((item) => item.id === materialId);
        if (!material) {
          if (file) uploads.current.delete(file);
          toast.error("This material was removed. Send again to upload a new copy.");
          return false;
        }
        if (material.processing_status !== "completed") {
          setIsMaterialsOpen(true);
          if (material.processing_status === "failed") {
            toast.error(material.processing_error ?? "This material could not be processed.");
          } else {
            toast.info("Your file is processing. Send again when it shows Ready in Materials.");
          }
          return false;
        }
      }
      const reply = await api.sendChatMessage(courseId, {
        message: userText,
        material_id: materialId,
        attachments: attachment ? [attachment] : [],
      });
      setNewReplyId(`${reply.id}-1`);
      await queryClient.invalidateQueries({ queryKey: ["chat_history", courseId] });
      void queryClient.invalidateQueries({ queryKey: ["study"] });
      return true;
    } catch (err: any) {
      toast.error(err.message || "Failed to receive a tutor reply");
      return false;
    } finally {
      sendLock.current = false;
      setPending(null);
    }
  };

  if (!profile) {
    return (
      <main className="grid min-h-screen place-items-center p-6">
        {profileError ? <button onClick={() => retryProfile()}>Could not load your profile. Try again</button> : "Opening workspace..."}
      </main>
    );
  }

  const leftVisible = coursesVisible;
  const materialsVisible = !!activeCourse && isMaterialsOpen;
  const savedAnswers = messages.filter((message) => message.role === "model" && message.bookmarked);

  return (
    <div className="relative flex h-dvh w-full overflow-hidden bg-background dark:bg-slate-950">
      <div className="workspace-panel workspace-panel-left" data-open={leftVisible}>
        <div className="workspace-panel-content" inert={!leftVisible}>
          <Sidebar
            courses={courses}
            profileName={profile.name}
            avatar={profile.avatar}
            onSelectCourse={selectCourse}
            onDeleteCourse={(id) => setCourseToDelete(courses.find((course) => course.id === id))}
          />
        </div>
      </div>

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header coursesVisible={leftVisible} materialsVisible={materialsVisible} savedOpen={view === "saved"}
          toggleCourses={() => setCoursesVisible(!leftVisible)}
          toggleMaterials={() => setIsMaterialsOpen(!materialsVisible)}
          toggleSaved={() => setSavedCourseId(view === "saved" ? undefined : courseId)} />
        {activeCourse && view === "chat" && settings && settings.status !== "ready" && (
          <p className="border-b border-line px-4 py-2 text-center text-sm">
            {settings.status === "missing" ? "Download the tutor model to start chatting." : "Start Ollama to use the tutor."}{" "}
            <Link href="/settings?section=models" className="text-accent underline underline-offset-2">Local model settings</Link>
          </p>
        )}

        {activeCourse && view === "chat" ? (
          <>
            <ChatContainer
              key={activeCourse.id}
              messages={messages}
              newReplyId={newReplyId}
              onRevealComplete={() => setNewReplyId(undefined)}
              onOpenSource={openSource}
              onBookmark={saveAnswer}
              onDiagram={(turn_id) => setDiagram({ turn_id })}
              onPractice={(turn_id) => setPractice({ courseId: activeCourse.id, origin: { turn_id } })}
              isLoading={sendingInActiveCourse}
              courseName={activeCourse.name}
              onSendExample={(text) => { void handleSendMessage(text); }}
            />
            <ChatInput
              key={activeCourse.id}
              onSendMessage={handleSendMessage}
              onTyping={collapsePanels}
              isLoading={sendingInActiveCourse}
              disabled={!!pending && !sendingInActiveCourse}
              visionEnabled={settings?.vision_enabled ?? false}
              whisperAvailable={settings?.whisper_available ?? false}
            />
          </>
        ) : activeCourse ? (
          <main className="study-enter min-h-0 flex-1 overflow-y-auto px-6 py-12 sm:py-16">
            <div className="mx-auto max-w-2xl">
                  <h1 className="font-display text-5xl tracking-tight">Saved answers</h1>
                  {historyError ? <button className="mt-4 underline" onClick={() => reloadHistory()}>Could not load answers. Retry</button>
                    : historyPending ? <p role="status" className="mt-4 text-sm">Loading answers?</p>
                    : savedAnswers.length === 0 && <p className="mt-4 text-sm text-neutral-600 dark:text-neutral-300">Save useful tutor replies to revisit them here.</p>}
                  <div className="divide-y divide-[var(--line)]">
                    {savedAnswers.map((answer) => (
                      <MessageBubble key={answer.id} message={answer} reveal={false} onRevealComplete={() => {}} onOpenSource={openSource} onBookmark={saveAnswer} onDiagram={(turn_id) => setDiagram({ turn_id })} onPractice={(turn_id) => setPractice({ courseId: activeCourse.id, origin: { turn_id } })} />
                    ))}
                  </div>
            </div>
          </main>
        ) : <StudyOverview name={profile.name} courses={courses} coursesPending={coursesPending} onResume={selectCourse} onReview={(reviewCourse) => setPractice({ courseId: reviewCourse })} />}
      </div>

      <div className="workspace-panel workspace-panel-right" data-open={materialsVisible}>
        <div className="workspace-panel-content" inert={!materialsVisible}>
          <MaterialsSidebar key={courseId} source={source} setSource={setSource} onDiagram={setDiagram} onPractice={(origin) => { if (courseId) setPractice({ courseId, origin }); }} />
        </div>
      </div>

      {practice && <PracticeStudio courseId={practice.courseId} origin={practice.origin} close={() => setPractice(undefined)} />}
      {courseId && diagram && <DiagramStudio courseId={courseId} selection={diagram} close={() => setDiagram(undefined)} />}

      <dialog ref={deleteDialog} onClose={() => setCourseToDelete(undefined)}
        onCancel={(event) => { if (deleteCourseMutation.isPending) event.preventDefault(); }}
        aria-labelledby="delete-course-title" aria-describedby="delete-course-description"
        className="fixed inset-0 m-auto w-[min(26rem,calc(100%-2rem))] rounded-panel border border-line bg-surface p-6 text-foreground shadow-xl backdrop:bg-black/45">
        <h2 id="delete-course-title" className="font-display text-3xl">Delete course?</h2>
        <p id="delete-course-description" className="mt-3 break-words text-sm">
          Deleting <strong>{courseToDelete?.name}</strong> permanently removes its chats, materials, and saved answers.
        </p>
        <div className="mt-6 flex flex-wrap justify-end gap-2">
          <button type="button" autoFocus className="study-secondary" disabled={deleteCourseMutation.isPending}
            onClick={() => deleteDialog.current?.close()}>Cancel</button>
          <button type="button" disabled={!courseToDelete || deleteCourseMutation.isPending}
            className="rounded-control bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-800 disabled:opacity-50"
            onClick={() => courseToDelete && deleteCourseMutation.mutate(courseToDelete.id)}>
            {deleteCourseMutation.isPending ? "Deleting?" : "Delete course"}
          </button>
        </div>
      </dialog>

      {/* Self-contained Modals */}
      <NewCourseModal
        onCreateCourse={(name, color, subject_profile) => createCourseMutation.mutateAsync({ name, color, subject_profile })}
      />
      <SearchCourseModal
        courses={courses}
        onSelectCourse={selectCourse}
      />
    </div>
  );
}

