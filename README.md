# Vocation.ai
Empowering rural India's youth through AI driven education and employment solutions. We bridge the gap between learning and earning, fostering nation's development and individual growth.

## How to Use

- **View the Project**: To see the output, visit: [link >](https://vocation-ai.web.app)
- **Local Setup**: Please note that the project’s backend and major functionalities will not run locally. This is due to the removal of API keys, system prompts, and other sensitive credentials to ensure security and prevent unauthorized access.
- **Assets**: Images, PDFs, audio files, and other assets have been removed due to file size limitations. As a result, the project will not be fully functional in a local environment.
- **Codebase Access**: Despite these removals, the full codebase is available for thorough review.

# Prototype
[Try Out >](https://vocation-ai.web.app/)

# Technology
```mermaid
    %%{init: {'theme': 'neutral', 'themeVariables': { 'primaryColor': '#830C4F', 'primaryTextColor': '#fff', 'primaryBorderColor': '#6a0a3f', 'lineColor': '#830C4F', 'secondaryColor': '#006100', 'tertiaryColor': '#fff'}}}%%
    graph TD
        A((("Vocation.ai<br>Technology"))):::mainNode --> B{{"Tutor AI"}}:::feature
        A --> C{{"Quiz AI"}}:::feature
        A --> D{{"Job AI"}}:::feature
        A --> ASSSA{{"Online Community"}}:::feature
        ASSSA --> SSSSA["Peers, Mentors, and<br>Technical Admins"]
        
        B --> XssaA["RAG Architecture"]
        
        XssaA --> E["LangChain Framework"]
        XssaA --> F["OpenAI GPT-4 Turbo"]
        XssaA --> G["Google Gemini-1.5 Pro"]
        XssaA --> H[("Pinecone DB")]:::database
        
        H --> I["Vector Embeddings"]
        I --> J[("Knowledge Base")]:::database
        J --> QQWQ["Dynamic Knowledge Update<br>through Internet Access"]
        QQWQ --> SFAS["Curated by Admins"]
        I --> K[("Student Memory")]:::database
        K --> DSD["Strengths & Weaknesses,<br>Topics Covered,<br>Learning Style etc."]
        DSD --> DGFS["Adaptive and<br>Personalised Learning"]
        
        B --> L["Multimodal AI"]
        B --> 12HJK["Learning Path Generator"]
        12HJK --> rraaA["Notes AI"]
        rraaA --> sggds[YouTube AI]
        sggds --> ffaggt[Mindmap Generator]
        ffaggt --> gg1121[Productivity AI 'To-Do List AI, Pomodoro Timer & My Calendar']
        gg1121 --> ssq1tt1[V.ai Live 'Live Video-Chat Study Sessions with Peers']
        ssq1tt1 --> sssaa1111[V.ai Relax 'Calming Music, Inspiring Quotes & Ambient Images—perfect for a break']
        L --> SS14["Multiple Indic Languages"]
        SS14 --> DB168["Voice Recognition and<br>Text-To-Speech<br>'ResponseVoice.JS API'"]
        DB168 --> X23100["Face expression detection AI<br>using webcam 'Face++ API'"]
        X23100 --> M["Vision-powered System"]

        M --> SS["Screen Monitoring"]
        M --> DD["File / Image Upload"]

        SS --> XY["Real-Time Guidance"]
        DD --> XY
        XY --> Z141["Autograding Homework<br>using vision capabilities"]
        
        C --> 12DFFF1["Access to Knowledge Base"]
        12DFFF1 --> N["AI-Powered Subjective Quiz, Objective Quiz & Flashcards Generation"]
        1JH23 --> QW["Learning Progress Tracking"]
        N --> O["Test Student Knowledge"]
        O --> 1JH23["Gamification and<br>Reward Points"]
        QW --> HFX["Determine Job Readiness"]
        HFX --> DOP21["AI Proctoring monitors<br>Tab switching, Shared Screen<br>Content and Webcam Activity"]

        D --> R["Job Search APIs &<br>Web Scraping"]
        R --> 4W1["Job Recommendation"]
        4W1 --> S["Remote Job Opportunities"]
        S --> D12["Job Quality<br>Feedback Mechanism"]
        
        D --> T["Vision-powered Chat System"]
        T --> U["Assist with Job Tasks"]
        T --> V["Quality Control"]

        D --> 12HHQ["Resume AI"]
        D --> 14HHQ["Interview AI"]    

        B -.-> C
        C -.-> D
        D -.-> B

        classDef mainNode fill:#830C4F,stroke:#fff,color:#fff;
        classDef database fill:#e1e1e1,stroke:#333,stroke-width:2px;
        classDef feature fill:#830C4F,stroke:#6a0a3f,color:#fff;
        
        ```
