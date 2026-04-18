import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, CheckCircle, XCircle, Download, MessageSquare, ChevronRight } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

export interface QueryEntry {
  id: number;
  queryText: string;
  status: 'answered' | 'referral';
  time: string;
  response: string;
  language: 'ar' | 'en';
  direction: 'rtl' | 'ltr';
}

//Sessions are grouped by date for easier browsing in the UI
export interface Session {
  sessionDate: string;
  queryCount: number;
  entries: QueryEntry[];
}
//Static mock data simulating query sessions for demonstration purposes unless connected to a backend. 
export const sessionsData: Session[] = [
  {
    sessionDate: '2026-03-20',
    queryCount: 3,
    entries: [
      {
        id: 1,
        queryText: 'متى يتم التقديم لجامعة الكويت؟',
        status: 'answered',
        time: '09:10 AM',
        response: 'يتم تقديم طلب الالتحاق إلكترونيًا خلال الفترة التي تعلنها عمادة القبول والتسجيل عبر الموقع الرسمي، ولا يُقبل أي طلب بعد انتهاء المواعيد المحددة. كما يمكن متابعة الإعلانات عبر الحساب الرسمي: https://x.com/Register_Ku',
        language: 'ar',
        direction: 'rtl',
      },
      {
        id: 2,
        queryText: 'طيب وين أقدم بالضبط؟',
        status: 'answered',
        time: '09:13 AM',
        response: 'يمكنك التقديم عبر بوابة القبول الإلكترونية لجامعة الكويت من خلال الرابط التالي:\n\nhttps://portal.ku.edu.kw/kuadm/faces/login.jspx?_afrLoop=917086342041201&_afrWindowMode=0&_adf.ctrl-state=3dwyxpr2f_4#TS00000000076=c6a35a6e98e8e8480169c462d521074f4ef9bd837ceb69d597dcde8e2d013833ef',
        language: 'ar',
        direction: 'rtl',
      },
      {
        id: 3,
        queryText: 'بعد ما أقدم هل أقدر أغير التخصصات اللي اخترتها؟',
        status: 'answered',
        time: '09:17 AM',
        response: 'لا، لا يُسمح بتعديل التخصصات بعد انتهاء فترة تقديم الطلبات، لذلك يُنصح باختيار أكبر عدد ممكن من الرغبات قبل الإرسال.',
        language: 'ar',
        direction: 'rtl',
      },
    ],
  },
  {
    sessionDate: '2026-03-21',
    queryCount: 3,
    entries: [
      {
        id: 4,
        queryText: 'القبول للفصل الثاني مفتوح الحين، ليش ما أقدر أقدم على كلية الحقوق؟',
        status: 'answered',
        time: '11:05 AM',
        response: 'لأن بعض الكليات مثل كلية الحقوق يكون القبول فيها للفصل الدراسي الأول فقط، لذلك لا تظهر ضمن خيارات الفصل الثاني.',
        language: 'ar',
        direction: 'rtl',
      },
      {
        id: 5,
        queryText: 'يعني إذا ما انقبلت فيها الحين، شنو أسوي؟',
        status: 'answered',
        time: '11:09 AM',
        response: 'يمكنك التقديم على تخصصات متاحة في الفصل الثاني، ثم لاحقًا التقديم للمنافسة على الكليات التي تقبل في الفصل الأول عند فتح باب القبول للفصل التالي.',
        language: 'ar',
        direction: 'rtl',
      },
      {
        id: 6,
        queryText: 'هل أحتفظ برقمي الجامعي إذا غيرت التخصص لاحقًا؟',
        status: 'answered',
        time: '11:13 AM',
        response: 'نعم، في حال قبولك لاحقًا في تخصص آخر من خلال المنافسة، يتم الاحتفاظ برقمك الجامعي وسجلك الدراسي.',
        language: 'ar',
        direction: 'rtl',
      },
    ],
  },
  {
    sessionDate: '2026-03-22',
    queryCount: 1,
    entries: [
      {
        id: 7,
        queryText: 'أنا خريج أدبي هل يمكنني دخول تخصص تقني؟',
        status: 'answered',
        time: '02:00 PM',
        response: 'التخصصات التقنية والعلمية مثل الهندسة والطب والعلوم تقتصر على خريجي القسم العلمي، لذلك لا يمكن لخريجي القسم الأدبي الالتحاق بها.',
        language: 'ar',
        direction: 'rtl',
      },
    ],
  },
  {
    sessionDate: '2026-03-23',
    queryCount: 1,
    entries: [
      {
        id: 8,
        queryText: 'How do I register for courses after being accepted?',
        status: 'answered',
        time: '10:15 AM',
        response: 'Students register through the Kuwait University portal by accessing Academic Services → Registration Services → Registration, then adding courses to their schedule.\n\nPortal: https://portal.ku.edu.kw/',
        language: 'en',
        direction: 'ltr',
      },
    ],
  },
  {
    sessionDate: '2026-03-24',
    queryCount: 1,
    entries: [
      {
        id: 9,
        queryText: 'أنا معدلي 2.3 وأبغى أعرف كيف أحسب المعدل المتوقع وأبني خطة دراسية، من وين أبدأ؟',
        status: 'referral',
        time: '01:20 PM',
        response: 'يُفضل مراجعة مكتب التوجيه والإرشاد التابع لكليتك، حيث يمكنهم مساعدتك في حساب المعدل ووضع خطة دراسية مناسبة.',
        language: 'ar',
        direction: 'rtl',
      },
    ],
  },
  {
    sessionDate: '2026-03-25',
    queryCount: 1,
    entries: [
      {
        id: 10,
        queryText: 'هل توجد منح دراسية داخل جامعة الكويت وما هي؟',
        status: 'referral',
        time: '03:05 PM',
        response: 'نعم يوجد يمكنك التواصل عبر خدمة "الواتساب" الخاص بالقسم وهو (24984114) أو الحضور لقسم المنح الدراسية بإدارة الإسكان الطلابي وشئون الطلبة الوافدين.',
        language: 'ar',
        direction: 'rtl',
      },
    ],
  },
];

//Make one list of all queries from all sessions for easy reuse.
export const allQueries: QueryEntry[] = sessionsData.flatMap((s) =>
  s.entries.map((e) => ({ ...e, sessionDate: s.sessionDate }))
);

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
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'answered' | 'referral'>('all');

  const totalQueries = allQueries.length;
  const answeredCount = allQueries.filter((q) => q.status === 'answered').length;
  const referralCount = allQueries.filter((q) => q.status === 'referral').length;

  //Filter sessions based on search and status
  const filteredSessions = sessionsData
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
    const headers = ['Session Date', 'Query #', 'Query Text', 'Response', 'Status', 'Time', 'Language'];
    const rows = sessionsData.flatMap((s) =>
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
        <Button onClick={exportCSV} variant="outline" className="gap-2">
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
        {filteredSessions.length === 0 ? (
          <Card className="shadow-sm">
            <CardContent className="py-8 text-center text-muted-foreground text-sm">
              No queries found.
            </CardContent>
          </Card>
        ) : (
          filteredSessions.map((session) => (
            <Card key={session.sessionDate} className="shadow-sm overflow-hidden">
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
                            <span className="text-[11px] font-bold text-muted-foreground tabular-nums w-5">
                              {entry.id}.
                            </span>
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
