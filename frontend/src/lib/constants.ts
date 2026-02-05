import type { RequestCategory, RequestStatus, AssignmentStatus } from './types';

export const CATEGORY_LABELS: Record<RequestCategory, string> = {
  food: 'غذاء',
  water: 'ماء',
  shelter: 'مأوى',
  medicine: 'دواء',
  clothes: 'ملابس',
  blankets: 'أغطية',
  baby_supplies: 'مستلزمات أطفال',
  hygiene: 'نظافة',
  financial: 'مساعدة مالية',
  other: 'أخرى',
};

export const CATEGORY_ICONS: Record<RequestCategory, string> = {
  food: '🍞',
  water: '💧',
  shelter: '🏠',
  medicine: '💊',
  clothes: '👕',
  blankets: '🛏️',
  baby_supplies: '🍼',
  hygiene: '🧴',
  financial: '💰',
  other: '📦',
};

export const REQUEST_STATUS_LABELS: Record<RequestStatus, string> = {
  new: 'جديد',
  assigned: 'متكفل به',
  in_progress: 'قيد التنفيذ',
  completed: 'مكتمل',
  cancelled: 'ملغي',
};

export const REQUEST_STATUS_COLORS: Record<RequestStatus, string> = {
  new: 'bg-blue-100 text-blue-800',
  assigned: 'bg-yellow-100 text-yellow-800',
  in_progress: 'bg-orange-100 text-orange-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
};

export const ASSIGNMENT_STATUS_LABELS: Record<AssignmentStatus, string> = {
  pledged: 'تعهد',
  in_progress: 'قيد التنفيذ',
  completed: 'مكتمل',
  failed: 'فشل',
};

export const ASSIGNMENT_STATUS_COLORS: Record<AssignmentStatus, string> = {
  pledged: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-orange-100 text-orange-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

export const ALL_CATEGORIES: RequestCategory[] = [
  'food',
  'water',
  'shelter',
  'medicine',
  'clothes',
  'blankets',
  'baby_supplies',
  'hygiene',
  'financial',
  'other',
];

export const ALL_REQUEST_STATUSES: RequestStatus[] = [
  'new',
  'assigned',
  'in_progress',
  'completed',
  'cancelled',
];

export const ALL_ASSIGNMENT_STATUSES: AssignmentStatus[] = [
  'pledged',
  'in_progress',
  'completed',
  'failed',
];
