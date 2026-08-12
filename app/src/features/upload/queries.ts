import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from '@/lib/api';

export type UploadStatus = 'none' | 'pending' | 'approved' | 'rejected';

export function useUploadStatus(userId?: number) {
  return useQuery({
    queryKey: ['upload-status', userId],
    queryFn: () => api.get<{ status: string; username: string }>('/upload/status'),
    enabled: userId != null,
  });
}

export function useApplyUpload() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<{ status: string; username: string }>('/upload/apply'),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['upload-status'] });
    },
  });
}
