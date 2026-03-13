import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { 
  Bot, 
  Play, 
  Square, 
  RotateCcw, 
  Activity, 
  Package, 
  Receipt, 
  FileText,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Zap,
  TrendingUp,
  ShieldAlert,
  RefreshCw
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ROBOT_CONFIG = {
  inventory: {
    icon: Package,
    color: 'text-blue-500',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/20',
    gradient: 'from-blue-600 to-cyan-500',
  },
  debt: {
    icon: Receipt,
    color: 'text-amber-500',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/20',
    gradient: 'from-amber-500 to-orange-500',
  },
  report: {
    icon: FileText,
    color: 'text-emerald-500',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/20',
    gradient: 'from-emerald-500 to-teal-500',
  },
};

function StatBox({ label, value, icon: Icon, color }) {
  return (
    <div className="flex items-center gap-2 p-2 rounded-lg bg-muted/50" data-testid={`stat-${label}`}>
      <div className={`p-1.5 rounded-md ${color || 'bg-primary/10'}`}>
        <Icon className="h-3.5 w-3.5 text-inherit" />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground truncate">{label}</p>
        <p className="text-sm font-bold">{value}</p>
      </div>
    </div>
  );
}

function RobotCard({ name, robot, config, onRestart, onRun, loading }) {
  const Icon = config.icon;
  const isRunning = robot.is_running;
  const lastRun = robot.last_run 
    ? new Date(robot.last_run).toLocaleString('ar-DZ', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
    : '---';
  const stats = robot.stats || {};

  return (
    <Card className={`relative overflow-hidden border ${config.border} transition-all duration-300 hover:shadow-lg`} data-testid={`robot-card-${name}`}>
      <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${config.gradient}`} />
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-xl ${config.bg}`}>
              <Icon className={`h-5 w-5 ${config.color}`} />
            </div>
            <div>
              <CardTitle className="text-base">{robot.name}</CardTitle>
              <p className="text-xs text-muted-foreground mt-0.5 flex items-center gap-1">
                <Clock className="h-3 w-3" /> {lastRun}
              </p>
            </div>
          </div>
          <Badge 
            variant={isRunning ? 'default' : 'secondary'} 
            className={`text-xs ${isRunning ? 'bg-emerald-500/15 text-emerald-600 border-emerald-500/30' : 'bg-red-500/10 text-red-500 border-red-500/20'}`}
            data-testid={`robot-status-${name}`}
          >
            <span className={`inline-block h-1.5 w-1.5 rounded-full mr-1.5 ${isRunning ? 'bg-emerald-500 animate-pulse' : 'bg-red-400'}`} />
            {isRunning ? 'يعمل' : 'متوقف'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-2">
          {name === 'inventory' && (
            <>
              <StatBox label="الفحوصات" value={stats.checks || 0} icon={Activity} color="bg-blue-500/10" />
              <StatBox label="التنبيهات" value={stats.alerts_sent || 0} icon={AlertTriangle} color="bg-amber-500/10" />
              <StatBox label="التوصيات" value={stats.recommendations || 0} icon={TrendingUp} color="bg-emerald-500/10" />
              <StatBox label="التوقعات" value={stats.predictions || 0} icon={Zap} color="bg-purple-500/10" />
            </>
          )}
          {name === 'debt' && (
            <>
              <StatBox label="الفحوصات" value={stats.checks || 0} icon={Activity} color="bg-blue-500/10" />
              <StatBox label="التذكيرات" value={stats.reminders_sent || 0} icon={ShieldAlert} color="bg-amber-500/10" />
              <StatBox label="ديون متأخرة" value={stats.overdue_found || 0} icon={AlertTriangle} color="bg-red-500/10" />
              <StatBox label="SMS" value={stats.sms_sent || 0} icon={Zap} color="bg-purple-500/10" />
            </>
          )}
          {name === 'report' && (
            <>
              <StatBox label="الفحوصات" value={stats.checks || 0} icon={Activity} color="bg-blue-500/10" />
              <StatBox label="التقارير" value={stats.reports_generated || 0} icon={FileText} color="bg-emerald-500/10" />
            </>
          )}
        </div>
        <div className="flex gap-2 pt-1">
          <Button
            size="sm"
            variant="outline"
            className="flex-1 text-xs h-8"
            onClick={() => onRun(name)}
            disabled={loading}
            data-testid={`robot-run-${name}`}
          >
            <Play className="h-3.5 w-3.5 mr-1" /> تشغيل يدوي
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="flex-1 text-xs h-8"
            onClick={() => onRestart(name)}
            disabled={loading}
            data-testid={`robot-restart-${name}`}
          >
            <RotateCcw className="h-3.5 w-3.5 mr-1" /> إعادة تشغيل
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default function RobotsPage() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/robots/status`);
      setStatus(data);
    } catch (err) {
      console.error('Failed to fetch robot status:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchStatus]);

  const handleRun = async (name) => {
    setActionLoading(true);
    try {
      const { data } = await axios.post(`${API}/robots/run/${name}`);
      toast.success(data.message);
      await fetchStatus();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'فشل تشغيل الروبوت');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRestart = async (name) => {
    setActionLoading(true);
    try {
      const { data } = await axios.post(`${API}/robots/restart/${name}`);
      toast.success(data.message);
      setTimeout(fetchStatus, 2000);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'فشل إعادة تشغيل الروبوت');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStopAll = async () => {
    setActionLoading(true);
    try {
      await axios.post(`${API}/robots/stop-all`);
      toast.success('تم إيقاف جميع الروبوتات');
      await fetchStatus();
    } catch (err) {
      toast.error('فشل إيقاف الروبوتات');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStartAll = async () => {
    setActionLoading(true);
    try {
      await axios.post(`${API}/robots/start-all`);
      toast.success('تم تشغيل جميع الروبوتات');
      setTimeout(fetchStatus, 2000);
    } catch (err) {
      toast.error('فشل تشغيل الروبوتات');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]" data-testid="robots-loading">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  const robots = status?.robots || {};
  const isSystemRunning = status?.is_running;
  const runningCount = Object.values(robots).filter(r => r.is_running).length;
  const totalChecks = Object.values(robots).reduce((s, r) => s + (r.stats?.checks || 0), 0);
  const startedAt = status?.started_at 
    ? new Date(status.started_at).toLocaleString('ar-DZ', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
    : '---';

  return (
    <div className="space-y-6 p-1" data-testid="robots-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bot className="h-6 w-6 text-primary" />
            لوحة تحكم الروبوتات
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            مراقبة وإدارة الروبوتات الذكية
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => { setAutoRefresh(!autoRefresh); }}
            className={`text-xs ${autoRefresh ? 'text-emerald-600' : 'text-muted-foreground'}`}
            data-testid="toggle-auto-refresh"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1 ${autoRefresh ? 'animate-spin' : ''}`} style={autoRefresh ? { animationDuration: '3s' } : {}} />
            {autoRefresh ? 'تحديث تلقائي' : 'تحديث يدوي'}
          </Button>
          <Button size="sm" variant="outline" onClick={fetchStatus} disabled={actionLoading} data-testid="refresh-status">
            <RefreshCw className="h-3.5 w-3.5 mr-1" /> تحديث
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <Card className="border-primary/20" data-testid="overview-status">
          <CardContent className="p-4 flex items-center gap-3">
            <div className={`p-2.5 rounded-xl ${isSystemRunning ? 'bg-emerald-500/10' : 'bg-red-500/10'}`}>
              {isSystemRunning 
                ? <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                : <AlertTriangle className="h-5 w-5 text-red-500" />
              }
            </div>
            <div>
              <p className="text-xs text-muted-foreground">حالة النظام</p>
              <p className={`font-bold ${isSystemRunning ? 'text-emerald-600' : 'text-red-500'}`}>
                {isSystemRunning ? 'يعمل' : 'متوقف'}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card data-testid="overview-active">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-500/10">
              <Bot className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">روبوتات نشطة</p>
              <p className="font-bold">{runningCount} / {Object.keys(robots).length}</p>
            </div>
          </CardContent>
        </Card>
        <Card data-testid="overview-checks">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-500/10">
              <Activity className="h-5 w-5 text-purple-500" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">إجمالي الفحوصات</p>
              <p className="font-bold">{totalChecks}</p>
            </div>
          </CardContent>
        </Card>
        <Card data-testid="overview-started">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-500/10">
              <Clock className="h-5 w-5 text-amber-500" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">بدأ في</p>
              <p className="font-bold text-sm">{startedAt}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Global Controls */}
      <div className="flex gap-2">
        {isSystemRunning ? (
          <Button 
            variant="destructive" 
            size="sm" 
            onClick={handleStopAll} 
            disabled={actionLoading}
            data-testid="stop-all-btn"
          >
            <Square className="h-3.5 w-3.5 mr-1" /> إيقاف جميع الروبوتات
          </Button>
        ) : (
          <Button 
            size="sm" 
            onClick={handleStartAll} 
            disabled={actionLoading}
            className="bg-emerald-600 hover:bg-emerald-700"
            data-testid="start-all-btn"
          >
            <Play className="h-3.5 w-3.5 mr-1" /> تشغيل جميع الروبوتات
          </Button>
        )}
      </div>

      {/* Robot Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(robots).map(([name, robot]) => (
          <RobotCard
            key={name}
            name={name}
            robot={robot}
            config={ROBOT_CONFIG[name] || ROBOT_CONFIG.inventory}
            onRestart={handleRestart}
            onRun={handleRun}
            loading={actionLoading}
          />
        ))}
      </div>
    </div>
  );
}
