import type { AxiosInstance } from "axios";
import axios from "axios";

// Lightning AI ve localhost uyumlu dinamik API URL
const API_BASE = window.location.hostname === 'localhost' 
  ? "http://localhost:8000/api"
  : `${window.location.protocol}//${window.location.hostname.replace('4173', '8000')}/api`;

interface ReferenceVoicesResponse {
  voices: Record<
    string,
    Array<{
      name: string;
      path: string;
      filename: string;
    }>
  >;
  error?: string;
}

interface ProjectResponse {
  project_id: number;
  total_chunks: number;
  message: string;
}

interface ProjectStatusResponse {
  id: number;
  name: string;
  status: string;
  total_chunks: number;
  processed_chunks: number;
  progress: number;
}

const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 10000, // 10 saniye timeout
});

// Retry logic helper
async function retryRequest<T>(
  requestFn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      
      console.log(`Retry ${i + 1}/${maxRetries} after ${delay}ms...`);
      await new Promise(resolve => setTimeout(resolve, delay));
      delay *= 2; // Exponential backoff
    }
  }
  throw new Error("Max retries exceeded");
}

// Backend health check
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await axios.get(`${API_BASE.replace('/api', '')}/health`, {
      timeout: 2000
    });
    return response.status === 200;
  } catch {
    return false;
  }
}

export async function getReferenceVoices(): Promise<ReferenceVoicesResponse> {
  return retryRequest(async () => {
    const response = await api.get<ReferenceVoicesResponse>("/reference-voices");
    return response.data;
  });
}

export async function createProject(
  formData: FormData
): Promise<ProjectResponse> {
  const response = await api.post<ProjectResponse>("/projects/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
}

export async function startProcessing(
  projectId: number,
  useGpu: boolean = false
): Promise<{ message: string }> {
  const response = await api.post<{ message: string }>(
    `/projects/${projectId}/process`,
    null,
    {
      params: {
        use_gpu: useGpu,
      },
    }
  );
  return response.data;
}

export async function getProjectStatus(
  projectId: number
): Promise<ProjectStatusResponse> {
  const response = await api.get<ProjectStatusResponse>(
    `/projects/${projectId}`
  );
  return response.data;
}

export async function getAllProjects(): Promise<{
  projects: Array<{
    id: number;
    name: string;
    status: string;
    created_at: string | null;
    audio_path?: string | null;
  }>;
}> {
  const response = await api.get("/projects");
  return response.data;
}

export async function deleteProject(projectId: number): Promise<{ message: string }> {
  const response = await api.delete(`/projects/${projectId}`);
  return response.data;
}

export async function getTTSPresets(): Promise<{ presets: Record<string, any> }> {
  return retryRequest(async () => {
    const response = await api.get("/tts-presets");
    return response.data;
  });
}

// ACX / Audio Quality
export interface AudioQualityResponse {
  project_id: number;
  audio_path: string;
  analysis: {
    rms_db: number;
    peak_db: number;
    noise_floor_db: number;
    acx_compliant: boolean;
    duration_seconds: number;
    sample_rate: number;
    channels: number;
  };
  compliance_details: {
    rms: {
      value: number;
      pass: boolean;
      target: string;
      description: string;
    };
    peak: {
      value: number;
      pass: boolean;
      target: string;
      description: string;
    };
    noise_floor: {
      value: number;
      pass: boolean;
      target: string;
      description: string;
    };
  };
  overall_acx_compliant: boolean;
}

export async function getAudioQuality(projectId: number): Promise<AudioQualityResponse> {
  const response = await api.get<AudioQualityResponse>(`/projects/${projectId}/audio-quality`);
  return response.data;
}

export async function normalizeAudio(projectId: number): Promise<{ project_id: number; message: string; status: string }> {
  const response = await api.post<{ project_id: number; message: string; status: string }>(
    `/projects/${projectId}/normalize`
  );
  return response.data;
}

export async function cancelProcessing(projectId: number): Promise<{ project_id: number; status: string; message: string }> {
  const response = await api.post<{ project_id: number; status: string; message: string }>(
    `/projects/${projectId}/cancel`
  );
  return response.data;
}