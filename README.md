# 🎥 Video Insight Chatbot

A powerful chatbot that allows users to ask questions about the content of a video — whether by uploading a file, providing a YouTube link, or even submitting a screenshot to locate specific moments in the video.

---

## ✨ Features

- 📹 Upload a YouTube URL.
- 🔍 Ask natural language questions about video content (speech, scenes, visuals).
- 🖼️ Submit a screenshot/image and ask it.
- 🧠 Backed by modern multimodal AI techniques (speech + image + text).

---

## 🔄 System Pipeline

```mermaid
graph TD
    A[User Input: Youtube URL] --> B[Video Downloader and Preprocessing]
    B --> C[ASR]
    C --> D[Transcription - chunked]
    B --> E[Frame Sampling - 1 fps for image search]

    D --> F[Video Chunk Mapping by Timestamp]
    F --> G[VLM]
    
    G --> H[Extracted Visual Information:
        - Caption
        - Object Detection
        - OCR
        - Activity
        - Scene
        - Lighting]
    
    H --> I[Merge with Transcript Text]
    I --> J[Embed Text Segments]
    
    J --> K[Store in Text Vector DB]
    E --> L[Embed Sampled Frames]
    L --> M[Store in Image Vector DB]
    
    N[User Input: Question or Image] --> O[Query Processing]
    
    O --> P{Image provided?}
    
    P -- Yes --> Q1[Embed Query Image]
    Q1 --> R1[Search in Image Vector DB]
    R1 --> S1[Map to Timestamp]
    S1 --> T1[Retrieve Related Text Segments]

    P -- Yes --> Q2[Feed Image to VLM]
    Q2 --> R2[Extract Visual Text from Image]
    R2 --> S2[Embed Visual Text]
    S2 --> T2[Search in Text Vector DB]

    P -- No --> U[Embed Text Query]
    U --> V[Search in Text Vector DB]

    %% Merge logic
    T1 --> W[Contextual Answer by LLM]
    T2 --> W
    V  --> W
    W --> X[Chatbot Response]

```

## Technologies Used
- Video Downloader: yt-dlp
- Transcription (ASR): Whisper.cpp (don't use when have subtitles in video)
- Image Embedding:
- Video Analysis: SmolVLM2
  - Detail Caption
  - Object Detection
  - Text in image (OCR)
  - Actions or activity
  - Spatial context / scene	
  - Time / lighting context	
- Vector Store: Qdrant
- Contextual Answering: LLM


