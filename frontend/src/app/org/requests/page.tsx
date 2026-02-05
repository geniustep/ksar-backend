'use client';

import React, { useEffect, useState } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Select from '@/components/ui/Select';
import StatsCard from '@/components/ui/StatsCard';
import Spinner from '@/components/ui/Spinner';
import Modal from '@/components/ui/Modal';
import Textarea from '@/components/ui/Textarea';
import { orgApi, ApiError } from '@/lib/api';
import { CATEGORY_LABELS, CATEGORY_ICONS, ALL_CATEGORIES } from '@/lib/constants';
import { formatRelativeTime } from '@/lib/utils';
import type { RequestResponse, OrgStats, RequestCategory } from '@/lib/types';

export default function OrgRequestsPage() {
  const [requests, setRequests] = useState<RequestResponse[]>([]);
  const [stats, setStats] = useState<OrgStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  // Pledge modal
  const [pledgeModal, setPledgeModal] = useState<string | null>(null);
  const [pledgeNotes, setPledgeNotes] = useState('');
  const [pledging, setPledging] = useState(false);

  useEffect(() => {
    loadData();
  }, [categoryFilter, page]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [reqData, statsData] = await Promise.all([
        orgApi.getAvailableRequests({
          category: categoryFilter as RequestCategory || undefined,
          page,
          limit: 20,
        }),
        orgApi.getStats(),
      ]);
      setRequests(reqData.items);
      setTotal(reqData.total);
      setHasMore(reqData.has_more);
      setStats(statsData);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePledge = async () => {
    if (!pledgeModal) return;
    setPledging(true);
    try {
      await orgApi.createAssignment({
        request_id: pledgeModal,
        notes: pledgeNotes || undefined,
      });
      setPledgeModal(null);
      setPledgeNotes('');
      loadData();
    } catch (err) {
      if (err instanceof ApiError) alert(err.detail);
    } finally {
      setPledging(false);
    }
  };

  const categoryOptions = [
    { value: '', label: 'جميع التصنيفات' },
    ...ALL_CATEGORIES.map((c) => ({ value: c, label: CATEGORY_LABELS[c] })),
  ];

  return (
    <DashboardLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">الطلبات المتاحة</h1>
        <p className="text-gray-500 mt-1">طلبات المساعدة المتاحة للتكفل بها</p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatsCard title="إجمالي التكفلات" value={stats.data.total_assignments} />
          <StatsCard title="مكتمل" value={stats.data.total_completed} color="text-green-600" />
          <StatsCard title="قيد التنفيذ" value={stats.data.by_status?.in_progress || 0} color="text-orange-600" />
          <StatsCard title="الطلبات المتاحة" value={total} color="text-blue-600" />
        </div>
      )}

      {/* Filter */}
      <div className="mb-6 flex items-center gap-3">
        <Select
          options={categoryOptions}
          value={categoryFilter}
          onChange={(e) => { setCategoryFilter(e.target.value); setPage(1); }}
          className="max-w-xs"
        />
      </div>

      {/* Requests */}
      {loading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : requests.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
          <p className="text-gray-500 text-lg">لا توجد طلبات متاحة حالياً</p>
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {requests.map((req) => (
              <div
                key={req.id}
                className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-sm transition-shadow"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">{CATEGORY_ICONS[req.category]}</span>
                      <span className="font-medium">{CATEGORY_LABELS[req.category]}</span>
                      {req.is_urgent === 1 && (
                        <Badge className="bg-red-100 text-red-800">مستعجل</Badge>
                      )}
                      <Badge className="bg-purple-100 text-purple-800">
                        أولوية: {req.priority_score}
                      </Badge>
                    </div>
                    <p className="text-gray-700 text-sm line-clamp-2 mb-2">{req.description}</p>
                    <div className="flex items-center gap-4 text-xs text-gray-400">
                      <span>{req.requester_name}</span>
                      {req.city && <span>{req.city}</span>}
                      {req.region && <span>{req.region}</span>}
                      <span>أفراد الأسرة: {req.family_members}</span>
                      <span>{formatRelativeTime(req.created_at)}</span>
                    </div>
                  </div>

                  <Button onClick={() => setPledgeModal(req.id)}>
                    تكفل بالطلب
                  </Button>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between mt-6">
            <Button
              variant="secondary"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
            >
              السابق
            </Button>
            <span className="text-sm text-gray-500">
              صفحة {page} - {total} طلب
            </span>
            <Button
              variant="secondary"
              disabled={!hasMore}
              onClick={() => setPage(page + 1)}
            >
              التالي
            </Button>
          </div>
        </>
      )}

      {/* Pledge Modal */}
      <Modal
        isOpen={!!pledgeModal}
        onClose={() => { setPledgeModal(null); setPledgeNotes(''); }}
        title="التكفل بالطلب"
      >
        <div className="space-y-4">
          <p className="text-gray-600 text-sm">
            هل أنت متأكد من رغبتك في التكفل بهذا الطلب؟ سيتم تعيينه لمؤسستك.
          </p>
          <Textarea
            label="ملاحظات (اختياري)"
            placeholder="أضف ملاحظات..."
            value={pledgeNotes}
            onChange={(e) => setPledgeNotes(e.target.value)}
          />
          <div className="flex gap-3">
            <Button onClick={handlePledge} loading={pledging} className="flex-1">
              تأكيد التكفل
            </Button>
            <Button variant="secondary" onClick={() => setPledgeModal(null)}>
              إلغاء
            </Button>
          </div>
        </div>
      </Modal>
    </DashboardLayout>
  );
}
