import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import AcademicBotLogo from '@/components/AcademicBotLogo';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const AdminLogin = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setError('Please enter your username and password');
      return;
    }
    // Mock auth — replace with Supabase Auth
    if (username === 'admin' && password === 'admin') {
      navigate('/admin');
    } else {
      setError('Invalid username or password');
    }
  };

  return (
    <div className="min-h-dvh bg-background flex items-center justify-center p-4" dir="ltr">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-primary mx-auto flex items-center justify-center mb-4">
            <AcademicBotLogo size={32} color="hsl(var(--primary-foreground))" animated={false} />
          </div>
          <h1 className="text-xl font-bold text-foreground">Daleel KU</h1>
          <p className="text-sm text-muted-foreground mt-1">Admin Panel</p>
        </div>

        {/* Form */}
        <form onSubmit={handleLogin} className="bg-card rounded-xl border border-border p-6 shadow-sm space-y-4">
          <div className="space-y-2">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              value={username}
              onChange={(e) => { setUsername(e.target.value); setError(''); }}
              placeholder="admin"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => { setPassword(e.target.value); setError(''); }}
                placeholder="••••••••"
                className="pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {error && <p className="text-destructive text-sm">{error}</p>}

          <Button type="submit" className="w-full">Sign In</Button>
        </form>
      </div>
    </div>
  );
};

export default AdminLogin;
