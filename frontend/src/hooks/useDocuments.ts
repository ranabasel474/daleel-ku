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

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.del<{ message: string }>(`/api/admin/documents/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  });
}
