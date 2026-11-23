import type { Course } from "@/store/useStore";

export interface CourseSource { id: string; name: string; page?: number | null }
export type DiagramOrigin = { turn_id: number } | { material_ids: string[] };
export type DiagramType = "flowchart" | "sequence";
export type PracticeKind = "flashcard" | "quiz";
export interface PracticeContent {
  question: string;
  answer: string;
  explanation: string;
  choices: string[];
}
export interface PracticeItem extends PracticeContent {
  id: number;
  kind: PracticeKind;
  due_at: number;
  revision: number;
  evidence: { source: CourseSource; text: string };
}
export interface SavedDiagram {
  id: number;
  title: string;
  mermaid: string;
  sources: CourseSource[];
}

export interface LocalProfile {
  name: string;
  avatar?: string | null;
  institution?: string;
  goal?: string;
  terms_accepted?: boolean;
  academic: { grade: string; subject: string };
}

type Preferences = Partial<Record<
  "detail_level" | "example_preference" | "analogy_preference" | "technical_language" | "structure_preference", number
>> & { learning_pace?: string | null; prior_experience?: string | null };

const API_BASE = "/api";

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errorDetail = `Request failed: ${res.statusText}`;
    try {
      const data = await res.json();
      errorDetail = typeof data.detail === "string" ? data.detail : data.detail?.[0]?.msg || errorDetail;
    } catch {}
    throw new Error(errorDetail);
  }

  return res.json();
}

export const api = {
  getProfile: () => request<LocalProfile | null>("/profile"),
  saveProfile: (profile: LocalProfile) =>
    request<LocalProfile>("/profile", { method: "PUT", body: JSON.stringify(profile) }),
  getSettings: () => request<{
    model: string;
    vision_enabled: boolean;
    whisper_available: boolean;
    installed_models: string[];
    status: "ready" | "missing" | "unavailable";
  }>("/settings"),
  getDevice: () => request<{
    system: string; arch: string; cpu: string; threads: number | null;
    ram_bytes: number | null; gpu: string | null; vram_bytes: number | null;
    unified_memory: boolean; recommended: string;
    ollama_auto: boolean; voice_auto: boolean;
    models: { id: string; name: string; size: string }[];
  }>("/settings/device"),
  downloadModel: (id: string) => request<{ status: "ready" }>(
    `/settings/model?model=${encodeURIComponent(id)}`, { method: "POST" },
  ),
  getKokoro: () => request<{
    installed: boolean;
    supported: boolean;
    progress: { phase: "downloading" | "installing"; package: "runtime" | "voice"; received: number; total: number | null } | null;
  }>("/settings/kokoro"),
  downloadKokoro: () => request<{ installed: boolean }>("/settings/kokoro", { method: "POST" }),
  downloadVoice: () => request<{ status: "ready" }>("/settings/voice", { method: "POST" }),

  saveSettings: (profile: LocalProfile, prefs: Preferences) =>
    request<{ profile: LocalProfile; prefs: Preferences }>("/profile/settings", {
      method: "PUT", body: JSON.stringify({ profile, prefs }),
    }),
  getPreferences: () => request<{ prefs: Preferences }>("/profile/preferences"),
  savePreferences: (prefs: Preferences) =>
    request<{ prefs: Preferences }>("/profile/preferences", {
      method: "POST",
      body: JSON.stringify(prefs),
    }),

  getStudy: () => request<{
    courses: number; materials: number; turns: number;
    due_flashcards: number;
    due_courses: { course_id: string; count: number }[];
    recent: { id: number; course_id: string; course: string; question: string; created_at: string }[];
  }>(`/study?due_before=${Math.floor(new Date().setHours(24, 0, 0, 0) / 1000)}`),
  transcribe: (audio: Blob) => {
    const body = new FormData();
    body.append("audio", audio, "speech.wav");
    return request<{ text: string }>("/transcribe", { method: "POST", body });
  },

  // Courses
  listCourses: () => request<Course[]>("/courses"),
  createCourse: (data: Omit<Course, "id">) =>
    request<Course>("/courses", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  deleteCourse: (courseId: string) =>
    request<{ message: string }>(`/courses/${courseId}`, {
      method: "DELETE",
    }),

  listDiagrams: (courseId: string) =>
    request<SavedDiagram[]>(`/courses/${courseId}/artifacts/diagrams`),
  saveReplyDiagram: (courseId: string, turnId: number, mermaid: string) =>
    request<SavedDiagram>(`/courses/${courseId}/artifacts/diagrams/from-reply/${turnId}`, {
      method: "POST", body: JSON.stringify({ mermaid }),
    }),
  repairReplyDiagram: (courseId: string, turnId: number, mermaid: string, parser_error: string) =>
    request<{ mermaid: string }>(`/courses/${courseId}/artifacts/diagrams/from-reply/${turnId}/repair`, {
      method: "POST", body: JSON.stringify({ mermaid, parser_error }),
    }),
  createDiagram: (courseId: string, origin: DiagramOrigin, question: string, diagram_type: DiagramType) =>
    request<SavedDiagram>(`/courses/${courseId}/artifacts/diagrams`, {
      method: "POST", body: JSON.stringify({ ...origin, question, diagram_type }),
    }),
  updateDiagram: (courseId: string, diagram: SavedDiagram, title: string, mermaid: string) =>
    request<SavedDiagram>(`/courses/${courseId}/artifacts/diagrams/${diagram.id}`, {
      method: "PUT", body: JSON.stringify({ title, mermaid }),
    }),
  listPractice: (courseId: string) => request<PracticeItem[]>(`/courses/${courseId}/artifacts/practice`),
  createPractice: (courseId: string, origin: DiagramOrigin, kind: PracticeKind, question: string) =>
    request<PracticeItem[]>(`/courses/${courseId}/artifacts/practice`, {
      method: "POST", body: JSON.stringify({ ...origin, kind, question }),
    }),
  editPractice: (courseId: string, item: PracticeItem, content: PracticeContent) =>
    request<PracticeItem>(`/courses/${courseId}/artifacts/practice/${item.id}`, {
      method: "PUT", body: JSON.stringify({ ...content, revision: item.revision }),
    }),
  reviewPractice: (courseId: string, item: PracticeItem, grade: { recalled: boolean } | { choice: string }) =>
    request<{ correct: boolean; item: PracticeItem }>(`/courses/${courseId}/artifacts/practice/${item.id}/review`, {
      method: "POST", body: JSON.stringify({ ...grade, revision: item.revision }),
    }),
  // Materials
  listMaterials: (courseId: string) =>
    request<Array<{
      id: string;
      name: string;
      file_type: string;
      file_size: number;
      processing_status: string;
      processing_error?: string | null;
      created_at: string;
    }>>(`/courses/${courseId}/materials`),

  uploadMaterial: (courseId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<any>(`/courses/${courseId}/materials`, {
      method: "POST",
      body: formData,
    });
  },

  retryMaterial: (materialId: string) => request(`/materials/${materialId}/retry`, { method: "POST" }),

  deleteMaterial: (materialId: string) =>
    request<{ message: string }>(`/materials/${materialId}`, {
      method: "DELETE",
    }),

  getMaterial: (courseId: string, source: CourseSource) =>
    request<{ name: string; text: string; truncated: boolean }>(
      `/courses/${courseId}/materials/${source.id}${source.page ? `?page=${source.page}` : ""}`,
    ),

  setBookmark: (courseId: string, turnId: number, saved: boolean) =>
    request<{ bookmarked: boolean }>(`/courses/${courseId}/chat/${turnId}/bookmark?saved=${saved}`, { method: "PUT" }),

  // Chat
  sendChatMessage: (courseId: string, payload: { message: string; material_id?: string; attachments?: { filename: string; mime_type: string; data: string }[] }) =>
    request<{
      id: number;
      response: string;
      timestamp: string;
    }>(`/courses/${courseId}/chat`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getChatHistory: (courseId: string) => request<{
    id: number;
    bookmarked?: boolean;
    history: { role: "user" | "model"; content: string; sources?: CourseSource[] }[];
    created_at: string;
  }[]>(`/courses/${courseId}/chat`),
};

