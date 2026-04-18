import { FileText, MessageSquare, CheckCircle, XCircle, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Table, TableHeader, TableBody, TableHead, TableRow, TableCell,
} from '@/components/ui/table';
import { allQueries } from '@/pages/admin/AdminQueries';

//Static Data for demo purposes until we connect the backend.
const initialDocs = [
  { id: 1, title: 'KU Official Website', type: 'URL', topic: 'Student Services', college: 'All Colleges', dateAdded: '2025-03-20' },
  { id: 2, title: 'Vice Dean for Student Affairs for CLS', type: 'URL', topic: 'Student Services', college: 'CLS', dateAdded: '2025-03-18' },
  { id: 3, title: 'Deanship of Admission and Registration — Official Account', type: 'URL', topic: 'Admissions', college: 'All Colleges', dateAdded: '2025-03-15' },
  { id: 4, title: 'Student Handbook 2025/2026', type: 'PDF', topic: 'Regulations', college: 'All Colleges', dateAdded: '2025-03-12' },
];

//Renders the admin overview with aggregate metrics plus recent query/content snapshots.
const AdminDashboard = () => {
  const navigate = useNavigate();

  const totalDocs = initialDocs.length;
  const totalQueries = allQueries.length;
  const answeredCount = allQueries.filter((q) => q.status === 'answered').length;
  const referralCount = allQueries.filter((q) => q.status === 'referral').length;

  //Show the newest queries first while keeping the source array unchanged.
  const recentQueries = allQueries.slice(-5).reverse();
  //Sort by ISO date string and keep only the latest three entries for the summary table.
  const recentDocs = [...initialDocs].sort((a, b) => b.dateAdded.localeCompare(a.dateAdded)).slice(0, 3);

  //Keeps card rendering declarative so labels/icons/counts stay in one place.
  const stats = [
    { label: 'Total Documents', value: totalDocs, icon: FileText, color: 'text-primary' },
    { label: 'Total Queries', value: totalQueries, icon: MessageSquare, color: 'text-primary' },
    { label: 'Answered Queries', value: answeredCount, icon: CheckCircle, color: 'text-green-600' },
    { label: 'Referral Queries', value: referralCount, icon: XCircle, color: 'text-destructive' },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-foreground">Overview</h2>

      {/* Row 1 — Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card key={stat.label} className="shadow-sm">
            <CardContent className="pt-5 pb-4 px-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">{stat.label}</p>
                  <p className="text-2xl font-bold mt-1 text-foreground tabular-nums">{stat.value}</p>
                </div>
                <div className={`p-2.5 rounded-lg bg-secondary ${stat.color}`}>
                  <stat.icon size={18} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Row 2 — Recent Queries */}
      <Card className="shadow-sm">
        <CardContent className="p-0">
          <div className="flex items-center justify-between px-5 py-4 border-b border-border/60">
            <h3 className="text-sm font-semibold text-foreground">Recent Queries</h3>
            <Button variant="ghost" size="sm" className="gap-1 text-xs" onClick={() => navigate('/admin/queries')}>
              View All <ChevronRight size={14} />
            </Button>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Query Text</TableHead>
                <TableHead className="w-28">Status</TableHead>
                <TableHead className="w-28">Time</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recentQueries.map((q) => (
                <TableRow
                  key={q.id}
                  className="cursor-pointer"
                  onClick={() => navigate(`/admin/queries/${q.id}`)}
                >
                  <TableCell dir={q.direction} className="truncate max-w-[300px]">{q.queryText}</TableCell>
                  <TableCell>
                    {q.status === 'answered' ? (
                      <Badge variant="secondary" className="text-green-600 text-[11px] gap-1">
                        <CheckCircle size={12} /> Answered
                      </Badge>
                    ) : (
                      <Badge variant="destructive" className="text-[11px] gap-1">
                        <XCircle size={12} /> Referral
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground text-xs tabular-nums">{q.time}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Row 3 — Knowledge Base Summary */}
      <Card className="shadow-sm">
        <CardContent className="px-5 py-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-foreground">Latest Content&nbsp;</h3>
            <Button variant="ghost" size="sm" className="gap-1 text-xs" onClick={() => navigate('/admin/knowledge')}>
              View All <ChevronRight size={14} />
            </Button>
          </div>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="hidden sm:table-cell">Topic</TableHead>
                  <TableHead className="hidden md:table-cell">College</TableHead>
                  <TableHead>Date Added</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentDocs.map((doc) => (
                  <TableRow key={doc.id}>
                    <TableCell className="font-medium text-sm max-w-[200px] truncate">{doc.title}</TableCell>
                    <TableCell><Badge variant="secondary" className="text-[11px]">{doc.type}</Badge></TableCell>
                    <TableCell className="hidden sm:table-cell text-sm text-muted-foreground">{doc.topic}</TableCell>
                    <TableCell className="hidden md:table-cell text-sm text-muted-foreground">{doc.college}</TableCell>
                    <TableCell className="text-muted-foreground text-xs tabular-nums">{doc.dateAdded}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminDashboard;
