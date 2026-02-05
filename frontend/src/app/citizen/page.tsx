'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import StatsCard from '@/components/ui/StatsCard';
import Spinner from '@/components/ui/Spinner';
import { citizenApi, ApiError } from '@/lib/api';
import { REQUEST_STATUS_LABELS, REQUEST_STATUS_COLORS, CATEGORY_LABELS } from '@/lib/constants';
import { formatRelativeTime } from '@/lib/utils';
import type { CitizenRequestResponse, CitizenStats, RequestStatus, RequestCategory } from '@/lib/types';

export default function CitizenDashboard() {
  const [requests, setRequests] = useState<CitizenRequestResponse[]>([]);
  const [stats, setStats] = useState<CitizenStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<RequestStatus | ''>('');

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [reqData, statsData] = await Promise.all([
        citizenApi.getMyRequests(statusFilter || undefined),
        citizenApi.getStats(),
      ]);
      setRequests(reqData);
      setStats(statsData);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (requestId: string) => {
    if (!confirm('هل أنت متأكد من إلغاء هذا الطلب؟')) return;
    try {
      await citizenApi.cancelRequest(requestId);
      loadData();
    } catch (err) {
      if (err instanceof ApiError) alert(err.detail);
    }
  };

  return (
    <DashboardLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">طلباتي</h1>
        <p className="text-gray-500 mt-1">إدارة ومتابعة طلبات المساعدة الخاصة بك</p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatsCard
            title="إجمالي الطلبات"
            value={stats.total_requests}
            color="text-primary-600"
          />
          <StatsCard
            title="جديد"
            value={stats.by_status?.new || 0}
            color="text-blue-600"
          />
          <StatsCard
            title="قيد التنفيذ"
            value={(stats.by_status?.assigned || 0) + (stats.by_status?.in_progress || 0)}
            color="text-orange-600"
          />
          <StatsCard
            title="مكتمل"
            value={stats.by_status?.completed || 0}
            color="text-green-600"
          />
        </div>
      )}

      {/* Filter + Action */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-6">
        <div className="flex items-center gap-2 flex-wrap">
          {(['' , 'new', 'assigned', 'in_progress', 'completed', 'cancelled'] as (RequestStatus | '')[]).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                statusFilter === s
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {s === '' ? 'الكل' : REQUEST_STATUS_LABELS[s]}
            </button>
          ))}
        </div>
        <Link href="/citizen/new-request">
          <Button>+ طلب جديد</Button>
        </Link>
      </div>

      {/* Requests list */}
      {loading ? (
        <div className="flex justify-center py-12">
          <Spinner />
        </div>
      ) : requests.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
          <p className="text-gray-500 text-lg mb-4">لا توجد طلبات</p>
          <Link href="/citizen/new-request">
            <Button>تقديم طلب جديد</Button>
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {requests.map((req) => (
            <div
              key={req.id}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-sm transition-shadow"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge className={REQUEST_STATUS_COLORS[req.status]}>
                      {req.status_ar}
                    </Badge>
                    {req.is_urgent && (
                      <Badge className="bg-red-100 text-red-800">مستعجل</Badge>
                    )}
                    <span className="text-sm text-gray-400">
                      {CATEGORY_LABELS[req.category as RequestCategory]}
                    </span>
                  </div>
                  <p className="text-gray-800 text-sm line-clamp-1">{req.description}</p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                    <span>رمز المتابعة: {req.tracking_code}</span>
                    <span>{formatRelativeTime(req.created_at)}</span>
                    {req.organization_name && (
                      <span className="text-green-600">المؤسسة: {req.organization_name}</span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Link href={`/citizen/requests/${req.id}`}>
                    <Button variant="ghost" size="sm">
                      التفاصيل
                    </Button>
                  </Link>
                  {req.status === 'new' && (
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleCancel(req.id)}
                    >
                      إلغاء
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}
