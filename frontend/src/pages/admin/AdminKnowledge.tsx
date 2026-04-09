import { useState } from 'react';
import { Plus, Search, Pencil, Trash2, Upload } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '@/components/ui/alert-dialog';

interface Document {
  id: number;
  title: string;
  type: string;
  college: string;
  topic: string;
  dateAdded: string;
  sourceUrl: string;
}

const colleges = [
  'All Colleges', 'Engineering', 'Science', 'Arts', 'Law', 'Medicine',
  'Education', 'Business Administration', 'Sharia & Islamic Studies',
];

const topics = [
  'Admissions', 'Registration', 'Exams', 'Scholarships',
  'Calendar', 'Regulations', 'Student Services', 'Graduation',
];

const docTypes = ['PDF', 'HTML', 'DOCX', 'URL'];

const initialDocs: Document[] = [
  { id: 1, title: 'KU Official Website', type: 'URL', college: 'All Colleges', topic: 'Student Services', dateAdded: '2025-03-20', sourceUrl: 'https://www.ku.edu.kw/' },
  { id: 2, title: 'Vice Dean for Student Affairs for CLS', type: 'URL', college: 'CLS', topic: 'Student Services', dateAdded: '2025-03-18', sourceUrl: 'https://www.instagram.com/vdsa_cls/' },
  { id: 3, title: 'Deanship of Admission and Registration — Official Account', type: 'URL', college: 'All Colleges', topic: 'Admissions', dateAdded: '2025-03-15', sourceUrl: 'https://x.com/Register_Ku' },
  { id: 4, title: 'Student Handbook 2025/2026', type: 'PDF', college: 'All Colleges', topic: 'Regulations', dateAdded: '2025-03-12', sourceUrl: '' },
];

const emptyForm = { title: '', type: 'PDF', college: 'All Colleges', topic: 'Admissions', sourceUrl: '' };

const AdminKnowledge = () => {
  const [docs, setDocs] = useState<Document[]>(initialDocs);
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const filtered = docs.filter((d) =>
    d.title.toLowerCase().includes(search.toLowerCase()) ||
    d.topic.toLowerCase().includes(search.toLowerCase())
  );

  const openAdd = () => {
    setEditId(null);
    setForm(emptyForm);
    setFormErrors({});
    setModalOpen(true);
  };

  const openEdit = (doc: Document) => {
    setEditId(doc.id);
    setForm({ title: doc.title, type: doc.type, college: doc.college, topic: doc.topic, sourceUrl: doc.sourceUrl });
    setFormErrors({});
    setModalOpen(true);
  };

  const validate = () => {
    const errors: Record<string, string> = {};
    if (!form.title.trim()) errors.title = 'Title is required';
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSave = () => {
    if (!validate()) return;
    if (editId !== null) {
      setDocs((prev) => prev.map((d) => d.id === editId ? { ...d, ...form, title: form.title.trim() } : d));
    } else {
      const newDoc: Document = {
        id: Date.now(),
        title: form.title.trim(),
        type: form.type,
        college: form.college,
        topic: form.topic,
        dateAdded: new Date().toISOString().split('T')[0],
        sourceUrl: form.sourceUrl,
      };
      setDocs((prev) => [newDoc, ...prev]);
    }
    setModalOpen(false);
  };

  const handleDelete = () => {
    if (deleteId !== null) {
      setDocs((prev) => prev.filter((d) => d.id !== deleteId));
      setDeleteId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <h2 className="text-xl font-bold text-foreground">Content</h2>
        <Button onClick={openAdd} className="gap-2">
          <Plus size={16} />
          Add Document
        </Button>
      </div>

      {/* Search */}
      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <div className="relative max-w-sm">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by title or topic..."
              className="pl-9"
            />
          </div>
        </CardHeader>
        <CardContent className="px-0 pb-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="hidden md:table-cell">College</TableHead>
                  <TableHead className="hidden sm:table-cell">Topic</TableHead>
                  <TableHead className="hidden sm:table-cell">Date Added</TableHead>
                  <TableHead className="hidden xl:table-cell">Source URL</TableHead>
                  <TableHead className="w-24">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                      No documents found.
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.map((doc) => (
                    <TableRow key={doc.id}>
                      <TableCell className="font-medium text-sm max-w-[200px] truncate">{doc.title}</TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="text-[11px]">{doc.type}</Badge>
                      </TableCell>
                      <TableCell className="hidden md:table-cell text-sm text-muted-foreground">{doc.college}</TableCell>
                      <TableCell className="hidden sm:table-cell text-sm text-muted-foreground">{doc.topic}</TableCell>
                      <TableCell className="hidden sm:table-cell text-sm text-muted-foreground tabular-nums">
                        {new Date(doc.dateAdded).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
                      </TableCell>
                      <TableCell className="hidden xl:table-cell text-sm text-muted-foreground max-w-[160px] truncate">
                        {doc.sourceUrl || '—'}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => openEdit(doc)}
                            className="p-1.5 hover:bg-secondary rounded text-muted-foreground hover:text-foreground transition-colors"
                            title="Edit"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            onClick={() => setDeleteId(doc.id)}
                            className="p-1.5 hover:bg-destructive/10 rounded text-muted-foreground hover:text-destructive transition-colors"
                            title="Delete"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Add/Edit Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="sm:max-w-md" dir="ltr">
          <DialogHeader>
            <DialogTitle>{editId !== null ? 'Edit Document' : 'Add Document'}</DialogTitle>
            <DialogDescription>
              {editId !== null ? 'Update the document details below.' : 'Fill in the details to add a new document to the knowledge base.'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="doc-title">Title *</Label>
              <Input
                id="doc-title"
                value={form.title}
                onChange={(e) => { setForm({ ...form, title: e.target.value }); setFormErrors({}); }}
                placeholder="Document title"
              />
              {formErrors.title && <p className="text-destructive text-xs">{formErrors.title}</p>}
            </div>

            <div className="space-y-2">
              <Label>Document Type</Label>
              <Select dir="ltr" value={form.type} onValueChange={(v) => setForm({ ...form, type: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {docTypes.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Source URL</Label>
              <Input
                value={form.sourceUrl}
                onChange={(e) => setForm({ ...form, sourceUrl: e.target.value })}
                placeholder="https://..."
              />
            </div>

            <div className="flex items-center gap-3 p-3 border border-dashed border-border rounded-lg bg-secondary/30 cursor-pointer hover:bg-secondary/50 transition-colors">
              <Upload size={18} className="text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Upload PDF</span>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>College</Label>
                <Select dir="ltr" value={form.college} onValueChange={(v) => setForm({ ...form, college: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {colleges.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Topic</Label>
                <Select dir="ltr" value={form.topic} onValueChange={(v) => setForm({ ...form, topic: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {topics.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button onClick={handleSave}>{editId !== null ? 'Save Changes' : 'Add Document'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={deleteId !== null} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent dir="ltr">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Document</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this document? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default AdminKnowledge;
