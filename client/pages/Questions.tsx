import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Progress } from "@/components/ui/progress";
import { useAuth } from "@/hooks/use-auth";
import { toast } from "@/lib/toast";

interface Question {
  id: number;
  category: string;
  title: string;
  question: string;
  options: {
    label: string;
    text: string;
  }[];
}

const questions: Question[] = [
  {
    id: 1,
    category: "Detail Preference",
    title: "Question 1",
    question: '"When learning a new concept, I prefer..."',
    options: [
      { label: "A", text: "Brief explanations that get straight to the point" },
      { label: "B", text: "Moderate explanations with key details" },
      { label: "C", text: "Comprehensive explanations that cover everything thoroughly" },
    ],
  },
  {
    id: 2,
    category: "Example Preference",
    title: "Question 2",
    question: '"I understand concepts better when..."',
    options: [
      { label: "A", text: "Explained abstractly with theory and definitions" },
      { label: "B", text: "Explained with occasional examples" },
      { label: "C", text: "Explained through multiple real-world examples" },
    ],
  },
  {
    id: 3,
    category: "Analogy Preference",
    title: "Question 3",
    question: '"When explaining difficult topics, I prefer..."',
    options: [
      { label: "A", text: "Direct explanations without comparisons" },
      { label: "B", text: "Some analogies when helpful" },
      { label: "C", text: "Frequent use of analogies and metaphors" },
    ],
  },
  {
    id: 4,
    category: "Technical Language",
    title: "Question 4",
    question: '"I prefer explanations using..."',
    options: [
      { label: "A", text: "Simple, everyday language" },
      { label: "B", text: "A mix of simple and technical terms" },
      { label: "C", text: "Proper technical and scientific terminology" },
    ],
  },
  {
    id: 5,
    category: "Structure Preference",
    title: "Question 5",
    question: '"I learn best when information is..."',
    options: [
      { label: "A", text: "Presented as a complete overview" },
      { label: "B", text: "Somewhat organized in steps" },
      { label: "C", text: "Broken down into clear, numbered steps" },
    ],
  },
  {
    id: 6,
    category: "Visual vs. Text",
    title: "Question 6",
    question: '"When studying, I prefer..."',
    options: [
      { label: "A", text: "Reading text-based explanations" },
      { label: "B", text: "Mix of text and visual descriptions" },
      { label: "C", text: "Visual representations (diagrams, charts, etc.)" },
    ],
  },
  {
    id: 7,
    category: "Learning Pace",
    title: "Question 7",
    question: '"When learning new material, my pace is usually..."',
    options: [
      { label: "A", text: "I prefer to take my time and understand deeply" },
      { label: "B", text: "I learn at a moderate, steady pace" },
      { label: "C", text: "I like to move quickly through material" },
    ],
  },
  {
    id: 8,
    category: "Prior Experience",
    title: "Question 8",
    question: '"How comfortable are you with the subjects youre studying?"',
    options: [
      { label: "A", text: "I'm just starting / struggling with basics" },
      { label: "B", text: "I have moderate understanding" },
      { label: "C", text: "I'm confident with the material" },
      { label: "D", text: "I'm advanced / helping others"}
    ],
  },
];

export default function Questions() {
  const navigate = useNavigate();
  const { savePreferences } = useAuth();
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [isSaving, setIsSaving] = useState(false);

  const currentQuestion = questions[currentQuestionIndex];
  const selectedOption = answers[currentQuestion.id];
  const progress = currentQuestionIndex + 1;
  const percentage = (progress / questions.length) * 100;

  const handleSelectOption = (label: string) => {
    setAnswers((prev) => ({
      ...prev,
      [currentQuestion.id]: label,
    }));
  };

  // Convert questionnaire answers to preference values (0-1 scale)
  const convertAnswersToPreferences = () => {
    const getScaleValue = (answer: string, questionId: number) => {
      // Most questions have A=0, B=0.5, C=1
      // Question 7 (learning pace) is reversed: A=0 (slow), B=0.5, C=1 (fast)
      // Question 8 (prior experience) has 4 options: A=0, B=0.33, C=0.67, D=1
      
      if (questionId === 8) {
        const mapping: Record<string, number> = { 'A': 0, 'B': 0.33, 'C': 0.67, 'D': 1 };
        return mapping[answer] || 0.5;
      }
      
      const mapping: Record<string, number> = { 'A': 0, 'B': 0.5, 'C': 1 };
      return mapping[answer] || 0.5;
    };

    const getPaceValue = (answer: string) => {
      const mapping: Record<string, 'slow' | 'moderate' | 'fast'> = {
        'A': 'slow',
        'B': 'moderate',
        'C': 'fast'
      };
      return mapping[answer] || 'moderate';
    };

    const getExperienceValue = (answer: string) => {
      const mapping: Record<string, 'beginner' | 'intermediate' | 'advanced' | 'expert'> = {
        'A': 'beginner',
        'B': 'intermediate',
        'C': 'advanced',
        'D': 'expert'
      };
      return mapping[answer] || 'intermediate';
    };

    return {
      detail_level: getScaleValue(answers[1] || 'B', 1),
      example_preference: getScaleValue(answers[2] || 'B', 2),
      analogy_preference: getScaleValue(answers[3] || 'B', 3),
      technical_language: getScaleValue(answers[4] || 'B', 4),
      structure_preference: getScaleValue(answers[5] || 'B', 5),
      visual_preference: getScaleValue(answers[6] || 'B', 6),
      learning_pace: getPaceValue(answers[7] || 'B'),
      prior_experience: getExperienceValue(answers[8] || 'B'),
    };
  };

  const handleNext = async () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
    } else {
      // Last question - save preferences and navigate
      setIsSaving(true);
      try {
        const preferences = convertAnswersToPreferences();
        await savePreferences(preferences);
        toast.success("Preferences saved!", "Your learning profile is ready");
        setTimeout(() => navigate("/app"), 600);
      } catch (error) {
        setIsSaving(false);
        const errorMessage = error instanceof Error ? error.message : "Failed to save preferences";
        toast.error("Error", errorMessage);
      }
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex((prev) => prev - 1);
    }
  };

  return (
    <div className="min-h-screen w-full bg-white dark:bg-slate-950 px-6 md:px-12 lg:px-20 flex flex-col">
      {/* Header */}
      <header className="w-full h-[114px] flex items-center">
        <h1 className="font-koulen text-3xl md:text-4xl lg:text-[36px] tracking-[3.6px] text-black dark:text-white">
          StudyMate
        </h1>
      </header>

      {/* Progress Bar */}
      <div className="mb-8">
        <Progress value={percentage} className="h-2" />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col max-w-[1200px] mx-auto w-full py-8">
        {/* Question Header */}
        <div className="mb-12">
          <p className="font-audiowide text-[20px] md:text-[24px] tracking-[2.4px] text-[#404040] dark:text-gray-400 mb-2">
            {currentQuestion.title}
          </p>
          <h2 className="font-audiowide text-[20px] md:text-[24px] tracking-[2.4px] text-black dark:text-white mb-6">
            {currentQuestion.category}
          </h2>
          <h3 className="font-audiowide text-[28px] md:text-[32px] tracking-[3.2px] text-black dark:text-white mb-12">
            {currentQuestion.question}
          </h3>
        </div>

        {/* Question Options */}
        <div className="space-y-5 mb-12 flex-1">
          {currentQuestion.options.map((option) => {
            const isSelected = selectedOption === option.label;
            return (
              <button
                key={option.label}
                onClick={() => handleSelectOption(option.label)}
                className="w-full flex items-center gap-5 hover:opacity-80 transition-all duration-200 group message-enter"
                aria-pressed={isSelected}
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    handleSelectOption(option.label);
                  }
                }}
              >
                <div
                  className={`w-[54px] h-[54px] rounded-full flex items-center justify-center flex-shrink-0 border-2 transition-all duration-200 ${
                    isSelected
                      ? "bg-studymate-green/20 border-studymate-green scale-110 shadow-md"
                      : "bg-studymate-gray/25 dark:bg-slate-700 border-black dark:border-white group-hover:scale-105"
                  }`}
                >
                  <span className="font-roboto-slab text-[28px] tracking-[2.8px] text-black dark:text-white">
                    {option.label}
                  </span>
                </div>
                <p className="font-roboto-slab text-[20px] md:text-[24px] tracking-[2.4px] text-black dark:text-white text-left flex-1">
                  {option.text}
                </p>
              </button>
            );
          })}
        </div>

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between gap-4">
          {/* Previous Button */}
          <button
            onClick={handlePrevious}
            disabled={currentQuestionIndex === 0}
            className="w-[65px] h-[65px] rounded-full flex items-center justify-center hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors disabled:opacity-30 disabled:cursor-not-allowed btn-micro"
            aria-label="Previous question"
          >
            <svg
              width="65"
              height="65"
              viewBox="0 0 65 65"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="rotate-180"
            >
              <path
                d="M32.4998 43.3333L43.3332 32.5M43.3332 32.5L32.4998 21.6666M43.3332 32.5H21.6665M59.5832 32.5C59.5832 47.4577 47.4575 59.5833 32.4998 59.5833C17.5421 59.5833 5.4165 47.4577 5.4165 32.5C5.4165 17.5422 17.5421 5.41663 32.4998 5.41663C47.4575 5.41663 59.5832 17.5422 59.5832 32.5Z"
                stroke="currentColor"
                strokeWidth="4"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-studymate-black dark:text-white"
              />
            </svg>
          </button>

          {/* Next Button */}
          <button
            onClick={handleNext}
            disabled={!selectedOption || isSaving}
            className="w-[65px] h-[65px] rounded-full flex items-center justify-center hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors disabled:opacity-30 disabled:cursor-not-allowed btn-micro"
            aria-label={currentQuestionIndex === questions.length - 1 ? "Complete questionnaire" : "Next question"}
            aria-busy={isSaving}
          >
            <svg
              width="65"
              height="65"
              viewBox="0 0 65 65"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M32.4998 43.3333L43.3332 32.5M43.3332 32.5L32.4998 21.6666M43.3332 32.5H21.6665M59.5832 32.5C59.5832 47.4577 47.4575 59.5833 32.4998 59.5833C17.5421 59.5833 5.4165 47.4577 5.4165 32.5C5.4165 17.5422 17.5421 5.41663 32.4998 5.41663C47.4575 5.41663 59.5832 17.5422 59.5832 32.5Z"
                stroke="currentColor"
                strokeWidth="4"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-studymate-black dark:text-white"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
