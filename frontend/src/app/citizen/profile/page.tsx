'use client';

import React, { useState, useEffect } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import Spinner from '@/components/ui/Spinner';
import { authApi, ApiError } from '@/lib/api';
import type { UserProfileResponse } from '@/lib/types';

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const [form, setForm] = useState({
    full_name: '',
    phone: '',
    address: '',
    city: '',
    region: '',
  });

  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState('');
  const [passwordError, setPasswordError] = useState('');

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const data = await authApi.getMe();
      setProfile(data);
      setForm({
        full_name: data.full_name || '',
        phone: data.phone || '',
        address: data.address || '',
        city: data.city || '',
        region: data.region || '',
      });
    } catch {
      setError('خطأ في تحميل البيانات');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage('');
    setError('');
    setSaving(true);

    try {
      await authApi.updateProfile({
        full_name: form.full_name || undefined,
        phone: form.phone || undefined,
        address: form.address || undefined,
        city: form.city || undefined,
        region: form.region || undefined,
      });
      setMessage('تم تحديث الملف الشخصي بنجاح');
    } catch (err) {
      if (err instanceof ApiError) setError(err.detail);
      else setError('خطأ في حفظ البيانات');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMessage('');
    setPasswordError('');

    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPasswordError('كلمتا المرور غير متطابقتين');
      return;
    }

    setPasswordSaving(true);

    try {
      await authApi.changePassword({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      });
      setPasswordMessage('تم تغيير كلمة المرور بنجاح');
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      if (err instanceof ApiError) setPasswordError(err.detail);
      else setPasswordError('خطأ في تغيير كلمة المرور');
    } finally {
      setPasswordSaving(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center py-12"><Spinner /></div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">الملف الشخصي</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Profile form */}
        <Card>
          <h2 className="text-lg font-semibold mb-4">البيانات الشخصية</h2>
          <form onSubmit={handleSaveProfile} className="space-y-4">
            {message && (
              <div className="bg-green-50 border border-green-200 text-green-700 text-sm p-3 rounded-lg">
                {message}
              </div>
            )}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg">
                {error}
              </div>
            )}

            <Input
              label="البريد الإلكتروني"
              value={profile?.email || ''}
              disabled
              dir="ltr"
            />
            <Input
              label="الاسم الكامل"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            />
            <Input
              label="رقم الهاتف"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              dir="ltr"
            />
            <Input
              label="العنوان"
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
            />
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="المدينة"
                value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
              />
              <Input
                label="المنطقة"
                value={form.region}
                onChange={(e) => setForm({ ...form, region: e.target.value })}
              />
            </div>
            <Button type="submit" loading={saving}>حفظ التغييرات</Button>
          </form>
        </Card>

        {/* Password form */}
        <Card>
          <h2 className="text-lg font-semibold mb-4">تغيير كلمة المرور</h2>
          <form onSubmit={handleChangePassword} className="space-y-4">
            {passwordMessage && (
              <div className="bg-green-50 border border-green-200 text-green-700 text-sm p-3 rounded-lg">
                {passwordMessage}
              </div>
            )}
            {passwordError && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg">
                {passwordError}
              </div>
            )}

            <Input
              label="كلمة المرور الحالية"
              type="password"
              value={passwordForm.current_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
              required
              dir="ltr"
            />
            <Input
              label="كلمة المرور الجديدة"
              type="password"
              value={passwordForm.new_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
              required
              minLength={6}
              dir="ltr"
            />
            <Input
              label="تأكيد كلمة المرور الجديدة"
              type="password"
              value={passwordForm.confirm_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
              required
              dir="ltr"
            />
            <Button type="submit" loading={passwordSaving}>تغيير كلمة المرور</Button>
          </form>
        </Card>
      </div>
    </DashboardLayout>
  );
}
