'use client';

import React, { useEffect, useState } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Select from '@/components/ui/Select';
import Spinner from '@/components/ui/Spinner';
import { adminApi, ApiError } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import type { AdminOrgListItem } from '@/lib/types';

export default function AdminOrganizationsPage() {
  const [orgs, setOrgs] = useState<AdminOrgListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    loadData();
  }, [page, statusFilter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await adminApi.getOrganizations({
        status: statusFilter || undefined,
        page,
        limit: 20,
      });
      setOrgs(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to load orgs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (orgId: string, newStatus: string) => {
    try {
      await adminApi.updateOrgStatus(orgId, newStatus);
      loadData();
    } catch (err) {
      if (err instanceof ApiError) alert(err.detail);
    }
  };

  return (
    <DashboardLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">إدارة المؤسسات</h1>
        <p className="text-gray-500 mt-1">عرض وإدارة المؤسسات المسجلة</p>
      </div>

      {/* Filter */}
      <div className="mb-6 flex items-center gap-3">
        <Select
          options={[
            { value: '', label: 'جميع الحالات' },
            { value: 'active', label: 'نشط' },
            { value: 'suspended', label: 'معلق' },
          ]}
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="max-w-xs"
        />
        <span className="text-sm text-gray-500">{total} مؤسسة</span>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : orgs.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
          <p className="text-gray-500 text-lg">لا توجد مؤسسات</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-gray-500 border-b">
                  <th className="text-right px-4 py-3">المؤسسة</th>
                  <th className="text-right px-4 py-3">البريد</th>
                  <th className="text-right px-4 py-3">الهاتف</th>
                  <th className="text-center px-4 py-3">الحالة</th>
                  <th className="text-center px-4 py-3">المنجز</th>
                  <th className="text-right px-4 py-3">التسجيل</th>
                  <th className="text-center px-4 py-3">إجراءات</th>
                </tr>
              </thead>
              <tbody>
                {orgs.map((org) => (
                  <tr key={org.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{org.name}</td>
                    <td className="px-4 py-3 text-gray-500" dir="ltr">{org.contact_email}</td>
                    <td className="px-4 py-3 text-gray-500" dir="ltr">{org.contact_phone}</td>
                    <td className="px-4 py-3 text-center">
                      <Badge className={org.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                        {org.status === 'active' ? 'نشط' : 'معلق'}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-center font-medium text-green-600">
                      {org.total_completed}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-400">
                      {formatDate(org.created_at)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {org.status === 'active' ? (
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={() => handleStatusChange(org.id, 'suspended')}
                        >
                          تعليق
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          onClick={() => handleStatusChange(org.id, 'active')}
                        >
                          تفعيل
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pagination */}
      {total > 20 && (
        <div className="flex items-center justify-between mt-6">
          <Button variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            السابق
          </Button>
          <span className="text-sm text-gray-500">صفحة {page}</span>
          <Button variant="secondary" disabled={orgs.length < 20} onClick={() => setPage(page + 1)}>
            التالي
          </Button>
        </div>
      )}
    </DashboardLayout>
  );
}
