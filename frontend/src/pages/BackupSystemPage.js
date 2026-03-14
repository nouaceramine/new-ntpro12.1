import { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import axios from 'axios';
import { Database, Download, Calendar, Shield, Clock, HardDrive, Plus, Trash2 } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function BackupSystemPage() {
  const { language } = useLanguage();
  const isAr = language === 'ar';
  const [backups, setBackups] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showSchedule, setShowSchedule] = useState(false);
  const [scheduleForm, setScheduleForm] = useState({ frequency: 'daily', time: '02:00', format: 'json', auto_email: false, keep_last: 7 });

  const token = localStorage.getItem('token');
  const headers = { Authorization: `Bearer ${token}` };

  const fetchData = async () => {
    try {
      const [bRes, sRes, stRes] = await Promise.all([
        axios.get(`${API}/backup/list`, { headers }),
        axios.get(`${API}/backup/schedules/list`, { headers }),
        axios.get(`${API}/backup/stats/summary`, { headers }),
      ]);
      setBackups(bRes.data);
      setSchedules(sRes.data);
      setStats(stRes.data);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  const createBackup = async () => {
    setCreating(true);
    try {
      const res = await axios.post(`${API}/backup/create`, { backup_type: 'full', format: 'json' }, { headers });
      toast.success(isAr ? `تم إنشاء النسخة الاحتياطية (${res.data.records_count} سجل)` : `Backup créé (${res.data.records_count} records)`);
      fetchData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Error'); }
    setCreating(false);
  };

  const createSchedule = async () => {
    try {
      await axios.post(`${API}/backup/schedules`, scheduleForm, { headers });
      toast.success(isAr ? 'تم إنشاء الجدول' : 'Schedule créé');
      setShowSchedule(false);
      fetchData();
    } catch (e) { toast.error('Error'); }
  };

  const deleteBackup = async (id) => {
    try {
      await axios.delete(`${API}/backup/${id}`, { headers });
      toast.success(isAr ? 'تم الحذف' : 'Supprimé');
      fetchData();
    } catch (e) { toast.error('Error'); }
  };

  const formatSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  return (
    <Layout>
      <div className="p-4 md:p-6 space-y-6" data-testid="backup-system-page">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white">{isAr ? 'النسخ الاحتياطي' : 'Sauvegardes'}</h1>
            <p className="text-sm text-gray-400 mt-1">{isAr ? 'إدارة النسخ الاحتياطية للنظام' : 'Gestion des sauvegardes système'}</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setShowSchedule(true)} className="gap-2 border-gray-600" data-testid="schedule-backup-btn"><Calendar className="w-4 h-4" />{isAr ? 'جدول تلقائي' : 'Planifier'}</Button>
            <Button onClick={createBackup} disabled={creating} className="gap-2" data-testid="create-backup-btn"><Database className="w-4 h-4" />{creating ? (isAr ? 'جاري...' : 'En cours...') : (isAr ? 'نسخ احتياطي الآن' : 'Sauvegarder')}</Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: isAr ? 'إجمالي النسخ' : 'Total backups', value: stats.total_backups || 0, icon: Database, color: 'text-blue-400' },
            { label: isAr ? 'الحجم الكلي' : 'Taille totale', value: formatSize(stats.total_size), icon: HardDrive, color: 'text-purple-400' },
            { label: isAr ? 'إجمالي السجلات' : 'Total records', value: (stats.total_records || 0).toLocaleString(), icon: Shield, color: 'text-emerald-400' },
            { label: isAr ? 'جداول نشطة' : 'Schedules actifs', value: stats.active_schedules || 0, icon: Clock, color: 'text-amber-400' },
          ].map((s, i) => (
            <Card key={i} className="bg-gray-800/50 border-gray-700"><CardContent className="p-4 flex items-center gap-3">
              <s.icon className={`w-8 h-8 ${s.color}`} />
              <div><p className="text-xs text-gray-400">{s.label}</p><p className="text-xl font-bold text-white">{s.value}</p></div>
            </CardContent></Card>
          ))}
        </div>

        {/* Backups List */}
        <div>
          <h2 className="text-lg font-semibold text-white mb-3">{isAr ? 'النسخ الاحتياطية' : 'Sauvegardes'}</h2>
          <div className="space-y-3">
            {loading ? <p className="text-gray-400 text-center py-8">{isAr ? 'جاري التحميل...' : 'Chargement...'}</p> :
             backups.length === 0 ? <p className="text-gray-400 text-center py-8">{isAr ? 'لا توجد نسخ احتياطية' : 'Aucune sauvegarde'}</p> :
             backups.map(b => (
              <Card key={b.id} className="bg-gray-800/50 border-gray-700" data-testid={`backup-${b.id}`}>
                <CardContent className="p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
                  <div className="flex items-center gap-3">
                    <Database className="w-10 h-10 text-blue-400 p-2 bg-blue-500/10 rounded-lg" />
                    <div>
                      <div className="flex items-center gap-2"><span className="text-white font-medium">{b.backup_number}</span><Badge className="bg-emerald-500/10 text-emerald-400">{b.status}</Badge></div>
                      <p className="text-sm text-gray-400">{b.tables_count} {isAr ? 'جدول' : 'tables'} | {(b.records_count || 0).toLocaleString()} {isAr ? 'سجل' : 'records'} | {formatSize(b.file_size)}</p>
                      <p className="text-xs text-gray-500">{new Date(b.created_at).toLocaleString(isAr ? 'ar-DZ' : 'fr-FR')}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" className="gap-1 border-gray-600 text-gray-300" data-testid={`download-backup-${b.id}`}><Download className="w-3 h-3" />{isAr ? 'تحميل' : 'Télécharger'}</Button>
                    <Button size="sm" variant="ghost" className="text-red-400" onClick={() => deleteBackup(b.id)}><Trash2 className="w-3 h-3" /></Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Schedules */}
        {schedules.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold text-white mb-3">{isAr ? 'الجداول التلقائية' : 'Planifications'}</h2>
            <div className="space-y-2">
              {schedules.map(s => (
                <Card key={s.id} className="bg-gray-800/50 border-gray-700"><CardContent className="p-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Clock className="w-5 h-5 text-amber-400" />
                    <div><span className="text-white">{s.frequency}</span><span className="text-gray-400 text-sm ml-2">{s.time}</span></div>
                  </div>
                  <Badge className={s.is_active ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}>{s.is_active ? (isAr ? 'نشط' : 'Actif') : (isAr ? 'متوقف' : 'Inactif')}</Badge>
                </CardContent></Card>
              ))}
            </div>
          </div>
        )}

        {/* Schedule Dialog */}
        <Dialog open={showSchedule} onOpenChange={setShowSchedule}>
          <DialogContent className="bg-gray-900 border-gray-700 text-white max-w-md">
            <DialogHeader><DialogTitle>{isAr ? 'جدول نسخ احتياطي تلقائي' : 'Planifier sauvegarde'}</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <Select value={scheduleForm.frequency} onValueChange={v => setScheduleForm({...scheduleForm, frequency: v})}><SelectTrigger className="bg-gray-800 border-gray-700"><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="daily">{isAr ? 'يومي' : 'Quotidien'}</SelectItem><SelectItem value="weekly">{isAr ? 'أسبوعي' : 'Hebdomadaire'}</SelectItem><SelectItem value="monthly">{isAr ? 'شهري' : 'Mensuel'}</SelectItem></SelectContent>
              </Select>
              <Input type="time" value={scheduleForm.time} onChange={e => setScheduleForm({...scheduleForm, time: e.target.value})} className="bg-gray-800 border-gray-700" />
              <Input type="number" placeholder={isAr ? 'الاحتفاظ بآخر' : 'Garder les derniers'} value={scheduleForm.keep_last} onChange={e => setScheduleForm({...scheduleForm, keep_last: parseInt(e.target.value) || 7})} className="bg-gray-800 border-gray-700" />
              <Button onClick={createSchedule} className="w-full" data-testid="submit-schedule-btn">{isAr ? 'حفظ الجدول' : 'Enregistrer'}</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
