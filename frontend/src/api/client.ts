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
});

export async function getReferenceVoices(): Promise<ReferenceVoicesResponse> {
  const response = await api.get<ReferenceVoicesResponse>("/reference-voices");
  return response.data;
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
  }>;
}> {
  const response = await api.get("/projects");
  return response.data;
}
