import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from '@/lib/api';

export type UploadRequest = {
  id: number;
  username: string;
  email: string | null;
  nickname: string | null;
  uploader_status: string;
};

export function useUploadRequests() {
  return useQuery({
    queryKey: ['admin-upload-requests'],
    queryFn: () => api.get<UploadRequest[]>('/admin/upload-requests'),
  });
}

export function useReviewUpload() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, action }: { userId: number; action: 'approve' | 'reject' }) =>
      api.post(`/admin/upload-requests/${userId}/review`, { action }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-upload-requests'] });
      qc.invalidateQueries({ queryKey: ['upload-status'] });
    },
  });
}
