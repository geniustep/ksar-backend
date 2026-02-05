import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  UserProfileResponse,
  UpdateProfileRequest,
  ChangePasswordRequest,
  CitizenRequestCreate,
  CitizenRequestUpdate,
  CitizenRequestResponse,
  CitizenRequestCreatedResponse,
  CitizenStats,
  RequestResponse,
  RequestDetailResponse,
  PaginatedRequests,
  RequestAdminUpdate,
  RequestTrackResponse,
  AssignmentCreate,
  AssignmentUpdate,
  AssignmentResponse,
  AssignmentWithRequest,
  PaginatedAssignments,
  OrgStats,
  OverviewStats,
  DailyStats,
  RegionalStats,
  AdminOrgStats,
  AdminOrgList,
  RequestStatus,
  RequestCategory,
  AssignmentStatus,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: 'خطأ في الخادم' }));
    throw new ApiError(res.status, body.detail || 'خطأ غير متوقع');
  }

  if (res.status === 204) return {} as T;
  return res.json();
}

// === Auth API ===

export const authApi = {
  login(data: LoginRequest): Promise<LoginResponse> {
    return request('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  register(data: RegisterRequest): Promise<RegisterResponse> {
    return request('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getMe(): Promise<UserProfileResponse> {
    return request('/api/v1/auth/me');
  },

  updateProfile(data: UpdateProfileRequest): Promise<UserProfileResponse> {
    return request('/api/v1/auth/me', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  changePassword(data: ChangePasswordRequest): Promise<{ message: string }> {
    return request('/api/v1/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  refreshToken(): Promise<{ access_token: string; token_type: string }> {
    return request('/api/v1/auth/refresh', {
      method: 'POST',
    });
  },
};

// === Public API ===

export const publicApi = {
  trackRequest(trackingCode: string, phone: string): Promise<RequestTrackResponse> {
    return request(
      `/api/v1/public/requests/track/${trackingCode}?phone=${encodeURIComponent(phone)}`
    );
  },

  getCategories(): Promise<Record<string, string>> {
    return request('/api/v1/public/categories');
  },
};

// === Citizen API ===

export const citizenApi = {
  createRequest(data: CitizenRequestCreate): Promise<CitizenRequestCreatedResponse> {
    return request('/api/v1/citizen/requests', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getMyRequests(status?: RequestStatus): Promise<CitizenRequestResponse[]> {
    const params = status ? `?status=${status}` : '';
    return request(`/api/v1/citizen/requests${params}`);
  },

  getRequest(requestId: string): Promise<CitizenRequestResponse> {
    return request(`/api/v1/citizen/requests/${requestId}`);
  },

  updateRequest(requestId: string, data: CitizenRequestUpdate): Promise<CitizenRequestResponse> {
    return request(`/api/v1/citizen/requests/${requestId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  cancelRequest(requestId: string): Promise<{ message: string }> {
    return request(`/api/v1/citizen/requests/${requestId}`, {
      method: 'DELETE',
    });
  },

  getStats(): Promise<CitizenStats> {
    return request('/api/v1/citizen/stats');
  },
};

// === Organization API ===

export const orgApi = {
  getAvailableRequests(params?: {
    category?: RequestCategory;
    region?: string;
    page?: number;
    limit?: number;
  }): Promise<PaginatedRequests> {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.set('category', params.category);
    if (params?.region) searchParams.set('region', params.region);
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    const qs = searchParams.toString();
    return request(`/api/v1/org/requests/available${qs ? '?' + qs : ''}`);
  },

  getRequest(requestId: string): Promise<RequestResponse> {
    return request(`/api/v1/org/requests/${requestId}`);
  },

  createAssignment(data: AssignmentCreate): Promise<AssignmentResponse> {
    return request('/api/v1/org/assignments', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getMyAssignments(params?: {
    status?: AssignmentStatus;
    page?: number;
    limit?: number;
  }): Promise<PaginatedAssignments> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set('status', params.status);
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    const qs = searchParams.toString();
    return request(`/api/v1/org/assignments${qs ? '?' + qs : ''}`);
  },

  getAssignment(assignmentId: string): Promise<AssignmentWithRequest> {
    return request(`/api/v1/org/assignments/${assignmentId}`);
  },

  updateAssignment(assignmentId: string, data: AssignmentUpdate): Promise<AssignmentResponse> {
    return request(`/api/v1/org/assignments/${assignmentId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  getStats(): Promise<OrgStats> {
    return request('/api/v1/org/stats');
  },
};

// === Admin API ===

export const adminApi = {
  getRequests(params?: {
    status?: RequestStatus;
    category?: RequestCategory;
    region?: string;
    is_urgent?: boolean;
    search?: string;
    page?: number;
    limit?: number;
  }): Promise<PaginatedRequests> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set('status', params.status);
    if (params?.category) searchParams.set('category', params.category);
    if (params?.region) searchParams.set('region', params.region);
    if (params?.is_urgent !== undefined) searchParams.set('is_urgent', String(params.is_urgent));
    if (params?.search) searchParams.set('search', params.search);
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    const qs = searchParams.toString();
    return request(`/api/v1/admin/requests${qs ? '?' + qs : ''}`);
  },

  getRequest(requestId: string): Promise<RequestDetailResponse> {
    return request(`/api/v1/admin/requests/${requestId}`);
  },

  updateRequest(
    requestId: string,
    data: RequestAdminUpdate
  ): Promise<{ message: string; data: RequestResponse }> {
    return request(`/api/v1/admin/requests/${requestId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  deleteRequest(requestId: string): Promise<{ message: string }> {
    return request(`/api/v1/admin/requests/${requestId}`, {
      method: 'DELETE',
    });
  },

  getOverviewStats(): Promise<OverviewStats> {
    return request('/api/v1/admin/stats/overview');
  },

  getDailyStats(days?: number): Promise<DailyStats> {
    const qs = days ? `?days=${days}` : '';
    return request(`/api/v1/admin/stats/daily${qs}`);
  },

  getRegionalStats(): Promise<RegionalStats> {
    return request('/api/v1/admin/stats/by-region');
  },

  getOrgStats(): Promise<AdminOrgStats> {
    return request('/api/v1/admin/stats/organizations');
  },

  getOrganizations(params?: {
    status?: string;
    page?: number;
    limit?: number;
  }): Promise<AdminOrgList> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set('status', params.status);
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    const qs = searchParams.toString();
    return request(`/api/v1/admin/organizations${qs ? '?' + qs : ''}`);
  },

  updateOrgStatus(orgId: string, status: string): Promise<{ message: string }> {
    return request(`/api/v1/admin/organizations/${orgId}/status?status=${status}`, {
      method: 'PATCH',
    });
  },
};

export { ApiError };
