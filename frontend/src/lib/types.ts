// Backend API response shapes (snake_case, matching Supabase)

export interface ApiSource {
  source_id: string;
  source_name: string;
  url: string;
  source_type: 'web' | 'instagram';
  status: 'pending' | 'active' | 'error' | 'hold' | 'scraped' | 'failed';
  crawl_depth: 'page' | 'half' | 'full';
  college_id: string | null;
  last_scraped: string | null;
}

export interface ApiDocument {
  document_id: string;
  title: string;
  source_url: string | null;
  document_type: string | null;
  date_added: string;
  admin_id: string | null;
  college_name?: string;
  topic_name?: string;
}

export interface ApiQuery {
  query_id: string;
  query_text: string;
  response_text: string | null;
  was_answered: boolean;
  created_at: string;
  session_id: string | null;
}

// Frontend UI shapes (camelCase, matching existing components)

export interface Document {
  id: string;
  title: string;
  type: string;
  college: string;
  topic: string;
  dateAdded: string;
  sourceUrl: string;
}

export interface QueryEntry {
  id: string;
  queryText: string;
  status: 'answered' | 'referral';
  time: string;
  response: string;
  language: 'ar' | 'en';
  direction: 'rtl' | 'ltr';
  sessionId: string;
  createdAt: string;
}

export interface Session {
  sessionDate: string;
  sessionId: string;
  queryCount: number;
  entries: QueryEntry[];
}
