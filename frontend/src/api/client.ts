import type { AxiosInstance } from "axios";
import axios from "axios";

// API tabanı: CloudSpaces için aynı domain, farklı port
export const getApiBase = () => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl) {
    return envUrl.replace(/\/$/, '');
  }

  // Localhost kontrolü - öncelikli
  const hostname = window.location.hostname;
  const isLocal = hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '0.0.0.0';
  
  if (isLocal) {
    return 'http://localhost:8000/api';
  }

  // CloudSpaces/Lightning AI'da çalışıyorsak
  if (hostname.includes('cloudspaces.litng.ai') || hostname.includes('litng.ai')) {
    const protocol = window.location.protocol;
    
    if (hostname.startsWith('5173-') || hostname.startsWith('4173-')) {
      // CloudSpaces'te iki olasılık:
      // 1. Vite proxy: Aynı origin, /api path'i Vite tarafından localhost:8000'e yönlendirilir
      // 2. Backend subdomain: 8000-xxx.cloudspaces.litng.ai
      
      // Önce Vite proxy'yi dene (CloudSpaces'te aynı container içinde çalışıyorsa)
      const proxyUrl = `${protocol}//${hostname}/api`;
      return proxyUrl;
    }
    
    // Eğer zaten 8000- ile başlıyorsa (backend subdomain)
    if (hostname.startsWith('8000-')) {
      return `${protocol}//${hostname}/api`;
    }
    
    // Fallback: Aynı hostname, port 8000 ekle
    return `${protocol}//${hostname}:8000/api`;
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
  started_at?: string | null;
  completed_at?: string | null;
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

// Request interceptor: Her istekte güncel baseURL'i kullan
api.interceptors.request.use((config) => {
  // Her istekte güncel API base URL'i al (CloudSpaces'te subdomain değişebilir)
  const currentApiBase = getApiBase();
  config.baseURL = currentApiBase;
  return config;
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
    // Health endpoint: Vite proxy kullanıyorsak /api/health, değilse /health
    // getApiBase() kullanarak güncel URL'i al (modül seviyesindeki API_BASE eski olabilir)
    const currentApiBase = getApiBase();
    // Vite proxy kullanıyorsak (same origin, /api prefix var), /api/health kullan
    // Değilse /health kullan (backend'in root endpoint'i)
    const isProxy = currentApiBase.includes('/api') && !currentApiBase.includes(':8000');
    const healthUrl = isProxy 
      ? `${currentApiBase}/health`
      : currentApiBase.replace(/\/api$/, '') + '/health';
    
    // Sadece error durumunda log basalım
    const response = await axios.get(healthUrl, {
      timeout: 10000, // CloudSpaces'te ağ gecikmesi olabilir, timeout'u artırdık
      validateStatus: (status) => status < 500, // 4xx hataları da başarılı sayılabilir
      headers: {
        'Accept': 'application/json',
      }
    });
    
    console.log('Backend health check response:', response.status, response.data);
    return response.status === 200;
  } catch (error: unknown) {
    // Detaylı hata loglama
    if (error && typeof error === 'object' && 'response' in error) {
      const axiosError = error as { response?: { status: number; data: unknown }; request?: unknown; message?: string };
      // Sunucu yanıt verdi ama hata kodu döndü
      if (axiosError.response) {
        console.error('Backend health check failed:', axiosError.response.status, axiosError.response.data);
      } else if (axiosError.request) {
        // İstek gönderildi ama yanıt alınamadı (timeout, network error)
        console.error('Backend health check failed: No response received', axiosError.message || 'Unknown error');
      } else {
        // İstek hazırlanırken hata oluştu
        console.error('Backend health check failed:', axiosError.message || 'Unknown error');
      }
    } else {
      console.error('Backend health check failed:', error);
    }
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

export async function getTTSPresets(): Promise<{ presets: Record<string, unknown> }> {
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

// Chapters

export interface ChaptersResponse {
  project_id: number;
  chapters: Array<{
    title: string;
    order: number;
    chunk_index: number;
  }>;
  total: number;
}

export async function getChapters(projectId: number): Promise<ChaptersResponse> {
  const response = await api.get<ChaptersResponse>(
    `/projects/${projectId}/chapters`
  );
  return response.data;
}

// Timelapse

export interface TimelapseResponse {
  project_id: number;
  timelapse: string;
  chapters_count: number;
  message?: string;
}

export async function getTimelapse(projectId: number): Promise<TimelapseResponse> {
  const response = await api.get<TimelapseResponse>(
    `/projects/${projectId}/timelapse`
  );
  return response.data;
}