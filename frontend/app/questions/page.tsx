"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { api } from "@/lib/api";
import SetupShell from "@/components/setup/SetupShell";
import { Check, ArrowRight, ArrowLeft } from "lucide-react";

interface Question {
  id: number;
  category: string;
  question: string;
  key: string;
  options: {
    label: string;
    text: string;
    value: number;
  }[];
}

const QUESTIONS: Question[] = [
  {
    id: 1,
    category: "Detail Level",
    question: "When learning a new concept, I prefer...",
    key: "detail_level",
    options: [
      { label: "A", text: "Brief explanations that get straight to the point", value: 0.2 },
      { label: "B", text: "Balanced explanations with essential context", value: 0.5 },
      { label: "C", text: "Comprehensive deep-dives covering all edge cases", value: 0.9 },
    ],
  },
  {
    id: 2,
    category: "Example Usage",
    question: "I grasp difficult theories best when...",
    key: "example_preference",
    options: [
      { label: "A", text: "Explained abstractly with formal definitions", value: 0.2 },
      { label: "B", text: "Supplemented with one or two key examples", value: 0.5 },
      { label: "C", text: "Walked through multiple step-by-step real world scenarios", value: 0.9 },
    ],
  },
  {
    id: 3,
    category: "Analogies & Metaphors",
    question: "When introducing complex terminology, I like...",
    key: "analogy_preference",
    options: [
      { label: "A", text: "Direct literal explanations only", value: 0.2 },
      { label: "B", text: "Occasional intuitive analogies", value: 0.5 },
      { label: "C", text: "Frequent metaphors to relate concepts to everyday life", value: 0.9 },
    ],
  },
  {
    id: 4,
    category: "Technical Rigor",
    question: "Regarding mathematical and technical notations, I prefer...",
    key: "technical_language",
    options: [
      { label: "A", text: "Plain conceptual English with minimal equations", value: 0.2 },
      { label: "B", text: "Standard academic formulas with clear variable breakdowns", value: 0.5 },
      { label: "C", text: "Full rigorous mathematical proofs and LaTeX derivations", value: 0.9 },
    ],
  },
  {
    id: 5,
    category: "Answer structure",
    question: "How should the tutor organize an explanation?",
    key: "structure_preference",
    options: [
      { label: "A", text: "A conversational explanation", value: 0.2 },
      { label: "B", text: "A short explanation with key points", value: 0.5 },
      { label: "C", text: "A clearly numbered, step-by-step breakdown", value: 0.9 },
    ],
  },
];

export default function QuestionsPage() {
  const router = useRouter();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const currentQ = QUESTIONS[currentIndex];
  const progressPercent = ((currentIndex + 1) / QUESTIONS.length) * 100;

  const handleSelect = (value: number) => {
    setAnswers((prev) => ({ ...prev, [currentQ.key]: value }));
  };

  const handleNext = async () => {
    if (answers[currentQ.key] === undefined) {
      toast.error("Please select an option before continuing.");
      return;
    }

    if (currentIndex < QUESTIONS.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    } else {
      // Save preferences
      try {
        setIsSubmitting(true);
        await api.savePreferences(answers);
        toast.success("Preferences saved successfully!");
        router.push("/app");
      } catch {
        toast.error("Could not save your preferences. Try again.");
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  return (
    <SetupShell>
      <div className="study-enter mx-auto w-full max-w-3xl space-y-9 px-6 py-10 sm:py-12">
        <header className="max-w-2xl mx-auto w-full">
          <div className="flex justify-between items-center mb-4">
            <span className="font-sans text-xs text-gray-500">
              Question {currentIndex + 1} of {QUESTIONS.length}
            </span>
            <span className="font-sans text-xs text-amber-700 dark:text-studymate-orange">
              {currentQ.category}
            </span>
          </div>
          <div role="progressbar" aria-label="Preference questions" aria-valuemin={0} aria-valuemax={QUESTIONS.length} aria-valuenow={currentIndex + 1}
            className="h-1.5 w-full overflow-hidden rounded-full bg-black/10 dark:bg-slate-800">
            <div
              className="h-full bg-[#FEAE01] transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </header>

        <main className="max-w-2xl mx-auto w-full my-auto space-y-8">
          <h2 className="font-display text-4xl md:text-5xl text-black dark:text-white">
            {currentQ.question}
          </h2>

          <div className="space-y-4">
            {currentQ.options.map((opt) => {
              const isSelected = answers[currentQ.key] === opt.value;
              return (
                <button
                  key={opt.label}
                  onClick={() => handleSelect(opt.value)}
                  aria-pressed={isSelected}
                  className={`w-full p-5 rounded-panel border text-left flex items-start gap-4 transition-all duration-200 ${
                    isSelected
                      ? "border-[#859075] bg-[#eeeee3] dark:border-[#a4b193] dark:bg-[#303329]"
                      : "border-black/10 bg-white hover:border-black/30 dark:border-white/10 dark:bg-slate-900 dark:hover:border-white/30"
                  }`}
                >
                  <span
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-sans shrink-0 ${
                      isSelected
                        ? "bg-black text-white dark:bg-white dark:text-black"
                        : "bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-gray-300"
                    }`}
                  >
                    {isSelected ? <Check className="w-4 h-4" /> : opt.label}
                  </span>
                  <span className="text-sm md:text-base font-sans pt-1 text-black dark:text-white">
                    {opt.text}
                  </span>
                </button>
              );
            })}
          </div>

          <div className="flex justify-between items-center pt-4">
            <button
              onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
              disabled={currentIndex === 0}
              className="px-6 h-12 rounded-full border border-black/10 dark:border-white/10 text-sm font-sans flex items-center gap-2 disabled:opacity-30"
            >
              <ArrowLeft className="w-4 h-4" /> Back
            </button>

            <button
              onClick={handleNext}
              disabled={isSubmitting || answers[currentQ.key] === undefined}
              className="px-8 h-12 study-action"
            >
              {currentIndex === QUESTIONS.length - 1 ? (isSubmitting ? "Finishing..." : "Start Studying") : "Continue"}
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </main>

        <footer className="max-w-2xl mx-auto w-full text-center">
          <button
            onClick={() => router.push("/app")}
            className="text-sm text-neutral-600 underline underline-offset-4 hover:text-black dark:text-slate-300 dark:hover:text-white"
          >
            Skip to workspace
          </button>
        </footer>
      </div>
    </SetupShell>
  );
}

