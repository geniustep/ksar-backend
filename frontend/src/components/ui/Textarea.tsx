'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export default function Textarea({
  label,
  error,
  className,
  id,
  ...props
}: TextareaProps) {
  const textareaId = id || label?.replace(/\s+/g, '-').toLowerCase();

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={textareaId}
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          {label}
        </label>
      )}
      <textarea
        id={textareaId}
        className={cn(
          'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm',
          'focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none',
          'placeholder:text-gray-400',
          error && 'border-red-500 focus:border-red-500 focus:ring-red-500',
          className
        )}
        rows={4}
        {...props}
      />
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
}
