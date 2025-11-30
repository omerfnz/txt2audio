# 🎙️ AI Audiobook Studio - Frontend

Modern, responsive, and user-friendly interface for the AI Audiobook Studio, built with React, TypeScript, and Tailwind CSS.

## 🚀 Features

- **Project Management**: Create, view, and manage audiobook projects.
- **Reference Voice Selection**: Upload custom voices or choose from pre-defined high-quality voices.
- **Real-time Progress**: WebSocket integration for live progress updates during audio generation.
- **Audio Player**: Integrated audio player to preview generated chunks and the final audiobook.
- **Responsive Design**: Works seamlessly on different screen sizes.
- **Dark/Light Mode**: (If applicable, otherwise just "Modern UI") Sleek and modern interface.

## 🛠️ Tech Stack

- **Framework**: [React 18](https://reactjs.org/)
- **Build Tool**: [Vite](https://vitejs.dev/)
- **Language**: [TypeScript](https://www.typescriptlang.org/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
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
├── hooks/          # Custom React hooks
├── pages/          # Page components (if using routing)
├── App.tsx         # Main application component
└── main.tsx        # Entry point
```

## 🔧 Configuration

- **API URL**: Configured in `src/api/client.ts` (defaults to `http://localhost:8000`).
