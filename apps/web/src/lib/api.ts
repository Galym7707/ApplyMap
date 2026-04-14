import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach auth token from session if available
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("sourcelock_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("sourcelock_token");
        const isAuthPage = ["/sign-in", "/sign-up"].includes(window.location.pathname);
        if (!isAuthPage) {
          window.location.href = "/sign-in";
        }
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const authApi = {
  signup: (data: { email: string; password: string; full_name?: string; country?: string }) =>
    api.post("/api/auth/signup", data),
  login: (data: { email: string; password: string }) =>
    api.post("/api/auth/login", data),
  logout: () => api.post("/api/auth/logout"),
  me: () => api.get("/api/auth/me"),
};

// Profile
export const profileApi = {
  get: () => api.get("/api/profile"),
  update: (data: Record<string, unknown>) => api.put("/api/profile", data),
  updateUser: (data: Record<string, unknown>) => api.put("/api/profile/user", data),
};

// Achievements
export const achievementsApi = {
  list: (type?: string) => api.get("/api/achievements", { params: type ? { type } : {} }),
  get: (id: string) => api.get(`/api/achievements/${id}`),
  create: (data: Record<string, unknown>) => api.post("/api/achievements", data),
  update: (id: string, data: Record<string, unknown>) => api.put(`/api/achievements/${id}`, data),
  delete: (id: string) => api.delete(`/api/achievements/${id}`),
  upload: (id: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post(`/api/achievements/${id}/upload`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

// Universities
export const universitiesApi = {
  list: (params?: {
    search?: string;
    country?: string;
    region?: string;
    application_system?: string;
    teaching_language?: string;
    major?: string;
    school_years?: string | number;
    full_ride_only?: boolean;
    common_app_only?: boolean;
    aid_type?: string;
    sort_by?: string;
    sort_dir?: string;
  }) =>
    api.get("/api/universities", { params }),
  get: (id: string) => api.get(`/api/universities/${id}`),
  getSources: (id: string) => api.get(`/api/universities/${id}/sources`),
  recommendCommonApp: (data: {
    top_honor_ids: string[];
    top_activity_ids: string[];
    preferences: Record<string, unknown>;
    save_preferences?: boolean;
  }) => api.post("/api/universities/recommendations/common-app", data),
};

// Targets
export const targetsApi = {
  list: () => api.get("/api/targets"),
  add: (data: { university_id: string; priority_order?: number }) =>
    api.post("/api/targets", data),
  remove: (id: string) => api.delete(`/api/targets/${id}`),
};

// Reports
export const reportsApi = {
  generate: (universityId: string) =>
    api.post("/api/reports/generate", null, { params: { university_id: universityId } }),
  list: () => api.get("/api/reports"),
  get: (id: string) => api.get(`/api/reports/${id}`),
  export: (id: string) => api.get(`/api/reports/${id}/export`),
};
