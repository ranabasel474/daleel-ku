import { useState, useRef, useMemo } from 'react';
import { Plus, Search, Pencil, Trash2, Upload, Loader2, Check, ChevronsUpDown, Globe } from 'lucide-react';
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
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import { Skeleton } from '@/components/ui/skeleton';
import { Checkbox } from '@/components/ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';
import {
  useDocuments, useCreateDocument, useUpdateDocument, useDeleteDocument,
  useUploadDocument, useColleges, useTopics, useCreateSource, useTriggerScrape,
  useSources, useDeleteSource, useUpdateSource,
} from '@/hooks/useDocuments';
import type { ApiSource } from '@/lib/types';

const docTypes = ['PDF', 'web', 'instagram', 'text'];
const emptyForm = { title: '', type: 'PDF', college: '', topic: '', sourceUrl: '' };

const statusBadgeVariant = (status: ApiSource['status']) => {
  if (status === 'active' || status === 'scraped') return 'default';
  if (status === 'error' || status === 'failed') return 'destructive';
  if (status === 'hold') return 'outline';
  return 'secondary'; // pending
};

const AdminKnowledge = () => {
  const { data: docs = [], isLoading, isError } = useDocuments();
  const { data: colleges = [] } = useColleges();
  const { data: topics = [] } = useTopics();
  const { data: sources = [], isLoading: sourcesLoading, isError: sourcesError } = useSources();
  const createDoc = useCreateDocument();
  const updateDoc = useUpdateDocument();
  const deleteDoc = useDeleteDocument();
  const uploadDoc = useUploadDocument();
  const createSource = useCreateSource();
  const updateSource = useUpdateSource();
  const deleteSource = useDeleteSource();
  const triggerScrape = useTriggerScrape();
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [topicOpen, setTopicOpen] = useState(false);
  const [topicSearch, setTopicSearch] = useState('');
  const [sourceModalOpen, setSourceModalOpen] = useState(false);
  const [sourceForm, setSourceForm] = useState({ source_name: '', url: '', source_type: 'web' as 'web' | 'instagram', crawl_depth: 'page' as 'page' | 'half' | 'full' });
  const [scrapeNow, setScrapeNow] = useState(true);
  const [sourceFormErrors, setSourceFormErrors] = useState<Record<string, string>>({});
  const [deleteSourceId, setDeleteSourceId] = useState<string | null>(null);
  const [editSourceId, setEditSourceId] = useState<string | null>(null);
  const [editSourceModalOpen, setEditSourceModalOpen] = useState(false);
  const [editSourceForm, setEditSourceForm] = useState<{
    source_name: string; url: string; source_type: 'web' | 'instagram';
    crawl_depth: 'page' | 'half' | 'full'; status: ApiSource['status'];
  }>({ source_name: '', url: '', source_type: 'web', crawl_depth: 'page', status: 'pending' });
  const [editSourceErrors, setEditSourceErrors] = useState<Record<string, string>>({});
  const [scrapeOnEdit, setScrapeOnEdit] = useState(false);

  const isSaving = createDoc.isPending || updateDoc.isPending || uploadDoc.isPending;

  const filteredTopics = useMemo(() => {
    if (!topicSearch) return topics;
    const q = topicSearch.toLowerCase();
    return topics.filter((t) => t.topic_name.toLowerCase().includes(q));
  }, [topics, topicSearch]);

  const filtered = docs.filter((d) =>
    d.title.toLowerCase().includes(search.toLowerCase()) ||
    d.topic.toLowerCase().includes(search.toLowerCase())
  );

  const openAdd = () => {
    setEditId(null);
    setForm(emptyForm);
    setFormErrors({});
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    setModalOpen(true);
  };

  const openEdit = (doc: { id: string; title: string; type: string; college: string; topic: string; sourceUrl: string }) => {
    setEditId(doc.id);
    setForm({ title: doc.title, type: doc.type, college: doc.college, topic: doc.topic, sourceUrl: doc.sourceUrl });
    setFormErrors({});
    setModalOpen(true);
  };

  const validate = () => {
    const errors: Record<string, string> = {};
    if (!form.title.trim()) errors.title = 'Title is required';
    if (!editId && !selectedFile) errors.file = 'A PDF file is required';
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSave = () => {
    if (!validate()) return;

    const onError = (err: Error) => toast({ title: 'Error', description: err.message, variant: 'destructive' });

    if (editId !== null) {
      const payload: Record<string, string> = {
        title: form.title.trim(),
        source_url: form.sourceUrl,
        document_type: form.type,
      };
      if (form.topic && form.topic !== '—') payload.topic_name = form.topic;
      if (form.college && form.college !== '—') payload.college_name = form.college;
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
    }
  };

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

  const openAddSource = () => {
    setSourceForm({ source_name: '', url: '', source_type: 'web', crawl_depth: 'page' });
    setSourceFormErrors({});
    setScrapeNow(true);
    setSourceModalOpen(true);
  };

  const handleSaveSource = () => {
    const errors: Record<string, string> = {};
    if (!sourceForm.source_name.trim()) errors.source_name = 'Source name is required';
    if (!sourceForm.url.trim() || !sourceForm.url.startsWith('http')) errors.url = 'A valid URL is required';
    setSourceFormErrors(errors);
    if (Object.keys(errors).length > 0) return;

    createSource.mutate(sourceForm, {
      onSuccess: () => {
        setSourceModalOpen(false);
        if (scrapeNow) {
          triggerScrape.mutate(undefined, {
            onSuccess: () => toast({ title: 'Source Added', description: 'Source saved and scraping started in the background.' }),
            onError: () => toast({ title: 'Source Added', description: 'Source saved but scraping failed to start.', variant: 'destructive' }),
          });
        } else {
          toast({ title: 'Source Added', description: 'Source saved with status "pending".' });
        }
      },
      onError: (err) => toast({ title: 'Error', description: err.message, variant: 'destructive' }),
    });
  };

  const openEditSource = (src: ApiSource) => {
    setEditSourceId(src.source_id);
    setEditSourceForm({
      source_name: src.source_name,
      url: src.url,
      source_type: src.source_type,
      crawl_depth: src.crawl_depth,
      status: src.status,
    });
    setEditSourceErrors({});
    setScrapeOnEdit(false);
    setEditSourceModalOpen(true);
  };

  const handleSaveEditSource = () => {
    const errors: Record<string, string> = {};
    if (!editSourceForm.source_name.trim()) errors.source_name = 'Source name is required';
    if (!editSourceForm.url.trim() || !editSourceForm.url.startsWith('http')) errors.url = 'A valid URL is required';
    setEditSourceErrors(errors);
    if (Object.keys(errors).length > 0) return;

    updateSource.mutate(
      { id: editSourceId!, data: editSourceForm },
      {
        onSuccess: () => {
          setEditSourceModalOpen(false);
          toast({ title: 'Source updated' });
          if (scrapeOnEdit) {
            triggerScrape.mutate(undefined, {
              onSuccess: () => toast({ title: 'Scraping started', description: 'Scraping all pending sources in the background.' }),
              onError: () => toast({ title: 'Scraping failed', description: 'Source updated but scraping failed to start.', variant: 'destructive' }),
            });
          }
        },
        onError: (err) => toast({ title: 'Error', description: err.message, variant: 'destructive' }),
      },
    );
  };

  const handleDeleteSource = () => {
    if (deleteSourceId !== null) {
      deleteSource.mutate(deleteSourceId, {
        onSuccess: () => {
          setDeleteSourceId(null);
          toast({ title: 'Source deleted' });
        },
        onError: (err) => {
          setDeleteSourceId(null);
          toast({ title: 'Error', description: err.message, variant: 'destructive' });
        },
      });
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-foreground">Content</h2>

      <Tabs defaultValue="documents">
        <TabsList>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="sources">Sources</TabsTrigger>
        </TabsList>

        {/* ── Documents Tab ── */}
        <TabsContent value="documents" className="space-y-4 mt-4">
          <div className="flex justify-end">
            <Button onClick={openAdd} className="gap-2">
              <Plus size={16} />
              Add Document
            </Button>
          </div>

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
        </TabsContent>

        {/* ── Sources Tab ── */}
        <TabsContent value="sources" className="space-y-4 mt-4">
          <div className="flex justify-end">
            <Button onClick={openAddSource} className="gap-2">
              <Globe size={16} />
              Add Source
            </Button>
          </div>

          <Card className="shadow-sm">
            <CardContent className="px-0 pb-0">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead className="hidden sm:table-cell">URL</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead className="hidden md:table-cell">Crawl Depth</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="hidden lg:table-cell">Last Scraped</TableHead>
                      <TableHead className="w-16">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {sourcesLoading ? (
                      Array.from({ length: 3 }).map((_, i) => (
                        <TableRow key={i}>
                          <TableCell><Skeleton className="h-4 w-36" /></TableCell>
                          <TableCell className="hidden sm:table-cell"><Skeleton className="h-4 w-48" /></TableCell>
                          <TableCell><Skeleton className="h-5 w-16" /></TableCell>
                          <TableCell className="hidden md:table-cell"><Skeleton className="h-4 w-20" /></TableCell>
                          <TableCell><Skeleton className="h-5 w-16" /></TableCell>
                          <TableCell className="hidden lg:table-cell"><Skeleton className="h-4 w-28" /></TableCell>
                          <TableCell><Skeleton className="h-4 w-8" /></TableCell>
                        </TableRow>
                      ))
                    ) : sourcesError ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center text-destructive py-8">
                          Failed to load sources. Please try again.
                        </TableCell>
                      </TableRow>
                    ) : sources.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                          No sources added yet.
                        </TableCell>
                      </TableRow>
                    ) : (
                      sources.map((src) => (
                        <TableRow key={src.source_id}>
                          <TableCell className="font-medium text-sm max-w-[180px] truncate">{src.source_name}</TableCell>
                          <TableCell className="hidden sm:table-cell text-sm text-muted-foreground max-w-[200px] truncate">
                            <a href={src.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                              {src.url}
                            </a>
                          </TableCell>
                          <TableCell>
                            <Badge variant="secondary" className="text-[11px] capitalize">{src.source_type}</Badge>
                          </TableCell>
                          <TableCell className="hidden md:table-cell text-sm text-muted-foreground capitalize">
                            {src.source_type === 'web' ? src.crawl_depth : '—'}
                          </TableCell>
                          <TableCell>
                            <Badge variant={statusBadgeVariant(src.status)} className="text-[11px] capitalize">
                              {src.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="hidden lg:table-cell text-sm text-muted-foreground tabular-nums">
                            {src.last_scraped
                              ? new Date(src.last_scraped).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
                              : '—'}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => openEditSource(src)}
                                className="p-1.5 hover:bg-secondary rounded text-muted-foreground hover:text-foreground transition-colors"
                                title="Edit"
                              >
                                <Pencil size={14} />
                              </button>
                              <button
                                onClick={() => setDeleteSourceId(src.source_id)}
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
        </TabsContent>
      </Tabs>

      {/* Add/Edit Document Modal */}
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
              <div>
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
                {formErrors.file && <p className="text-destructive text-xs">{formErrors.file}</p>}
              </div>
            )}

            {editId && (
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>College</Label>
                  <Select dir="ltr" value={form.college} onValueChange={(v) => setForm({ ...form, college: v })}>
                    <SelectTrigger><SelectValue placeholder="Select college" /></SelectTrigger>
                    <SelectContent>
                      {colleges.map((c) => <SelectItem key={c.college_id} value={c.college_name}>{c.college_name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Topic</Label>
                  <Popover open={topicOpen} onOpenChange={setTopicOpen}>
                    <PopoverTrigger asChild>
                      <Button variant="outline" role="combobox" aria-expanded={topicOpen} className="w-full justify-between font-normal">
                        {form.topic || 'Select or type topic'}
                        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0" align="start">
                      <Command shouldFilter={false}>
                        <CommandInput placeholder="Search or type new topic..." value={topicSearch} onValueChange={setTopicSearch} />
                        <CommandList>
                          <CommandEmpty>
                            {topicSearch.trim() ? (
                              <button
                                className="w-full px-2 py-1.5 text-sm text-left hover:bg-accent rounded-sm"
                                onClick={() => { setForm({ ...form, topic: topicSearch.trim() }); setTopicSearch(''); setTopicOpen(false); }}
                              >
                                Create "{topicSearch.trim()}"
                              </button>
                            ) : 'No topics found.'}
                          </CommandEmpty>
                          <CommandGroup>
                            {filteredTopics.map((t) => (
                              <CommandItem
                                key={t.topic_id}
                                onSelect={() => { setForm({ ...form, topic: t.topic_name }); setTopicSearch(''); setTopicOpen(false); }}
                              >
                                <Check className={cn('mr-2 h-4 w-4', form.topic === t.topic_name ? 'opacity-100' : 'opacity-0')} />
                                {t.topic_name}
                              </CommandItem>
                            ))}
                          </CommandGroup>
                        </CommandList>
                      </Command>
                    </PopoverContent>
                  </Popover>
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? <><Loader2 size={16} className="animate-spin mr-2" /> Saving...</> : editId !== null ? 'Save Changes' : 'Add Document'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Document Confirmation */}
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

      {/* Add Source Modal */}
      <Dialog open={sourceModalOpen} onOpenChange={setSourceModalOpen}>
        <DialogContent className="sm:max-w-md" dir="ltr">
          <DialogHeader>
            <DialogTitle>Add Source</DialogTitle>
            <DialogDescription>
              Add a web or social media source to be scraped into the knowledge base.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label>Source Name *</Label>
              <Input
                value={sourceForm.source_name}
                onChange={(e) => { setSourceForm({ ...sourceForm, source_name: e.target.value }); setSourceFormErrors({}); }}
                placeholder="e.g. KU Official Instagram"
              />
              {sourceFormErrors.source_name && <p className="text-destructive text-xs">{sourceFormErrors.source_name}</p>}
            </div>
            <div className="space-y-2">
              <Label>URL *</Label>
              <Input
                value={sourceForm.url}
                onChange={(e) => { setSourceForm({ ...sourceForm, url: e.target.value }); setSourceFormErrors({}); }}
                placeholder="https://..."
              />
              {sourceFormErrors.url && <p className="text-destructive text-xs">{sourceFormErrors.url}</p>}
            </div>
            <div className="space-y-2">
              <Label>Source Type</Label>
              <Select dir="ltr" value={sourceForm.source_type} onValueChange={(v) => setSourceForm({ ...sourceForm, source_type: v as 'web' | 'instagram' })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="web">Web</SelectItem>
                  <SelectItem value="instagram">Instagram</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {sourceForm.source_type === 'web' && (
              <div className="space-y-2">
                <Label>Crawl Depth</Label>
                <Select dir="ltr" value={sourceForm.crawl_depth} onValueChange={(v) => setSourceForm({ ...sourceForm, crawl_depth: v as 'page' | 'half' | 'full' })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="page">Single Page</SelectItem>
                    <SelectItem value="half">Half Site</SelectItem>
                    <SelectItem value="full">Full Site</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
            <div className="flex items-center gap-2">
              <Checkbox id="scrape-now" checked={scrapeNow} onCheckedChange={(v) => setScrapeNow(v === true)} />
              <Label htmlFor="scrape-now" className="text-sm font-normal cursor-pointer">Scrape Now</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSourceModalOpen(false)}>Cancel</Button>
            <Button onClick={handleSaveSource} disabled={createSource.isPending}>
              {createSource.isPending ? <><Loader2 size={16} className="animate-spin mr-2" /> Saving...</> : 'Add Source'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Source Modal */}
      <Dialog open={editSourceModalOpen} onOpenChange={setEditSourceModalOpen}>
        <DialogContent className="sm:max-w-md" dir="ltr">
          <DialogHeader>
            <DialogTitle>Edit Source</DialogTitle>
            <DialogDescription>Update the source details below.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label>Source Name *</Label>
              <Input
                value={editSourceForm.source_name}
                onChange={(e) => { setEditSourceForm({ ...editSourceForm, source_name: e.target.value }); setEditSourceErrors({}); }}
                placeholder="e.g. KU Official Website"
              />
              {editSourceErrors.source_name && <p className="text-destructive text-xs">{editSourceErrors.source_name}</p>}
            </div>
            <div className="space-y-2">
              <Label>URL *</Label>
              <Input
                value={editSourceForm.url}
                onChange={(e) => { setEditSourceForm({ ...editSourceForm, url: e.target.value }); setEditSourceErrors({}); }}
                placeholder="https://..."
              />
              {editSourceErrors.url && <p className="text-destructive text-xs">{editSourceErrors.url}</p>}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Source Type</Label>
                <Select dir="ltr" value={editSourceForm.source_type} onValueChange={(v) => setEditSourceForm({ ...editSourceForm, source_type: v as 'web' | 'instagram' })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="web">Web</SelectItem>
                    <SelectItem value="instagram">Instagram</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Status</Label>
                <Select dir="ltr" value={editSourceForm.status} onValueChange={(v) => setEditSourceForm({ ...editSourceForm, status: v as ApiSource['status'] })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="hold">Hold</SelectItem>
                    <SelectItem value="error">Error</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            {editSourceForm.source_type === 'web' && (
              <div className="space-y-2">
                <Label>Crawl Depth</Label>
                <Select dir="ltr" value={editSourceForm.crawl_depth} onValueChange={(v) => setEditSourceForm({ ...editSourceForm, crawl_depth: v as 'page' | 'half' | 'full' })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="page">Single Page</SelectItem>
                    <SelectItem value="half">Half Site</SelectItem>
                    <SelectItem value="full">Full Site</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
            {editSourceForm.status === 'pending' && (
              <div className="flex items-center gap-2">
                <Checkbox id="scrape-on-edit" checked={scrapeOnEdit} onCheckedChange={(v) => setScrapeOnEdit(v === true)} />
                <Label htmlFor="scrape-on-edit" className="text-sm font-normal cursor-pointer">Scrape this source now</Label>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditSourceModalOpen(false)}>Cancel</Button>
            <Button onClick={handleSaveEditSource} disabled={updateSource.isPending}>
              {updateSource.isPending ? <><Loader2 size={16} className="animate-spin mr-2" /> Saving...</> : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Source Confirmation */}
      <AlertDialog open={deleteSourceId !== null} onOpenChange={(open) => !open && setDeleteSourceId(null)}>
        <AlertDialogContent dir="ltr">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Source</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this source? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteSource} className="bg-destructive text-destructive-foreground hover:bg-destructive/90" disabled={deleteSource.isPending}>
              {deleteSource.isPending ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default AdminKnowledge;
