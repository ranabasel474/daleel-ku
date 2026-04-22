import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { transformQuery, groupQueriesBySessions } from '@/lib/transformers';
import type { ApiQuery, QueryEntry, Session } from '@/lib/types';

interface AdminQueriesResult {
  sessions: Session[];
  allQueries: QueryEntry[];
}

export function useAdminQueries() {
  return useQuery<AdminQueriesResult>({
    queryKey: ['admin-queries'],
    queryFn: async () => {
      const res = await api.get<{ queries: ApiQuery[] }>('/api/admin/queries');
      const allQueries = res.queries.map(transformQuery);
      const sessions = groupQueriesBySessions(allQueries);
      return { sessions, allQueries };
    },
  });
}
