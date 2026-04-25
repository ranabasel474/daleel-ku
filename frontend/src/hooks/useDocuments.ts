import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { transformDocument } from '@/lib/transformers';
import type { ApiDocument, Document } from '@/lib/types';

export function useDocuments() {
  return useQuery<Document[]>({
    queryKey: ['documents'],
    queryFn: async () => {
      const res = await api.get<{ documents: ApiDocument[] }>('/api/admin/documents');
      return res.documents.map(transformDocument);
    },
  });
}

export function useCreateDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { title: string; source_url: string; document_type: string }) =>
      api.post<{ document: ApiDocument }>('/api/admin/documents', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  });
}

export function useUpdateDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { title?: string; source_url?: string; document_type?: string } }) =>
      api.put<{ document: ApiDocument }>(`/api/admin/documents/${id}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  });
}

export function useUploadDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ file, title }: { file: File; title: string }) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title);

      const token = localStorage.getItem('access_token');
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
      const res = await fetch(`${baseUrl}/api/admin/documents/upload`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });

      const body = await res.json();
      if (!res.ok) throw new Error(body.error || 'Upload failed');
      return body as { document: ApiDocument; chunks_created: number };
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  });
}

export function useColleges() {
  return useQuery<{ college_id: string; college_name: string }[]>({
    queryKey: ['colleges'],
    queryFn: async () => {
      const res = await api.get<{ colleges: { college_id: string; college_name: string }[] }>('/api/admin/colleges');
      return res.colleges;
    },
  });
}

export function useTopics() {
  return useQuery<{ topic_id: string; topic_name: string }[]>({
    queryKey: ['topics'],
    queryFn: async () => {
      const res = await api.get<{ topics: { topic_id: string; topic_name: string }[] }>('/api/admin/topics');
      return res.topics;
    },
  });
}

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.del<{ message: string }>(`/api/admin/documents/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  });
}
