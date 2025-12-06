import { useEffect, useRef } from "react";
import { X, Check, RotateCcw } from "lucide-react";

interface VoiceVisualizerProps {
  isRecording: boolean;
  audioAnalyzer: AnalyserNode | null;
  transcript: string;
  onStop: () => void;
  onCancel: () => void;
  onRetry: () => void;
}

export default function VoiceVisualizer({
  isRecording,
  audioAnalyzer,
  transcript,
  onStop,
  onCancel,
  onRetry,
}: VoiceVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when text changes
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcript]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !isRecording) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Canvas Size
    const size = 300;
    canvas.width = size;
    canvas.height = size;

    const centerX = size / 2;
    const centerY = size / 2;
    const baseRadius = 70;

    // Theme Colors
    const isDarkMode = document.documentElement.classList.contains("dark");
    const themeColor = isDarkMode
      ? getComputedStyle(document.documentElement).getPropertyValue("--studymate-green").trim() || "#4ade80"
      : getComputedStyle(document.documentElement).getPropertyValue("--studymate-orange").trim() || "#f97316";

    let dataArray: Uint8Array<ArrayBuffer> | null = null;
    let bufferLength = 0;

    if (audioAnalyzer) {
      bufferLength = audioAnalyzer.frequencyBinCount;
      dataArray = new Uint8Array(bufferLength) as Uint8Array<ArrayBuffer>;
    }

    const animate = () => {
      ctx.clearRect(0, 0, size, size);
      let amplitude = 0;

      if (audioAnalyzer && dataArray) {
        audioAnalyzer.getByteFrequencyData(dataArray);
        const sum = dataArray.reduce((acc, val) => acc + val, 0);
        amplitude = sum / bufferLength / 255;
        
        // Idle animation
        if (amplitude < 0.05) {
          amplitude = 0.2 + Math.sin(Date.now() / 800) * 0.05;
        }
      } else {
        amplitude = 0.2 + Math.sin(Date.now() / 800) * 0.05;
      }

      const scaledRadius = baseRadius + amplitude * 50;

      // Outer Glow
      const gradient = ctx.createRadialGradient(centerX, centerY, scaledRadius * 0.5, centerX, centerY, scaledRadius * 1.5);
      gradient.addColorStop(0, `${themeColor}40`); 
      gradient.addColorStop(1, `${themeColor}00`); 
      
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(centerX, centerY, scaledRadius * 1.5, 0, Math.PI * 2);
      ctx.fill();

      // Main Circle
      ctx.fillStyle = `${themeColor}90`;
      ctx.beginPath();
      ctx.arc(centerX, centerY, scaledRadius, 0, Math.PI * 2);
      ctx.fill();

      // Inner Solid Circle
      ctx.fillStyle = themeColor;
      ctx.beginPath();
      ctx.arc(centerX, centerY, scaledRadius * 0.6, 0, Math.PI * 2);
      ctx.fill();

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, [isRecording, audioAnalyzer]);

  if (!isRecording) return null;

  return (
    <div 
      className="fixed inset-0 z-[100] flex flex-col items-center justify-between bg-white/30 dark:bg-black/40 backdrop-blur-xl animate-in fade-in duration-200"
      role="dialog"
    >
      {/* Visualizer Section (Top) */}
      <div className="flex-1 flex items-center justify-center w-full relative mt-10">
         <canvas ref={canvasRef} className="w-[300px] h-[300px]" />
      </div>

      {/* Real-time Transcript Section (Middle) */}
      <div className="w-full max-w-2xl px-6 mb-8 flex flex-col items-center">
        <div 
            ref={scrollRef}
            className="w-full text-center max-h-[200px] overflow-y-auto scrollbar-hide transition-all duration-200"
        >
            {transcript ? (
                <p className="text-2xl md:text-3xl font-medium text-studymate-black dark:text-white leading-relaxed drop-shadow-sm transition-opacity duration-200">
                    "{transcript}"
                </p>
            ) : (
                <p className="text-xl text-gray-500/80 dark:text-gray-400/80 font-medium animate-pulse">
                    Listening...
                </p>
            )}
        </div>
      </div>

      {/* Controls Section (Bottom) */}
      <div className="mb-12 flex items-center gap-10">
        
        {/* Retry Button */}
        <button
            onClick={onRetry}
            className="group flex flex-col items-center gap-2"
            title="Retry Recording"
        >
            <div className="w-12 h-12 flex items-center justify-center rounded-full bg-gray-200/50 dark:bg-gray-800/50 backdrop-blur-md text-studymate-black dark:text-white group-hover:bg-gray-300 dark:group-hover:bg-gray-700 transition-all shadow-sm">
                <RotateCcw className="w-5 h-5" />
            </div>
            <span className="text-xs font-semibold text-studymate-black/60 dark:text-white/60 uppercase tracking-wider">Retry</span>
        </button>

        {/* Cancel Button */}
        <button
            onClick={onCancel}
            className="group flex flex-col items-center gap-2"
            title="Cancel"
        >
            <div className="w-14 h-14 flex items-center justify-center rounded-full bg-red-500/10 dark:bg-red-500/20 backdrop-blur-md text-red-600 dark:text-red-400 group-hover:scale-110 transition-all shadow-sm">
                <X className="w-6 h-6" strokeWidth={3} />
            </div>
             <span className="text-xs font-semibold text-studymate-black/60 dark:text-white/60 uppercase tracking-wider">Cancel</span>
        </button>

        {/* Done/Send Button */}
        <button
            onClick={onStop}
            className="group flex flex-col items-center gap-2"
            title="Done"
        >
            <div className="w-16 h-16 flex items-center justify-center rounded-full bg-studymate-black dark:bg-white text-white dark:text-studymate-black shadow-lg group-hover:scale-110 transition-all">
                <Check className="w-8 h-8" strokeWidth={3} />
            </div>
             <span className="text-xs font-semibold text-studymate-black/60 dark:text-white/60 uppercase tracking-wider">Send</span>
        </button>

      </div>
    </div>
  );
}