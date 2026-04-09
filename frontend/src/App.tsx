import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { LanguageProvider } from "@/contexts/LanguageContext";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Landing from "./pages/Landing.tsx";
import Index from "./pages/Index.tsx";
import NotFound from "./pages/NotFound.tsx";
import AdminLogin from "./pages/admin/AdminLogin.tsx";
import AdminDashboard from "./pages/admin/AdminDashboard.tsx";
import AdminQueries from "./pages/admin/AdminQueries.tsx";
import AdminQueryDetail from "./pages/admin/AdminQueryDetail.tsx";
import AdminKnowledge from "./pages/admin/AdminKnowledge.tsx";
import AdminLayout from "./components/admin/AdminLayout.tsx";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <LanguageProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/chat" element={<Index />} />
            <Route path="/admin/login" element={<AdminLogin />} />
            <Route path="/admin" element={<AdminLayout><AdminDashboard /></AdminLayout>} />
            <Route path="/admin/queries" element={<AdminLayout><AdminQueries /></AdminLayout>} />
            <Route path="/admin/queries/:id" element={<AdminLayout><AdminQueryDetail /></AdminLayout>} />
            <Route path="/admin/knowledge" element={<AdminLayout><AdminKnowledge /></AdminLayout>} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </LanguageProvider>
  </QueryClientProvider>
);

export default App;
