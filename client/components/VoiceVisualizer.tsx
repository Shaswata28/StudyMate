import { useEffect, useRef } from "react";

interface VoiceVisualizerProps {
  isRecording: boolean;
  audioAnalyzer: AnalyserNode | null;
  recordingTime: number;
}

export default function VoiceVisualizer({
  isRecording,
  audioAnalyzer,
  recordingTime,
}: VoiceVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Format recording time as MM:SS
  const formatRecordingTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !isRecording) {
      return;
    }

    const ctx = canvas.getContext("2d");
    if (!ctx) {
      return;
    }

    // Set canvas size
    const size = 200;
    canvas.width = size;
    canvas.height = size;

    const centerX = size / 2;
    const centerY = size / 2;
    const baseRadius = 60;

    // Get theme color based on current theme
    const isDarkMode = document.documentElement.classList.contains("dark");
    const themeColor = isDarkMode
      ? getComputedStyle(document.documentElement).getPropertyValue("--studymate-green").trim()
      : getComputedStyle(document.documentElement).getPropertyValue("--studymate-orange").trim();

    let dataArray: Uint8Array<ArrayBuffer> | null = null;
    let bufferLength = 0;

    // Set up audio analyzer if available
    if (audioAnalyzer) {
      bufferLength = audioAnalyzer.frequencyBinCount;
      dataArray = new Uint8Array(bufferLength) as Uint8Array<ArrayBuffer>;
    }

    // Threshold for detecting low/no audio
    const IDLE_THRESHOLD = 0.05;

    const animate = () => {
      // Clear canvas
      ctx.clearRect(0, 0, size, size);

      let amplitude = 0;

      // Get audio amplitude if analyzer is available
      if (audioAnalyzer && dataArray) {
        audioAnalyzer.getByteFrequencyData(dataArray);
        
        // Calculate average amplitude
        const sum = dataArray.reduce((acc, val) => acc + val, 0);
        amplitude = sum / bufferLength / 255; // Normalize to 0-1

        // If amplitude is below threshold, use idle animation
        if (amplitude < IDLE_THRESHOLD) {
          amplitude = 0.3 + Math.sin(Date.now() / 500) * 0.1;
        }
      } else {
        // Idle animation - gentle pulse when no analyzer
        amplitude = 0.3 + Math.sin(Date.now() / 500) * 0.1;
      }

      // Scale radius based on amplitude
      const scaledRadius = baseRadius + amplitude * 30;

      // Draw outer glow
      const gradient = ctx.createRadialGradient(
        centerX,
        centerY,
        scaledRadius * 0.5,
        centerX,
        centerY,
        scaledRadius * 1.2
      );
      gradient.addColorStop(0, `${themeColor}40`); // 25% opacity
      gradient.addColorStop(1, `${themeColor}00`); // 0% opacity
      
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(centerX, centerY, scaledRadius * 1.2, 0, Math.PI * 2);
      ctx.fill();

      // Draw main circle
      ctx.fillStyle = `${themeColor}80`; // 50% opacity
      ctx.beginPath();
      ctx.arc(centerX, centerY, scaledRadius, 0, Math.PI * 2);
      ctx.fill();

      // Draw inner circle
      ctx.fillStyle = themeColor;
      ctx.beginPath();
      ctx.arc(centerX, centerY, scaledRadius * 0.6, 0, Math.PI * 2);
      ctx.fill();

      // Continue animation
      animationFrameRef.current = requestAnimationFrame(animate);
    };

    // Start animation
    animate();

    // Cleanup
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
    };
  }, [isRecording, audioAnalyzer]);

  if (!isRecording) {
    return null;
  }

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="visualizer-title"
      aria-describedby="visualizer-description"
    >
      <div className="flex flex-col items-center gap-6">
        {/* Hidden title for screen readers */}
        <h2 id="visualizer-title" className="sr-only">
          Voice Recording in Progress
        </h2>
        <p id="visualizer-description" className="sr-only">
          Recording your voice message. The visualizer shows audio levels. Press Escape to cancel or click Stop to finish recording.
        </p>

        {/* Circular visualizer */}
        <canvas
          ref={canvasRef}
          className="w-[200px] h-[200px]"
          aria-label="Voice recording visualizer showing audio amplitude"
          role="img"
        />

        {/* Recording timer */}
        <div 
          className="text-4xl font-bold text-white tracking-wider"
          role="timer"
          aria-live="off"
          aria-label={`Recording time: ${formatRecordingTime(recordingTime)}`}
        >
          {formatRecordingTime(recordingTime)}
        </div>
      </div>
    </div>
  );
}
