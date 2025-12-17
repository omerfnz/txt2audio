import type { AxiosInstance } from "axios";
import axios from "axios";

// API tabanı: CloudSpaces için aynı domain, farklı port
export const getApiBase = () => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl) {
    console.log('Using API_BASE from env:', envUrl);
    return envUrl.replace(/\/$/, '');
  }

  // Localhost kontrolü - öncelikli
  const hostname = window.location.hostname;
  const isLocal = hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '0.0.0.0';
  
  if (isLocal) {
    const defaultUrl = 'http://localhost:8000/api';
    console.log('Using localhost API_BASE:', defaultUrl);
    return defaultUrl;
  }

  // CloudSpaces/Lightning AI'da çalışıyorsak, aynı domain farklı port kullan
  if (hostname.includes('cloudspaces.litng.ai') || hostname.includes('litng.ai')) {
    const protocol = window.location.protocol;
    // CloudSpaces'te backend her zaman port 8000'de çalışır
    // Frontend port numarası URL'de olmayabilir (varsayılan HTTPS 443)
    const backendUrl = `${protocol}//${hostname}:8000/api`;
    console.log('Using CloudSpaces API_BASE:', backendUrl);
    return backendUrl;
  }

  // Fallback: Local development
  const defaultUrl = 'http://localhost:8000/api';
  console.log('Using fallback API_BASE:', defaultUrl);
  return defaultUrl;
};

const API_BASE = getApiBase();

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

interface MusicListResponse {
  music: Array<{
    name: string;
    filename: string;
    path: string;
  }>;
}

const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 300000, // 5 dakika timeout (büyük dosyalar için)
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
    // Health endpoint API prefix'i olmadan root'ta
    const healthUrl = API_BASE.replace(/\/api$/, '') + '/health';
    console.log('Checking backend health at:', healthUrl);
    const response = await axios.get(healthUrl, {
      timeout: 5000, // Timeout'u artırdık
      validateStatus: (status) => status < 500 // 4xx hataları da başarılı sayılabilir
    });
    console.log('Backend health check response:', response.status);
    return response.status === 200;
  } catch (error: any) {
    console.error('Backend health check failed:', error.message);
    return false;
  }
}

export async function getReferenceVoices(): Promise<ReferenceVoicesResponse> {
  return retryRequest(async () => {
    console.log('Calling getReferenceVoices API:', API_BASE + "/reference-voices");
    const response = await api.get<ReferenceVoicesResponse>("/reference-voices");
    console.log('getReferenceVoices response:', response.data);
    return response.data;
  });
}

export async function getMusicList(): Promise<MusicListResponse> {
  return retryRequest(async () => {
    console.log('Calling getMusicList API:', API_BASE + "/music");
    const response = await api.get<MusicListResponse>("/music");
    console.log('getMusicList response:', response.data);
    return response.data;
  });
}

export async function createProject(
  formData: FormData
): Promise<ProjectResponse> {
  // Proje oluşturma işlemi uzun sürebilir (chunking, DB kayıtları)
  // Özellikle büyük dosyalar için daha uzun timeout
  const response = await api.post<ProjectResponse>("/projects/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    timeout: 300000, // 5 dakika (büyük dosyalar için)
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

export async function cancelProcessing(projectId: number): Promise<{ project_id: number; status: string; message: string }> {
  const response = await api.post<{ project_id: number; status: string; message: string }>(
    `/projects/${projectId}/cancel`
  );
  return response.data;
}

// Resume project response type
export interface ResumeProjectResponse {
  project_id: number;
  status: string;
  resume_count: number;
  total_chunks: number;
  processed_chunks: number;
  remaining_chunks: number;
  progress: number;
  message: string;
}

/**
 * Resume a cancelled or failed project.
 * Continues processing from where it left off.
 */
export async function resumeProject(
  projectId: number,
  useGpu: boolean = false
): Promise<ResumeProjectResponse> {
  const response = await api.post<ResumeProjectResponse>(
    `/projects/${projectId}/resume`,
    null,
    {
      params: {
        use_gpu: useGpu,
      },
    }
  );
  return response.data;
}