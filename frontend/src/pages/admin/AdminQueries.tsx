import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, CheckCircle, XCircle, Download, MessageSquare, ChevronRight } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useAdminQueries } from '@/hooks/useQueries';
import type { QueryEntry, Session } from '@/lib/types';

export type { QueryEntry, Session };

const statusConfig = {
  answered: { label: 'Answered', icon: CheckCircle, color: 'text-green-600' },
  referral: { label: 'Referral', icon: XCircle, color: 'text-destructive' },
};


//Converts plain response text into a React node array with clickable URLs.
const renderTextWithLinks = (text: string) => {
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  const parts = text.split(urlRegex);
  return parts.map((part, i) =>
    urlRegex.test(part) ? (
      <a
        key={i}
        href={part}
        target="_blank"
        rel="noopener noreferrer"
        className="text-primary underline break-all"
      >
        {part}
      </a>
    ) : (
      <span key={i}>{part}</span>
    )
  );
};

//Renders query-log sessions with search/filter controls and CSV export.
const AdminQueries = () => {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useAdminQueries();
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'answered' | 'referral'>('all');

  const sessions = data?.sessions ?? [];
  const allQueries = data?.allQueries ?? [];

  const totalQueries = allQueries.length;
  const answeredCount = allQueries.filter((q) => q.status === 'answered').length;
  const referralCount = allQueries.filter((q) => q.status === 'referral').length;

  //Filter sessions based on search and status
  const filteredSessions = sessions
    .map((session) => {
      const filteredEntries = session.entries.filter((e) => {
        const matchesSearch = e.queryText.toLowerCase().includes(search.toLowerCase());
        const matchesFilter = filter === 'all' || e.status === filter;
        return matchesSearch && matchesFilter;
      });
      //Drop sessions with no visible entries so the UI only shows matching groups.
      return filteredEntries.length > 0 ? { ...session, entries: filteredEntries, queryCount: filteredEntries.length } : null;
    })
    .filter(Boolean) as Session[];

  // Exports all query logs as a CSV file for spreadsheet tools.
  const exportCSV = () => {
    const headers = ['Session Date', 'Query ID', 'Query Text', 'Response', 'Status', 'Time', 'Language'];
    const rows = sessions.flatMap((s) =>
      s.entries.map((e) => [
        s.sessionDate,
        e.id,
        `"${e.queryText.replace(/"/g, '""')}"`,
        `"${e.response.replace(/"/g, '""')}"`,
        e.status === 'answered' ? 'Answered' : 'Referral',
        e.time,
        e.language,
      ])
    );
    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    //Prefix with BOM so Arabic text opens correctly in Excel.
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `query-logs-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    //Release the temporary object URL
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <h2 className="text-xl font-bold text-foreground">Query Logs</h2>
        <Button onClick={exportCSV} variant="outline" className="gap-2" disabled={allQueries.length === 0}>
          <Download size={16} />
          Export CSV
        </Button>
      </div>



      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search queries..."
            className="pl-9"
          />
        </div>
        <div className="flex gap-2">
          {(['all', 'answered', 'referral'] as const).map((f) => (
            <Button
              key={f}
              variant={filter === f ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter(f)}
              className="text-xs capitalize"
            >
              {f === 'all' ? 'All' : f === 'answered' ? 'Answered' : 'Referral'}
            </Button>
          ))}
        </div>
      </div>

      {/* Sessions */}
      <div className="space-y-5">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <Card key={i} className="shadow-sm">
              <CardContent className="py-4 px-5 space-y-3">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </CardContent>
            </Card>
          ))
        ) : isError ? (
          <Card className="shadow-sm">
            <CardContent className="py-8 text-center text-destructive text-sm">
              Failed to load queries. Please try again.
            </CardContent>
          </Card>
        ) : filteredSessions.length === 0 ? (
          <Card className="shadow-sm">
            <CardContent className="py-8 text-center text-muted-foreground text-sm">
              No queries found.
            </CardContent>
          </Card>
        ) : (
          filteredSessions.map((session) => (
            <Card key={session.sessionId} className="shadow-sm overflow-hidden">
              <CardContent className="py-0 px-0">
                {/* Session header */}
                <div className="flex items-center gap-3 px-5 py-3 border-b border-border/60 bg-secondary/30">
                  <MessageSquare size={14} className="text-muted-foreground shrink-0" />
                  <span className="text-xs font-semibold text-foreground">
                    Session — {session.sessionDate}
                  </span>
                  <Badge variant="secondary" className="text-[10px] tabular-nums">
                    {session.queryCount} {session.queryCount === 1 ? 'query' : 'queries'}
                  </Badge>
                </div>

                {/* Entries */}
                {session.entries.map((entry, idx) => {
                  const sc = statusConfig[entry.status];
                  const StatusIcon = sc.icon;
                  const isLast = idx === session.entries.length - 1;

                  return (
                    <div
                      key={entry.id}
                      className={`group ${!isLast ? 'border-b border-border/40' : ''}`}
                    >
                      <button
                        onClick={() => navigate(`/admin/queries/${entry.id}`)}
                        className="w-full text-left px-5 py-4 hover:bg-secondary/30 transition-colors"
                      >
                        {/* Query header row */}
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <div className="flex items-center gap-2 shrink-0">
                            <span className={`flex items-center gap-1 text-xs font-medium ${sc.color}`}>
                              <StatusIcon size={12} />
                              {sc.label}
                            </span>
                            <span className="text-[11px] text-muted-foreground tabular-nums">{entry.time}</span>
                          </div>
                          <ChevronRight size={14} className="text-muted-foreground shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>

                        {/* Query text */}
                        <p
                          dir={entry.direction}
                          className="text-sm font-medium text-foreground leading-relaxed mb-2"
                        >
                          {entry.queryText}
                        </p>

                        {/* Response */}
                        <div
                          dir={entry.direction}
                          className="text-xs text-muted-foreground leading-relaxed whitespace-pre-line break-words"
                        >
                          {renderTextWithLinks(entry.response)}
                        </div>
                      </button>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default AdminQueries;
