'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import DashboardLayout from '@/components/DashboardLayout';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Textarea from '@/components/ui/Textarea';
import { Card } from '@/components/ui/Card';
import Spinner from '@/components/ui/Spinner';
import { orgApi, ApiError } from '@/lib/api';
import {
  ASSIGNMENT_STATUS_LABELS,
  ASSIGNMENT_STATUS_COLORS,
  CATEGORY_LABELS,
  CATEGORY_ICONS,
} from '@/lib/constants';
import { formatDateTime } from '@/lib/utils';
import type { AssignmentWithRequest, AssignmentStatus, RequestCategory } from '@/lib/types';

export default function AssignmentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [data, setData] = useState<AssignmentWithRequest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Update form
  const [updating, setUpdating] = useState(false);
  const [completionNotes, setCompletionNotes] = useState('');
  const [failureReason, setFailureReason] = useState('');

  useEffect(() => {
    loadData();
  }, [params.id]);

  const loadData = async () => {
    try {
      const result = await orgApi.getAssignment(params.id as string);
      setData(result);
    } catch (err) {
      if (err instanceof ApiError) setError(err.detail);
      else setError('خطأ في تحميل البيانات');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (status: AssignmentStatus) => {
    setUpdating(true);
    try {
      await orgApi.updateAssignment(params.id as string, {
        status,
        completion_notes: status === 'completed' ? completionNotes || undefined : undefined,
        failure_reason: status === 'failed' ? failureReason || undefined : undefined,
      });
      loadData();
    } catch (err) {
      if (err instanceof ApiError) alert(err.detail);
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center py-12"><Spinner /></div>
      </DashboardLayout>
    );
  }

  if (error || !data) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-red-600">{error || 'التكفل غير موجود'}</p>
          <Button variant="secondary" className="mt-4" onClick={() => router.push('/org/assignments')}>
            العودة
          </Button>
        </div>
      </DashboardLayout>
    );
  }

  const { assignment, request } = data;

  return (
    <DashboardLayout>
      <div className="mb-6">
        <button
          onClick={() => router.push('/org/assignments')}
          className="text-sm text-primary-600 hover:text-primary-700 mb-2 block"
        >
          &larr; العودة للتكفلات
        </button>
        <h1 className="text-2xl font-bold text-gray-900">تفاصيل التكفل</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Assignment info */}
        <Card>
          <h2 className="text-lg font-semibold mb-4">معلومات التكفل</h2>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-gray-500">الحالة</span>
              <Badge className={ASSIGNMENT_STATUS_COLORS[assignment.status]}>
                {ASSIGNMENT_STATUS_LABELS[assignment.status]}
              </Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">تاريخ التكفل</span>
              <span className="text-sm">{formatDateTime(assignment.created_at)}</span>
            </div>
            {assignment.completed_at && (
              <div className="flex justify-between">
                <span className="text-gray-500">تاريخ الإكمال</span>
                <span className="text-sm">{formatDateTime(assignment.completed_at)}</span>
              </div>
            )}
            {assignment.notes && (
              <div>
                <span className="text-gray-500 text-sm">ملاحظات</span>
                <p className="mt-1 text-gray-700">{assignment.notes}</p>
              </div>
            )}
            {assignment.completion_notes && (
              <div>
                <span className="text-gray-500 text-sm">ملاحظات الإكمال</span>
                <p className="mt-1 text-gray-700">{assignment.completion_notes}</p>
              </div>
            )}
            {assignment.failure_reason && (
              <div>
                <span className="text-gray-500 text-sm">سبب الفشل</span>
                <p className="mt-1 text-red-600">{assignment.failure_reason}</p>
              </div>
            )}
          </div>
        </Card>

        {/* Request info */}
        <Card>
          <h2 className="text-lg font-semibold mb-4">معلومات الطلب</h2>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-gray-500">التصنيف</span>
              <span>
                {CATEGORY_ICONS[request.category as RequestCategory]}{' '}
                {CATEGORY_LABELS[request.category as RequestCategory]}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">الاسم</span>
              <span>{request.requester_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">الهاتف</span>
              <span dir="ltr">{request.requester_phone}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">الكمية</span>
              <span>{request.quantity}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">أفراد الأسرة</span>
              <span>{request.family_members}</span>
            </div>
            <div>
              <span className="text-gray-500 text-sm">العنوان</span>
              <p className="mt-1">{request.address}</p>
              {request.city && <p className="text-sm text-gray-500">{request.city} - {request.region}</p>}
            </div>
            {request.is_urgent === 1 && (
              <Badge className="bg-red-100 text-red-800">طلب مستعجل</Badge>
            )}
          </div>
        </Card>

        {/* Description */}
        <Card className="lg:col-span-2">
          <h2 className="text-lg font-semibold mb-3">وصف الطلب</h2>
          <p className="text-gray-700 whitespace-pre-wrap">{request.description}</p>
        </Card>

        {/* Actions */}
        {assignment.status !== 'completed' && assignment.status !== 'failed' && (
          <Card className="lg:col-span-2">
            <h2 className="text-lg font-semibold mb-4">تحديث الحالة</h2>
            <div className="space-y-4">
              {assignment.status === 'pledged' && (
                <Button
                  onClick={() => handleStatusUpdate('in_progress')}
                  loading={updating}
                >
                  بدء التنفيذ
                </Button>
              )}

              {assignment.status === 'in_progress' && (
                <div className="space-y-4">
                  <Textarea
                    label="ملاحظات الإكمال"
                    placeholder="أضف ملاحظات عن عملية التسليم..."
                    value={completionNotes}
                    onChange={(e) => setCompletionNotes(e.target.value)}
                  />
                  <div className="flex gap-3">
                    <Button
                      onClick={() => handleStatusUpdate('completed')}
                      loading={updating}
                    >
                      تم التسليم بنجاح
                    </Button>
                    <div className="flex-1" />
                    <div>
                      <Textarea
                        label="سبب الفشل"
                        placeholder="أضف سبب الفشل..."
                        value={failureReason}
                        onChange={(e) => setFailureReason(e.target.value)}
                        className="mb-2"
                      />
                      <Button
                        variant="danger"
                        onClick={() => handleStatusUpdate('failed')}
                        loading={updating}
                      >
                        فشل التسليم
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
