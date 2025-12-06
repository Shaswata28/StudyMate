import { RequestHandler } from "express";
import multer from "multer";
import FormData from "form-data";

// Configure multer for memory storage
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 25 * 1024 * 1024, // 25MB limit (Whisper's max)
  },
});

// Middleware to handle file upload
export const uploadAudio = upload.single('audio');

// Handler for transcription
export const handleTranscribe: RequestHandler = async (req, res) => {
  try {
    // Check if file was uploaded
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No audio file provided',
      });
    }

    // Create form data to send to AI Brain
    const formData = new FormData();
    formData.append('audio', req.file.buffer, {
      filename: req.file.originalname || 'recording.webm',
      contentType: req.file.mimetype,
    });
    formData.append('prompt', 'Transcribe this audio');

    // Forward to AI Brain service
    const aiBrainUrl = process.env.AI_BRAIN_URL || 'http://localhost:8001';
    const response = await fetch(`${aiBrainUrl}/router`, {
      method: 'POST',
      body: formData as any,
      headers: formData.getHeaders(),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('AI Brain transcription error:', errorText);
      
      return res.status(response.status).json({
        success: false,
        error: `Transcription service error: ${response.statusText}`,
      });
    }

    const data = await response.json();

    // Return transcribed text
    return res.json({
      success: true,
      text: data.response || data.text || '',
      model: data.model,
    });
  } catch (error) {
    console.error('Transcription error:', error);
    
    // Handle specific error types
    if (error instanceof Error) {
      if (error.message.includes('ECONNREFUSED')) {
        return res.status(503).json({
          success: false,
          error: 'AI Brain service is unavailable. Please ensure it is running.',
        });
      }
      
      if (error.message.includes('timeout')) {
        return res.status(504).json({
          success: false,
          error: 'Transcription request timed out. Please try again.',
        });
      }
    }

    return res.status(500).json({
      success: false,
      error: 'Internal server error during transcription',
    });
  }
};
