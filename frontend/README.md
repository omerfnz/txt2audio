# 🎙️ AI Audiobook Studio - Frontend

Modern, responsive, and user-friendly interface for the AI Audiobook Studio, built with React, TypeScript, Tailwind CSS, and ShadCN UI.

## 🚀 Features

- **Project Management**: Create, view, and manage audiobook projects.
- **Reference Voice Selection**: Upload custom voices or choose from pre-defined high-quality voices.
- **Real-time Progress**: WebSocket integration for live progress updates during audio generation.
- **Audio Player**: Integrated audio player to preview generated chunks and the final audiobook.
- **ACX Quality Analysis**: Analyze and normalize audio for Audible ACX compliance.
- **Chunk Quality Control**: Visual feedback for chunk processing status and retry attempts.
- **Process Cancellation**: Cancel ongoing audio generation processes.
- **Responsive Design**: Works seamlessly on different screen sizes.
- **Modern UI**: ShadCN UI components with TweakCN Cosmic Night theme.

## 🛠️ Tech Stack

- **Framework**: [React 18](https://reactjs.org/)
- **Build Tool**: [Vite](https://vitejs.dev/)
- **Language**: [TypeScript](https://www.typescriptlang.org/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **UI Components**: [ShadCN UI](https://ui.shadcn.com/)
- **Theme**: [TweakCN Cosmic Night](https://tweakcn.com/r/themes/cosmic-night.json)
- **State Management**: [Zustand](https://github.com/pmndrs/zustand)
- **API Client**: [Axios](https://axios-http.com/)
- **Icons**: [Lucide React](https://lucide.dev/)

## 📦 Installation & Setup

The frontend is automatically set up via the root `setup-all.cmd` script. However, if you need to set it up manually:

```bash
cd frontend
npm install
```

## 🏃‍♂️ Running Locally

To start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

## 🏗️ Project Structure

```
src/
├── api/            # API client and types
├── components/     # Reusable UI components
│   ├── upload/     # Upload form components
│   └── ui/         # ShadCN UI components (lib/utils.ts, etc.)
├── hooks/          # Custom React hooks
├── views/          # Page views (Upload, Project)
├── types/          # TypeScript type definitions
├── App.tsx         # Main application component
└── main.tsx         # Entry point
```

## 🔧 Configuration

- **API URL**: Configured in `src/api/client.ts` (defaults to `http://localhost:8000`).
- **ShadCN UI**: Configured via `components.json` in the root directory.
- **Theme**: Cosmic Night theme from TweakCN applied via Tailwind CSS configuration.
