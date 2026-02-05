'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import { ApiError } from '@/lib/api';

export default function RegisterPage() {
  const { register, user } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    phone: '',
    address: '',
    city: '',
    region: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (form.password !== form.confirmPassword) {
      setError('كلمتا المرور غير متطابقتين');
      return;
    }

    setLoading(true);

    try {
      await register({
        email: form.email,
        password: form.password,
        full_name: form.full_name,
        phone: form.phone,
        address: form.address || undefined,
        city: form.city || undefined,
        region: form.region || undefined,
      });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError('خطأ في الاتصال بالخادم');
      }
      setLoading(false);
      return;
    }

    setLoading(false);
  };

  useEffect(() => {
    if (user) {
      router.push('/citizen');
    }
  }, [user, router]);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center py-12 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="text-3xl font-bold text-primary-600">
            KSAR
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-4">إنشاء حساب جديد</h1>
          <p className="text-gray-600 mt-2">سجّل حسابك لتقديم طلبات المساعدة</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg">
                {error}
              </div>
            )}

            <Input
              label="الاسم الكامل"
              name="full_name"
              placeholder="أدخل اسمك الكامل"
              value={form.full_name}
              onChange={handleChange}
              required
            />

            <Input
              label="البريد الإلكتروني"
              name="email"
              type="email"
              placeholder="example@email.com"
              value={form.email}
              onChange={handleChange}
              required
              dir="ltr"
            />

            <Input
              label="رقم الهاتف"
              name="phone"
              type="tel"
              placeholder="+212600000000"
              value={form.phone}
              onChange={handleChange}
              required
              dir="ltr"
            />

            <Input
              label="كلمة المرور"
              name="password"
              type="password"
              placeholder="6 أحرف على الأقل"
              value={form.password}
              onChange={handleChange}
              required
              minLength={6}
              dir="ltr"
            />

            <Input
              label="تأكيد كلمة المرور"
              name="confirmPassword"
              type="password"
              placeholder="أعد إدخال كلمة المرور"
              value={form.confirmPassword}
              onChange={handleChange}
              required
              dir="ltr"
            />

            <Input
              label="العنوان (اختياري)"
              name="address"
              placeholder="العنوان التفصيلي"
              value={form.address}
              onChange={handleChange}
            />

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="المدينة"
                name="city"
                placeholder="المدينة"
                value={form.city}
                onChange={handleChange}
              />
              <Input
                label="المنطقة/الحي"
                name="region"
                placeholder="المنطقة"
                value={form.region}
                onChange={handleChange}
              />
            </div>

            <Button type="submit" className="w-full" loading={loading}>
              إنشاء حساب
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-600">
            لديك حساب بالفعل؟{' '}
            <Link href="/login" className="text-primary-600 hover:text-primary-700 font-medium">
              سجّل الدخول
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
