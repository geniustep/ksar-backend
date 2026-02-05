'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Spinner from '@/components/ui/Spinner';
import { orgApi } from '@/lib/api';
import {
  ASSIGNMENT_STATUS_LABELS,
  ASSIGNMENT_STATUS_COLORS,
  ALL_ASSIGNMENT_STATUSES,
} from '@/lib/constants';
import { formatRelativeTime } from '@/lib/utils';
import type { AssignmentResponse, AssignmentStatus } from '@/lib/types';

export default function OrgAssignmentsPage() {
  const [assignments, setAssignments] = useState<AssignmentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<AssignmentStatus | ''>('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  useEffect(() => {
    loadData();
  }, [statusFilter, page]);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await orgApi.getMyAssignments({
        status: statusFilter || undefined,
        page,
        limit: 20,
      });
      setAssignments(data.items);
      setTotal(data.total);
      setHasMore(data.has_more);
    } catch (err) {
      console.error('Failed to load assignments:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">تكفلاتي</h1>
        <p className="text-gray-500 mt-1">إدارة ومتابعة التكفلات الخاصة بمؤسستك</p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 mb-6 flex-wrap">
        {(['' as AssignmentStatus | '', ...ALL_ASSIGNMENT_STATUSES]).map((s) => (
          <button
            key={s}
            onClick={() => { setStatusFilter(s); setPage(1); }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              statusFilter === s
                ? 'bg-primary-600 text-white'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            {s === '' ? 'الكل' : ASSIGNMENT_STATUS_LABELS[s]}
          </button>
        ))}
      </div>

      {/* Assignments list */}
      {loading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : assignments.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
          <p className="text-gray-500 text-lg mb-4">لا توجد تكفلات</p>
          <Link href="/org/requests">
            <Button>عرض الطلبات المتاحة</Button>
          </Link>
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {assignments.map((a) => (
              <Link
                key={a.id}
                href={`/org/assignments/${a.id}`}
                className="block bg-white rounded-xl border border-gray-200 p-5 hover:shadow-sm transition-shadow"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <Badge className={ASSIGNMENT_STATUS_COLORS[a.status]}>
                      {ASSIGNMENT_STATUS_LABELS[a.status]}
                    </Badge>
                    <p className="text-sm text-gray-500 mt-2">
                      رقم التكفل: {a.id.slice(0, 8)}...
                    </p>
                    {a.notes && (
                      <p className="text-sm text-gray-600 mt-1 line-clamp-1">{a.notes}</p>
                    )}
                    <p className="text-xs text-gray-400 mt-1">
                      {formatRelativeTime(a.created_at)}
                    </p>
                  </div>
                  <span className="text-sm text-primary-600">التفاصيل &larr;</span>
                </div>
              </Link>
            ))}
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between mt-6">
            <Button variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>
              السابق
            </Button>
            <span className="text-sm text-gray-500">صفحة {page} - {total} تكفل</span>
            <Button variant="secondary" disabled={!hasMore} onClick={() => setPage(page + 1)}>
              التالي
            </Button>
          </div>
        </>
      )}
    </DashboardLayout>
  );
}
