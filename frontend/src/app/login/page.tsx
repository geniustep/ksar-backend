'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import { ApiError } from '@/lib/api';

export default function LoginPage() {
  const { login, user } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login({ email, password });
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

  // Redirect after login
  React.useEffect(() => {
    if (user) {
      switch (user.role) {
        case 'admin':
          router.push('/admin');
          break;
        case 'organization':
          router.push('/org/requests');
          break;
        case 'citizen':
          router.push('/citizen');
          break;
      }
    }
  }, [user, router]);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center py-12 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="text-3xl font-bold text-primary-600">
            KSAR
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-4">تسجيل الدخول</h1>
          <p className="text-gray-600 mt-2">أدخل بياناتك للوصول إلى حسابك</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg">
                {error}
              </div>
            )}

            <Input
              label="البريد الإلكتروني"
              type="email"
              placeholder="example@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              dir="ltr"
            />

            <Input
              label="كلمة المرور"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              dir="ltr"
            />

            <Button type="submit" className="w-full" loading={loading}>
              دخول
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-600">
            ليس لديك حساب؟{' '}
            <Link href="/register" className="text-primary-600 hover:text-primary-700 font-medium">
              سجّل الآن
            </Link>
          </p>
        </div>

        {/* Demo accounts */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm">
          <p className="font-medium text-blue-800 mb-2">حسابات تجريبية:</p>
          <div className="space-y-1 text-blue-700">
            <p>المدير: admin@ksar.ma / admin123</p>
            <p>المؤسسة: org@ksar.ma / org123</p>
            <p>المواطن: citizen@example.ma / citizen123</p>
          </div>
        </div>
      </div>
    </div>
  );
}
