'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import DashboardLayout from '@/components/DashboardLayout';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Textarea from '@/components/ui/Textarea';
import Button from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { citizenApi, ApiError } from '@/lib/api';
import { ALL_CATEGORIES, CATEGORY_LABELS } from '@/lib/constants';
import type { RequestCategory } from '@/lib/types';

export default function NewRequestPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    category: '' as RequestCategory | '',
    description: '',
    quantity: '1',
    family_members: '1',
    address: '',
    city: '',
    region: '',
    is_urgent: false,
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<{ tracking_code: string; message: string } | null>(null);

  const categoryOptions = ALL_CATEGORIES.map((c) => ({
    value: c,
    label: CATEGORY_LABELS[c],
  }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.category) {
      setError('يرجى اختيار تصنيف الطلب');
      return;
    }
    setError('');
    setLoading(true);

    try {
      const result = await citizenApi.createRequest({
        category: form.category as RequestCategory,
        description: form.description,
        quantity: parseInt(form.quantity),
        family_members: parseInt(form.family_members),
        address: form.address || undefined,
        city: form.city || undefined,
        region: form.region || undefined,
        is_urgent: form.is_urgent,
      });
      setSuccess({
        tracking_code: result.tracking_code,
        message: result.message,
      });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError('خطأ في الاتصال بالخادم');
      }
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <DashboardLayout>
        <div className="max-w-lg mx-auto py-12">
          <Card className="text-center">
            <div className="text-5xl mb-4">&#10003;</div>
            <h2 className="text-2xl font-bold text-green-700 mb-2">تم إرسال الطلب بنجاح!</h2>
            <p className="text-gray-600 mb-4">{success.message}</p>
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <p className="text-sm text-gray-500">رمز المتابعة</p>
              <p className="text-2xl font-mono font-bold text-primary-600 mt-1">
                {success.tracking_code}
              </p>
              <p className="text-xs text-gray-400 mt-1">احتفظ بهذا الرمز لمتابعة طلبك</p>
            </div>
            <div className="flex gap-3 justify-center">
              <Button onClick={() => router.push('/citizen')}>العودة لطلباتي</Button>
              <Button
                variant="secondary"
                onClick={() => {
                  setSuccess(null);
                  setForm({
                    category: '',
                    description: '',
                    quantity: '1',
                    family_members: '1',
                    address: '',
                    city: '',
                    region: '',
                    is_urgent: false,
                  });
                }}
              >
                طلب جديد
              </Button>
            </div>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <button
            onClick={() => router.push('/citizen')}
            className="text-sm text-primary-600 hover:text-primary-700 mb-2 block"
          >
            &larr; العودة
          </button>
          <h1 className="text-2xl font-bold text-gray-900">طلب مساعدة جديد</h1>
          <p className="text-gray-500 mt-1">أملأ البيانات التالية لتقديم طلب مساعدة</p>
        </div>

        <Card>
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg">
                {error}
              </div>
            )}

            <Select
              label="نوع المساعدة"
              options={categoryOptions}
              placeholder="اختر نوع المساعدة"
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value as RequestCategory })}
              required
            />

            <Textarea
              label="وصف الاحتياج"
              placeholder="صف احتياجك بالتفصيل (10 أحرف على الأقل)"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              required
              minLength={10}
            />

            <div className="grid grid-cols-2 gap-4">
              <Input
                label="الكمية المطلوبة"
                type="number"
                min="1"
                max="100"
                value={form.quantity}
                onChange={(e) => setForm({ ...form, quantity: e.target.value })}
              />
              <Input
                label="عدد أفراد الأسرة"
                type="number"
                min="1"
                max="50"
                value={form.family_members}
                onChange={(e) => setForm({ ...form, family_members: e.target.value })}
              />
            </div>

            <Input
              label="العنوان (اختياري - يُستخدم عنوان حسابك إن لم يُحدد)"
              placeholder="العنوان التفصيلي"
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
            />

            <div className="grid grid-cols-2 gap-4">
              <Input
                label="المدينة"
                placeholder="المدينة"
                value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
              />
              <Input
                label="المنطقة/الحي"
                placeholder="المنطقة"
                value={form.region}
                onChange={(e) => setForm({ ...form, region: e.target.value })}
              />
            </div>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={form.is_urgent}
                onChange={(e) => setForm({ ...form, is_urgent: e.target.checked })}
                className="w-4 h-4 text-red-600 rounded border-gray-300 focus:ring-red-500"
              />
              <span className="text-sm font-medium text-red-700">
                طلب مستعجل (يرفع أولوية الطلب)
              </span>
            </label>

            <div className="flex gap-3 pt-2">
              <Button type="submit" className="flex-1" loading={loading}>
                إرسال الطلب
              </Button>
              <Button type="button" variant="secondary" onClick={() => router.push('/citizen')}>
                إلغاء
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </DashboardLayout>
  );
}
