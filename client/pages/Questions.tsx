import { useState } from "react";
import { useNavigate } from "react-router-dom";

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
    category: "Learning Style",
    title: "Question 2",
    question: '"I learn best when..."',
    options: [
      { label: "A", text: "I see visual diagrams and charts" },
      { label: "B", text: "I read detailed text explanations" },
      { label: "C", text: "I work through practical examples" },
    ],
  },
  {
    id: 3,
    category: "Pace Preference",
    title: "Question 3",
    question: '"My ideal learning pace is..."',
    options: [
      { label: "A", text: "Quick and concise" },
      { label: "B", text: "Moderate with time to digest" },
      { label: "C", text: "Slow and thorough" },
    ],
  },
  {
    id: 4,
    category: "Example Preference",
    title: "Question 4",
    question: '"When learning, I prefer..."',
    options: [
      { label: "A", text: "One clear example" },
      { label: "B", text: "A few diverse examples" },
      { label: "C", text: "Many examples covering all cases" },
    ],
  },
  {
    id: 5,
    category: "Feedback Style",
    title: "Question 5",
    question: '"I prefer feedback that is..."',
    options: [
      { label: "A", text: "Direct and to the point" },
      { label: "B", text: "Balanced with encouragement" },
      { label: "C", text: "Detailed with improvement suggestions" },
    ],
  },
  {
    id: 6,
    category: "Difficulty Level",
    title: "Question 6",
    question: '"I prefer challenges that are..."',
    options: [
      { label: "A", text: "Slightly above my current level" },
      { label: "B", text: "At my current level" },
      { label: "C", text: "Well within my comfort zone" },
    ],
  },
  {
    id: 7,
    category: "Study Method",
    title: "Question 7",
    question: '"My preferred study method is..."',
    options: [
      { label: "A", text: "Active recall and testing" },
      { label: "B", text: "Note-taking and reviewing" },
      { label: "C", text: "Reading and highlighting" },
    ],
  },
  {
    id: 8,
    category: "Explanation Style",
    title: "Question 8",
    question: '"I understand best when explanations..."',
    options: [
      { label: "A", text: "Use real-world analogies" },
      { label: "B", text: "Provide step-by-step breakdowns" },
      { label: "C", text: "Show multiple perspectives" },
    ],
  },
];

export default function Questions() {
  const navigate = useNavigate();
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});

  const currentQuestion = questions[currentQuestionIndex];
  const selectedOption = answers[currentQuestion.id];

  const handleSelectOption = (label: string) => {
    setAnswers((prev) => ({
      ...prev,
      [currentQuestion.id]: label,
    }));
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
    } else {
      console.log("All answers:", answers);
      navigate("/app");
    }
  };

  return (
    <div className="min-h-screen w-full bg-white px-6 md:px-12 lg:px-20">
      <header className="w-full h-[114px] flex items-center">
        <h1 className="font-koulen text-3xl md:text-4xl lg:text-[36px] tracking-[3.6px] text-black">
          StudyMate
        </h1>
      </header>

      <div className="max-w-[1200px] mx-auto pt-4">
        <div className="mb-8">
          <p className="font-audiowide text-[20px] md:text-[24px] tracking-[2.4px] text-[#404040] mb-2">
            {currentQuestion.title}
          </p>
          <h2 className="font-audiowide text-[20px] md:text-[24px] tracking-[2.4px] text-black mb-6">
            {currentQuestion.category}
          </h2>
          <h3 className="font-audiowide text-[28px] md:text-[32px] tracking-[3.2px] text-black mb-12">
            {currentQuestion.question}
          </h3>
        </div>

        <div className="space-y-5 mb-12">
          {currentQuestion.options.map((option) => {
            const isSelected = selectedOption === option.label;
            return (
              <button
                key={option.label}
                onClick={() => handleSelectOption(option.label)}
                className="w-full flex items-center gap-5 hover:opacity-80 transition-opacity"
              >
                <div
                  className={`w-[54px] h-[54px] rounded-full flex items-center justify-center flex-shrink-0 border transition-all ${
                    isSelected
                      ? "bg-[#6DE05D]/20 border-[#1FC209]"
                      : "bg-[#D9D9D9]/25 border-black"
                  }`}
                >
                  <span className="font-roboto-slab text-[28px] tracking-[2.8px] text-black">
                    {option.label}
                  </span>
                </div>
                <p className="font-roboto-slab text-[20px] md:text-[24px] tracking-[2.4px] text-black text-left flex-1">
                  {option.text}
                </p>
              </button>
            );
          })}
        </div>

        <div className="flex justify-end">
          <button
            onClick={handleNext}
            disabled={!selectedOption}
            className="w-[65px] h-[65px] rounded-full flex items-center justify-center hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
                stroke="#1E1E1E"
                strokeWidth="4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
