'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import DashboardLayout from '@/components/DashboardLayout';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import Spinner from '@/components/ui/Spinner';
import { citizenApi, ApiError } from '@/lib/api';
import { REQUEST_STATUS_LABELS, REQUEST_STATUS_COLORS, CATEGORY_LABELS, CATEGORY_ICONS } from '@/lib/constants';
import { formatDateTime } from '@/lib/utils';
import type { CitizenRequestResponse, RequestStatus, RequestCategory } from '@/lib/types';

export default function RequestDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [request, setRequest] = useState<CitizenRequestResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadRequest();
  }, [params.id]);

  const loadRequest = async () => {
    try {
      const data = await citizenApi.getRequest(params.id as string);
      setRequest(data);
    } catch (err) {
      if (err instanceof ApiError) setError(err.detail);
      else setError('خطأ في تحميل البيانات');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm('هل أنت متأكد من إلغاء هذا الطلب؟')) return;
    try {
      await citizenApi.cancelRequest(params.id as string);
      router.push('/citizen');
    } catch (err) {
      if (err instanceof ApiError) alert(err.detail);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center py-12"><Spinner /></div>
      </DashboardLayout>
    );
  }

  if (error || !request) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-red-600">{error || 'الطلب غير موجود'}</p>
          <Button variant="secondary" className="mt-4" onClick={() => router.push('/citizen')}>
            العودة
          </Button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <button onClick={() => router.push('/citizen')} className="text-sm text-primary-600 hover:text-primary-700 mb-2 block">
            &larr; العودة للطلبات
          </button>
          <h1 className="text-2xl font-bold text-gray-900">تفاصيل الطلب</h1>
        </div>
        {request.status === 'new' && (
          <Button variant="danger" onClick={handleCancel}>
            إلغاء الطلب
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h2 className="text-lg font-semibold mb-4">معلومات الطلب</h2>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-gray-500">الحالة</span>
              <Badge className={REQUEST_STATUS_COLORS[request.status]}>
                {request.status_ar}
              </Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">التصنيف</span>
              <span>
                {CATEGORY_ICONS[request.category as RequestCategory]}{' '}
                {CATEGORY_LABELS[request.category as RequestCategory]}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">مستعجل</span>
              <span>{request.is_urgent ? 'نعم' : 'لا'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">الكمية</span>
              <span>{request.quantity}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">أفراد الأسرة</span>
              <span>{request.family_members}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">رمز المتابعة</span>
              <span className="font-mono font-bold text-primary-600">{request.tracking_code}</span>
            </div>
          </div>
        </Card>

        <Card>
          <h2 className="text-lg font-semibold mb-4">الموقع والتواصل</h2>
          <div className="space-y-4">
            <div>
              <span className="text-gray-500 text-sm">العنوان</span>
              <p className="mt-1">{request.address}</p>
            </div>
            {request.city && (
              <div className="flex justify-between">
                <span className="text-gray-500">المدينة</span>
                <span>{request.city}</span>
              </div>
            )}
            {request.region && (
              <div className="flex justify-between">
                <span className="text-gray-500">المنطقة</span>
                <span>{request.region}</span>
              </div>
            )}
            {request.organization_name && (
              <div className="flex justify-between">
                <span className="text-gray-500">المؤسسة المتكفلة</span>
                <span className="font-medium text-green-700">{request.organization_name}</span>
              </div>
            )}
          </div>
        </Card>

        <Card className="lg:col-span-2">
          <h2 className="text-lg font-semibold mb-3">الوصف</h2>
          <p className="text-gray-700 whitespace-pre-wrap">{request.description}</p>
        </Card>

        <Card className="lg:col-span-2">
          <h2 className="text-lg font-semibold mb-3">التواريخ</h2>
          <div className="flex flex-wrap gap-6 text-sm">
            <div>
              <span className="text-gray-500">تاريخ الإنشاء:</span>{' '}
              <span>{formatDateTime(request.created_at)}</span>
            </div>
            {request.updated_at && (
              <div>
                <span className="text-gray-500">آخر تحديث:</span>{' '}
                <span>{formatDateTime(request.updated_at)}</span>
              </div>
            )}
            {request.completed_at && (
              <div>
                <span className="text-gray-500">تاريخ الإكمال:</span>{' '}
                <span>{formatDateTime(request.completed_at)}</span>
              </div>
            )}
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
}
