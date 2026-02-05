'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Spinner from '@/components/ui/Spinner';
import { adminApi, ApiError } from '@/lib/api';
import {
  CATEGORY_LABELS,
  CATEGORY_ICONS,
  REQUEST_STATUS_LABELS,
  REQUEST_STATUS_COLORS,
  ALL_CATEGORIES,
  ALL_REQUEST_STATUSES,
} from '@/lib/constants';
import { formatRelativeTime } from '@/lib/utils';
import type { RequestResponse, RequestStatus, RequestCategory } from '@/lib/types';

export default function AdminRequestsPage() {
  const [requests, setRequests] = useState<RequestResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  const [filters, setFilters] = useState({
    status: '',
    category: '',
    search: '',
    is_urgent: '',
  });

  useEffect(() => {
    loadData();
  }, [page, filters]);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await adminApi.getRequests({
        status: (filters.status as RequestStatus) || undefined,
        category: (filters.category as RequestCategory) || undefined,
        search: filters.search || undefined,
        is_urgent: filters.is_urgent === 'true' ? true : filters.is_urgent === 'false' ? false : undefined,
        page,
        limit: 20,
      });
      setRequests(data.items);
      setTotal(data.total);
      setHasMore(data.has_more);
    } catch (err) {
      console.error('Failed to load requests:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('هل أنت متأكد من حذف هذا الطلب؟')) return;
    try {
      await adminApi.deleteRequest(id);
      loadData();
    } catch (err) {
      if (err instanceof ApiError) alert(err.detail);
    }
  };

  const statusOptions = [
    { value: '', label: 'جميع الحالات' },
    ...ALL_REQUEST_STATUSES.map((s) => ({ value: s, label: REQUEST_STATUS_LABELS[s] })),
  ];

  const categoryOptions = [
    { value: '', label: 'جميع التصنيفات' },
    ...ALL_CATEGORIES.map((c) => ({ value: c, label: CATEGORY_LABELS[c] })),
  ];

  const urgentOptions = [
    { value: '', label: 'الكل' },
    { value: 'true', label: 'مستعجل فقط' },
    { value: 'false', label: 'عادي فقط' },
  ];

  return (
    <DashboardLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">إدارة الطلبات</h1>
        <p className="text-gray-500 mt-1">عرض وإدارة جميع طلبات المساعدة</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <Input
            placeholder="بحث بالاسم أو الهاتف..."
            value={filters.search}
            onChange={(e) => { setFilters({ ...filters, search: e.target.value }); setPage(1); }}
          />
          <Select
            options={statusOptions}
            value={filters.status}
            onChange={(e) => { setFilters({ ...filters, status: e.target.value }); setPage(1); }}
          />
          <Select
            options={categoryOptions}
            value={filters.category}
            onChange={(e) => { setFilters({ ...filters, category: e.target.value }); setPage(1); }}
          />
          <Select
            options={urgentOptions}
            value={filters.is_urgent}
            onChange={(e) => { setFilters({ ...filters, is_urgent: e.target.value }); setPage(1); }}
          />
          <Button
            variant="secondary"
            onClick={() => {
              setFilters({ status: '', category: '', search: '', is_urgent: '' });
              setPage(1);
            }}
          >
            مسح الفلاتر
          </Button>
        </div>
      </div>

      {/* Total */}
      <p className="text-sm text-gray-500 mb-4">{total} طلب</p>

      {/* Requests table */}
      {loading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : requests.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
          <p className="text-gray-500 text-lg">لا توجد طلبات مطابقة</p>
        </div>
      ) : (
        <>
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-gray-500 border-b">
                    <th className="text-right px-4 py-3">الاسم</th>
                    <th className="text-right px-4 py-3">التصنيف</th>
                    <th className="text-center px-4 py-3">الحالة</th>
                    <th className="text-center px-4 py-3">الأولوية</th>
                    <th className="text-right px-4 py-3">المنطقة</th>
                    <th className="text-right px-4 py-3">التاريخ</th>
                    <th className="text-center px-4 py-3">إجراءات</th>
                  </tr>
                </thead>
                <tbody>
                  {requests.map((req) => (
                    <tr key={req.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <div>
                          <span className="font-medium">{req.requester_name}</span>
                          <p className="text-xs text-gray-400" dir="ltr">{req.requester_phone}</p>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span>
                          {CATEGORY_ICONS[req.category]} {CATEGORY_LABELS[req.category]}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <Badge className={REQUEST_STATUS_COLORS[req.status]}>
                          {REQUEST_STATUS_LABELS[req.status]}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`font-medium ${req.is_urgent ? 'text-red-600' : ''}`}>
                          {req.priority_score}
                          {req.is_urgent === 1 && ' !'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {req.region || req.city || '-'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-400">
                        {formatRelativeTime(req.created_at)}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <div className="flex items-center justify-center gap-1">
                          <Link href={`/admin/requests/${req.id}`}>
                            <Button variant="ghost" size="sm">تفاصيل</Button>
                          </Link>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-600 hover:bg-red-50"
                            onClick={() => handleDelete(req.id)}
                          >
                            حذف
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between mt-6">
            <Button variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>
              السابق
            </Button>
            <span className="text-sm text-gray-500">صفحة {page}</span>
            <Button variant="secondary" disabled={!hasMore} onClick={() => setPage(page + 1)}>
              التالي
            </Button>
          </div>
        </>
      )}
    </DashboardLayout>
  );
}
