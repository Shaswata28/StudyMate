import { create } from "zustand";

export type SubjectProfile = "general" | "stem" | "life_sciences" | "humanities";

export interface Course {
  id: string;
  name: string;
  color: string;
  subject_profile: SubjectProfile;
}

interface AppState {
  // Workspace
  activeCourse: Course | null;
  setActiveCourse: (course: Course | null) => void;

  // Modals
  isNewCourseOpen: boolean;
  setIsNewCourseOpen: (open: boolean) => void;
  isMaterialsOpen: boolean;
  setIsMaterialsOpen: (open: boolean) => void;
  isSearchOpen: boolean;
  setIsSearchOpen: (open: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  activeCourse: null,
  setActiveCourse: (course) => set({ activeCourse: course }),

  isNewCourseOpen: false,
  setIsNewCourseOpen: (open) => set({ isNewCourseOpen: open }),
  isMaterialsOpen: false,
  setIsMaterialsOpen: (open) => set({ isMaterialsOpen: open }),
  isSearchOpen: false,
  setIsSearchOpen: (open) => set({ isSearchOpen: open }),
}));

