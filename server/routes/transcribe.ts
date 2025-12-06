import { RequestHandler } from "express";
import { TranscriptionResponse } from "@shared/api";

export const handleTranscribe: RequestHandler = async (req, res) => {
  try {
    // Check if file was uploaded
    if (!req.file) {
      const errorResponse: TranscriptionResponse = {
        text: "",
        success: false,
        error: "No audio file provided",
      };
      return res.status(400).json(errorResponse);
    }

    // Prepare form data to send to AI Brain
    const formData = new FormData();
    
    // Create a blob from the buffer - convert Buffer to Uint8Array first
    const uint8Array = new Uint8Array(req.file.buffer);
    const audioBlob = new Blob([uint8Array], { type: req.file.mimetype });
    formData.append("audio", audioBlob, req.file.originalname);
    formData.append("prompt", "Transcribe this audio");

    // Forward to AI Brain service
    const aiBrainUrl = "http://localhost:8001/router";
    
    const response = await fetch(aiBrainUrl, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`AI Brain service returned status ${response.status}`);
    }

    const data = await response.json();
    
    // Extract transcribed text from AI Brain response
    const transcribedText = data.response || data.text || "";

    const successResponse: TranscriptionResponse = {
      text: transcribedText,
      success: true,
    };

    res.json(successResponse);
  } catch (error) {
    console.error("Transcription error:", error);
    
    let errorMessage = "Transcription failed";
    
    if (error instanceof Error) {
      if (error.message.includes("ECONNREFUSED") || error.message.includes("fetch failed")) {
        errorMessage = "AI Brain service is unavailable";
      } else if (error.message.includes("timeout")) {
        errorMessage = "Transcription request timed out";
      } else {
        errorMessage = error.message;
      }
    }

    const errorResponse: TranscriptionResponse = {
      text: "",
      success: false,
      error: errorMessage,
    };

    res.status(500).json(errorResponse);
  }
};
