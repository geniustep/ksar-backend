// === Enums ===

export type UserRole = 'admin' | 'organization' | 'citizen';
export type UserStatus = 'active' | 'suspended';

export type RequestCategory =
  | 'food'
  | 'water'
  | 'shelter'
  | 'medicine'
  | 'clothes'
  | 'blankets'
  | 'baby_supplies'
  | 'hygiene'
  | 'financial'
  | 'other';

export type RequestStatus = 'new' | 'assigned' | 'in_progress' | 'completed' | 'cancelled';
export type AssignmentStatus = 'pledged' | 'in_progress' | 'completed' | 'failed';
export type OrganizationStatus = 'active' | 'suspended';

// === Auth ===

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  phone: string;
  address?: string;
  city?: string;
  region?: string;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  role: UserRole;
  organization_id: string | null;
  organization_name: string | null;
}

export interface UserProfileResponse extends UserResponse {
  address: string | null;
  city: string | null;
  region: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export interface RegisterResponse {
  message: string;
  user: UserResponse;
  access_token: string;
  token_type: string;
}

export interface UpdateProfileRequest {
  full_name?: string;
  phone?: string;
  address?: string;
  city?: string;
  region?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

// === Requests ===

export interface CitizenRequestCreate {
  category: RequestCategory;
  description: string;
  quantity: number;
  family_members: number;
  address?: string;
  city?: string;
  region?: string;
  latitude?: number;
  longitude?: number;
  is_urgent: boolean;
}

export interface CitizenRequestUpdate {
  description?: string;
  quantity?: number;
  family_members?: number;
  address?: string;
  city?: string;
  region?: string;
  is_urgent?: boolean;
}

export interface RequestResponse {
  id: string;
  requester_name: string;
  requester_phone: string;
  category: RequestCategory;
  description: string;
  quantity: number;
  family_members: number;
  address: string;
  city: string | null;
  region: string | null;
  latitude: number | null;
  longitude: number | null;
  status: RequestStatus;
  priority_score: number;
  is_urgent: number;
  created_at: string;
  updated_at: string | null;
  completed_at: string | null;
}

export interface CitizenRequestResponse {
  id: string;
  tracking_code: string;
  category: RequestCategory;
  description: string;
  quantity: number;
  family_members: number;
  address: string;
  city: string | null;
  region: string | null;
  status: RequestStatus;
  status_ar: string;
  is_urgent: boolean;
  created_at: string;
  updated_at: string | null;
  completed_at: string | null;
  organization_name: string | null;
}

export interface CitizenRequestCreatedResponse {
  id: string;
  tracking_code: string;
  message: string;
}

export interface RequestDetailResponse extends RequestResponse {
  admin_notes: string | null;
  assignments: AssignmentBriefResponse[];
}

export interface RequestTrackResponse {
  id: string;
  status: RequestStatus;
  status_ar: string;
  category: RequestCategory;
  created_at: string;
  updated_at: string | null;
  organization_name: string | null;
}

export interface PaginatedRequests {
  items: RequestResponse[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

export interface RequestAdminUpdate {
  status?: RequestStatus;
  priority_score?: number;
  is_urgent?: boolean;
  admin_notes?: string;
}

// === Assignments ===

export interface AssignmentCreate {
  request_id: string;
  notes?: string;
}

export interface AssignmentUpdate {
  status: AssignmentStatus;
  completion_notes?: string;
  failure_reason?: string;
}

export interface AssignmentResponse {
  id: string;
  request_id: string;
  org_id: string;
  status: AssignmentStatus;
  notes: string | null;
  completion_notes: string | null;
  failure_reason: string | null;
  created_at: string;
  updated_at: string | null;
  completed_at: string | null;
}

export interface AssignmentBriefResponse {
  id: string;
  org_id: string;
  status: AssignmentStatus;
  created_at: string;
}

export interface AssignmentWithRequest {
  assignment: AssignmentResponse;
  request: {
    id: string;
    requester_name: string;
    requester_phone: string;
    category: string;
    description: string;
    quantity: number;
    family_members: number;
    address: string;
    city: string | null;
    region: string | null;
    latitude: number | null;
    longitude: number | null;
    is_urgent: number;
  };
}

export interface PaginatedAssignments {
  items: AssignmentResponse[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

// === Statistics ===

export interface OverviewStats {
  data: {
    total_requests: number;
    by_status: Record<string, number>;
    by_category: Record<string, number>;
    urgent_count: number;
    avg_completion_hours: number | null;
    active_organizations: number;
  };
}

export interface DailyStats {
  data: Array<{
    date: string;
    count: number;
  }>;
}

export interface RegionalStats {
  data: Array<{
    region: string;
    total: number;
    new: number;
    completed: number;
  }>;
}

export interface OrgStats {
  data: {
    total_assignments: number;
    by_status: Record<string, number>;
    total_completed: number;
  };
}

export interface CitizenStats {
  total_requests: number;
  by_status: Record<string, number>;
}

export interface AdminOrgStats {
  data: Array<{
    id: string;
    name: string;
    total_assignments: number;
    completed: number;
  }>;
}

export interface AdminOrgListItem {
  id: string;
  name: string;
  contact_phone: string;
  contact_email: string;
  status: string;
  total_completed: number;
  created_at: string;
}

export interface AdminOrgList {
  items: AdminOrgListItem[];
  total: number;
  page: number;
  limit: number;
}
