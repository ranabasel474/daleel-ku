import { useState, useRef } from 'react';
import { Plus, Search, Pencil, Trash2, Upload, Loader2, Link } from 'lucide-react';
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
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { useDocuments, useCreateDocument, useUpdateDocument, useDeleteDocument, useUploadDocument, useColleges } from '@/hooks/useDocuments';

//Predefined topics for select fields in the add/edit form.
const topics = [
  'Admissions', 'Registration', 'Exams', 'Scholarships',
  'Calendar', 'Regulations', 'Student Services', 'Graduation',
];

//Predefined document types for the type select field in the add/edit form.
const docTypes = ['PDF', 'HTML', 'DOCX', 'URL'];

//Defines an empty form state for resetting the add/edit dialog when opening it for a new document.
const emptyForm = { title: '', type: 'PDF', college: '', topic: 'Admissions', sourceUrl: '' };

//Renders the knowledge-base admin page with real API-backed CRUD for documents.
const AdminKnowledge = () => {
  const { data: docs = [], isLoading, isError } = useDocuments();
  const { data: colleges = [] } = useColleges();
  const createDoc = useCreateDocument();
  const updateDoc = useUpdateDocument();
  const deleteDoc = useDeleteDocument();
  const uploadDoc = useUploadDocument();
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [ingestMode, setIngestMode] = useState<'upload' | 'url'>('upload');
  const [pdfUrl, setPdfUrl] = useState('');

  const isSaving = createDoc.isPending || updateDoc.isPending || uploadDoc.isPending;

  const filtered = docs.filter((d) =>
    d.title.toLowerCase().includes(search.toLowerCase()) ||
    d.topic.toLowerCase().includes(search.toLowerCase())
  );

  //Opens the add dialog with a clean form and no validation leftovers.
  const openAdd = () => {
    setEditId(null);
    setForm(emptyForm);
    setFormErrors({});
    setSelectedFile(null);
    setIngestMode('upload');
    setPdfUrl('');
    if (fileInputRef.current) fileInputRef.current.value = '';
    setModalOpen(true);
  };

  //Opens the edit dialog and preloads form fields from the selected document.
  const openEdit = (doc: { id: string; title: string; type: string; college: string; topic: string; sourceUrl: string }) => {
    setEditId(doc.id);
    setForm({ title: doc.title, type: doc.type, college: doc.college, topic: doc.topic, sourceUrl: doc.sourceUrl });
    setFormErrors({});
    setModalOpen(true);
  };

  // Validates current form values and returns true when the form is ready to save.
  const validate = () => {
    const errors: Record<string, string> = {};
    if (!form.title.trim()) errors.title = 'Title is required';
    if (!editId && ingestMode === 'url') {
      if (!pdfUrl.trim() || !pdfUrl.startsWith('http')) {
        errors.pdfUrl = 'A valid PDF URL is required';
      }
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  //Persists form data via the API. Uses upload endpoint when a PDF file is attached.
  const handleSave = () => {
    if (!validate()) return;

    const onError = (err: Error) => toast({ title: 'Error', description: err.message, variant: 'destructive' });

    if (editId !== null) {
      const payload = {
        title: form.title.trim(),
        source_url: form.sourceUrl,
        document_type: form.type,
      };
      updateDoc.mutate(
        { id: editId, data: payload },
        { onSuccess: () => setModalOpen(false), onError },
      );
    } else if (selectedFile) {
      uploadDoc.mutate(
        { file: selectedFile, title: form.title.trim() },
        {
          onSuccess: (data) => {
            setModalOpen(false);
            setSelectedFile(null);
            toast({ title: 'Uploaded', description: `PDF ingested — ${data.chunks_created} chunks created.` });
          },
          onError,
        },
      );
    } else {
      const payload = {
        title: form.title.trim(),
        source_url: form.sourceUrl,
        document_type: form.type,
      };
      createDoc.mutate(payload, {
        onSuccess: () => setModalOpen(false),
        onError,
      });
    }
  };

  //Deletes the selected document via the API.
  const handleDelete = () => {
    if (deleteId !== null) {
      deleteDoc.mutate(deleteId, {
        onSuccess: () => setDeleteId(null),
        onError: (err) => {
          setDeleteId(null);
          toast({ title: 'Error', description: err.message, variant: 'destructive' });
        },
      });
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
                {isLoading ? (
                  Array.from({ length: 4 }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell><Skeleton className="h-4 w-40" /></TableCell>
                      <TableCell><Skeleton className="h-5 w-12" /></TableCell>
                      <TableCell className="hidden md:table-cell"><Skeleton className="h-4 w-20" /></TableCell>
                      <TableCell className="hidden sm:table-cell"><Skeleton className="h-4 w-20" /></TableCell>
                      <TableCell className="hidden sm:table-cell"><Skeleton className="h-4 w-24" /></TableCell>
                      <TableCell className="hidden xl:table-cell"><Skeleton className="h-4 w-32" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                    </TableRow>
                  ))
                ) : isError ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-destructive py-8">
                      Failed to load documents. Please try again.
                    </TableCell>
                  </TableRow>
                ) : filtered.length === 0 ? (
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
                        {doc.dateAdded !== '—' ? new Date(doc.dateAdded).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : '—'}
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

            {editId && (
              <div className="space-y-2">
                <Label>Document Type</Label>
                <Select dir="ltr" value={form.type} onValueChange={(v) => setForm({ ...form, type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {docTypes.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            )}

            {editId && (
              <div className="space-y-2">
                <Label>Source URL</Label>
                <Input
                  value={form.sourceUrl}
                  onChange={(e) => setForm({ ...form, sourceUrl: e.target.value })}
                  placeholder="https://..."
                />
              </div>
            )}

            {!editId && (
              <Tabs value={ingestMode} onValueChange={(v) => setIngestMode(v as 'upload' | 'url')}>
                <TabsList className="w-full">
                  <TabsTrigger value="upload" className="flex-1 gap-2">
                    <Upload size={14} /> Upload PDF
                  </TabsTrigger>
                  <TabsTrigger value="url" className="flex-1 gap-2">
                    <Link size={14} /> From URL
                  </TabsTrigger>
                </TabsList>
                <TabsContent value="upload">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0] ?? null;
                      setSelectedFile(file);
                      if (file) setForm((f) => ({ ...f, type: 'PDF', title: f.title || file.name.replace(/\.pdf$/i, '') }));
                    }}
                  />
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center gap-3 p-3 border border-dashed border-border rounded-lg bg-secondary/30 cursor-pointer hover:bg-secondary/50 transition-colors"
                  >
                    <Upload size={18} className="text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">
                      {selectedFile ? selectedFile.name : 'Click to select a PDF file'}
                    </span>
                  </div>
                </TabsContent>
                <TabsContent value="url">
                  <div className="space-y-2">
                    <Input
                      value={pdfUrl}
                      onChange={(e) => { setPdfUrl(e.target.value); setFormErrors({}); }}
                      placeholder="https://example.com/document.pdf"
                    />
                    {formErrors.pdfUrl && <p className="text-destructive text-xs">{formErrors.pdfUrl}</p>}
                    <p className="text-[11px] text-muted-foreground">
                      Direct link to a PDF file. It will be downloaded and processed.
                    </p>
                  </div>
                </TabsContent>
              </Tabs>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>College</Label>
                <Select dir="ltr" value={form.college} onValueChange={(v) => setForm({ ...form, college: v })}>
                  <SelectTrigger><SelectValue placeholder="Select college" /></SelectTrigger>
                  <SelectContent>
                    {colleges.map((c) => <SelectItem key={c.college_id} value={c.college_name}>{c.college_name}</SelectItem>)}
                  </SelectContent>
                </Select>
                <p className="text-[11px] text-muted-foreground">Assigned during ingestion</p>
              </div>
              <div className="space-y-2">
                <Label>Topic</Label>
                <Select dir="ltr" value={form.topic} onValueChange={(v) => setForm({ ...form, topic: v })}>
                  <SelectTrigger><SelectValue placeholder="Select topic" /></SelectTrigger>
                  <SelectContent>
                    {topics.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                  </SelectContent>
                </Select>
                <p className="text-[11px] text-muted-foreground">Assigned during ingestion</p>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? <><Loader2 size={16} className="animate-spin mr-2" /> Saving...</> : editId !== null ? 'Save Changes' : 'Add Document'}
            </Button>
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
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90" disabled={deleteDoc.isPending}>
              {deleteDoc.isPending ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default AdminKnowledge;
