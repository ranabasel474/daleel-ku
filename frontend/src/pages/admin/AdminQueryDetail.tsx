import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, XCircle, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { sessionsData } from './AdminQueries';
import type { QueryEntry } from './AdminQueries';

const statusConfig = {
  answered: { label: 'Answered', icon: CheckCircle, color: 'text-green-600', badge: 'secondary' as const },
  referral: { label: 'Referral', icon: XCircle, color: 'text-destructive', badge: 'destructive' as const },
};

// Linkify URLs
const renderTextWithLinks = (text: string) => {
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  const parts = text.split(urlRegex);
  return parts.map((part, i) =>
    urlRegex.test(part) ? (
      <a key={i} href={part} target="_blank" rel="noopener noreferrer" className="text-primary underline break-all">
        {part}
      </a>
    ) : (
      <span key={i}>{part}</span>
    )
  );
};

const AdminQueryDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  // Find entry and its session
  let query: QueryEntry | undefined;
  let sessionDate = '';
  let sessionEntries: QueryEntry[] = [];

  for (const session of sessionsData) {
    const found = session.entries.find((e) => e.id === Number(id));
    if (found) {
      query = found;
      sessionDate = session.sessionDate;
      sessionEntries = session.entries;
      break;
    }
  }

  if (!query) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => navigate('/admin/queries')} className="gap-2 -ml-2">
          <ArrowLeft size={16} />
          Back to Query Logs
        </Button>
        <p className="text-muted-foreground text-center py-12">Query not found.</p>
      </div>
    );
  }

  const sc = statusConfig[query.status];
  const StatusIcon = sc.icon;
  const otherEntries = sessionEntries.filter((e) => e.id !== query!.id);

  return (
    <div className="space-y-6 max-w-3xl">
      <Button variant="ghost" onClick={() => navigate('/admin/queries')} className="gap-2 -ml-2">
        <ArrowLeft size={16} />
        Back to Query Logs
      </Button>

      {/* Main detail */}
      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Query Details</CardTitle>
            <Badge variant={sc.badge} className="text-xs gap-1">
              <StatusIcon size={12} />
              {sc.label}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Question</p>
            <p dir={query.direction} className="text-sm text-foreground leading-relaxed">
              {query.queryText}
            </p>
          </div>

          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Response</p>
            <div dir={query.direction} className="text-sm text-foreground leading-relaxed whitespace-pre-line break-words">
              {renderTextWithLinks(query.response)}
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-2 border-t border-border/60">
            <div>
              <p className="text-xs text-muted-foreground">Time</p>
              <p className="text-sm font-medium text-foreground mt-0.5">{query.time}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Session</p>
              <p className="text-sm font-medium text-foreground mt-0.5">{sessionDate}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Language</p>
              <p className="text-sm font-medium text-foreground mt-0.5 uppercase">{query.language}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Other queries in same session */}
      {otherEntries.length > 0 && (
        <Card className="shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Other Queries in This Session</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {otherEntries.map((e) => {
              const esc = statusConfig[e.status];
              const EIcon = esc.icon;
              return (
                <button
                  key={e.id}
                  onClick={() => navigate(`/admin/queries/${e.id}`)}
                  className="w-full flex items-center justify-between p-3 rounded-lg hover:bg-secondary/40 transition-colors text-left border border-border/60"
                >
                  <div className="flex-1 min-w-0">
                    <p dir={e.direction} className="text-sm text-foreground truncate">{e.queryText}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`flex items-center gap-1 text-xs ${esc.color}`}>
                        <EIcon size={12} />
                        {esc.label}
                      </span>
                      <span className="text-[11px] text-muted-foreground tabular-nums">{e.time}</span>
                    </div>
                  </div>
                </button>
              );
            })}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AdminQueryDetail;
