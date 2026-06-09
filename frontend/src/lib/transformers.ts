import type { ApiDocument, ApiQuery, Document, QueryEntry, Session } from './types';

const ARABIC_RE = /[\u0600-\u06FF]/;

export function transformDocument(api: ApiDocument): Document {
  return {
    id: api.document_id,
    title: api.title,
    type: api.document_type || '—',
    college: api.college_name || '—',
    topic: api.topic_name || '—',
    dateAdded: api.date_added ? api.date_added.split('T')[0] : '—',
    sourceUrl: api.source_url || '',
  };
}

export function transformQuery(api: ApiQuery): QueryEntry {
  const isArabic = ARABIC_RE.test(api.query_text);
  return {
    id: api.query_id,
    queryText: api.query_text,
    response: api.response_text || '',
    status: api.was_answered ? 'answered' : 'referral',
    time: new Date(api.created_at.endsWith('Z') ? api.created_at : api.created_at + 'Z')
      .toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
    language: isArabic ? 'ar' : 'en',
    direction: isArabic ? 'rtl' : 'ltr',
    sessionId: api.session_id || 'unknown',
    createdAt: api.created_at,
  };
}

export function groupQueriesBySessions(queries: QueryEntry[]): Session[] {
  const map = new Map<string, QueryEntry[]>();

  for (const q of queries) {
    const key = q.sessionId;
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(q);
  }

  const sessions: Session[] = [];

  for (const [sessionId, entries] of map) {
    // Sort entries within session by createdAt ascending
    entries.sort((a, b) => a.createdAt.localeCompare(b.createdAt));

    const earliest = entries[0].createdAt;
    sessions.push({
      sessionId,
      sessionDate: earliest.split('T')[0],
      queryCount: entries.length,
      entries,
    });
  }

  // Sort sessions by date descending
  sessions.sort((a, b) => b.sessionDate.localeCompare(a.sessionDate));

  return sessions;
}
