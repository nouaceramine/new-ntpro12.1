import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Layout } from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '../components/ui/alert-dialog';
import { toast } from 'sonner';
import { Users, Plus, Edit, Trash2, Calendar, DollarSign, Clock, UserPlus, KeyRound, UserX } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function EmployeesPage() {
  const { t, language } = useLanguage();
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [attendanceDialogOpen, setAttendanceDialogOpen] = useState(false);
  const [advanceDialogOpen, setAdvanceDialogOpen] = useState(false);
  const [accountDialogOpen, setAccountDialogOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [formData, setFormData] = useState({ name: '', phone: '', email: '', position: '', salary: '', commission_rate: '', hire_date: '' });
  const [attendanceData, setAttendanceData] = useState({ date: new Date().toISOString().split('T')[0], status: 'present', notes: '' });
  const [advanceAmount, setAdvanceAmount] = useState('');
  const [accountData, setAccountData] = useState({ email: '', password: '', role: 'seller' });
  const [creatingAccount, setCreatingAccount] = useState(false);

  const fetchEmployees = async () => {
    try {
      const res = await axios.get(`${API}/employees`);
      setEmployees(res.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchEmployees(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...formData, salary: parseFloat(formData.salary) || 0, commission_rate: parseFloat(formData.commission_rate) || 0 };
      if (selectedEmployee) {
        await axios.put(`${API}/employees/${selectedEmployee.id}`, payload);
        toast.success(t.employeeUpdated);
      } else {
        await axios.post(`${API}/employees`, payload);
        toast.success(t.employeeAdded);
      }
      setDialogOpen(false);
      resetForm();
      fetchEmployees();
    } catch (e) { toast.error(t.somethingWentWrong); }
  };

  const handleDelete = async () => {
    try {
      await axios.delete(`${API}/employees/${selectedEmployee.id}`);
      toast.success(t.employeeDeleted);
      setDeleteDialogOpen(false);
      fetchEmployees();
    } catch (e) { toast.error(t.somethingWentWrong); }
  };

  const handleAttendance = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/employees/attendance`, { employee_id: selectedEmployee.id, ...attendanceData });
      toast.success(t.recordAttendance);
      setAttendanceDialogOpen(false);
    } catch (e) { toast.error(t.somethingWentWrong); }
  };

  const handleAdvance = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/employees/advances`, { employee_id: selectedEmployee.id, amount: parseFloat(advanceAmount), notes: '' });
      toast.success(t.addAdvance);
      setAdvanceDialogOpen(false);
      setAdvanceAmount('');
      fetchEmployees();
    } catch (e) { toast.error(t.somethingWentWrong); }
  };

  const handleCreateAccount = async (e) => {
    e.preventDefault();
    if (!accountData.email || !accountData.password) {
      toast.error(language === 'ar' ? 'يرجى ملء جميع الحقول' : 'Veuillez remplir tous les champs');
      return;
    }
    setCreatingAccount(true);
    try {
      await axios.post(`${API}/employees/${selectedEmployee.id}/create-account`, accountData);
      toast.success(language === 'ar' ? 'تم إنشاء الحساب بنجاح' : 'Compte créé avec succès');
      setAccountDialogOpen(false);
      setAccountData({ email: '', password: '', role: 'seller' });
      fetchEmployees();
    } catch (e) {
      toast.error(e.response?.data?.detail || t.somethingWentWrong);
    } finally {
      setCreatingAccount(false);
    }
  };

  const handleDeleteAccount = async (employeeId) => {
    if (!window.confirm(language === 'ar' ? 'هل أنت متأكد من حذف حساب هذا الموظف؟' : 'Êtes-vous sûr de vouloir supprimer le compte?')) return;
    try {
      await axios.delete(`${API}/employees/${employeeId}/delete-account`);
      toast.success(language === 'ar' ? 'تم حذف الحساب' : 'Compte supprimé');
      fetchEmployees();
    } catch (e) {
      toast.error(e.response?.data?.detail || t.somethingWentWrong);
    }
  };

  const resetForm = () => {
    setSelectedEmployee(null);
    setFormData({ name: '', phone: '', email: '', position: '', salary: '', commission_rate: '', hire_date: '' });
  };

  const openEdit = (emp) => {
    setSelectedEmployee(emp);
    setFormData({ name: emp.name, phone: emp.phone, email: emp.email, position: emp.position, salary: emp.salary.toString(), commission_rate: emp.commission_rate.toString(), hire_date: emp.hire_date });
    setDialogOpen(true);
  };

  if (loading) return <Layout><div className="flex items-center justify-center min-h-[60vh]"><div className="spinner" /></div></Layout>;

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in" data-testid="employees-page">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">{t.employees}</h1>
            <p className="text-muted-foreground">{employees.length} {t.employees}</p>
          </div>
          <Button onClick={() => { resetForm(); setDialogOpen(true); }} className="gap-2" data-testid="add-employee-btn">
            <Plus className="h-5 w-5" />{t.addEmployee}
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {employees.map(emp => (
            <Card key={emp.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-5">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-lg">{emp.name}</h3>
                    <p className="text-sm text-muted-foreground">{emp.position || t.employees}</p>
                    {emp.phone && <p className="text-sm mt-1" dir="ltr">{emp.phone}</p>}
                  </div>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="sm" onClick={() => openEdit(emp)}><Edit className="h-4 w-4" /></Button>
                    <Button variant="ghost" size="sm" className="text-destructive" onClick={() => { setSelectedEmployee(emp); setDeleteDialogOpen(true); }}><Trash2 className="h-4 w-4" /></Button>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t text-sm">
                  <div><span className="text-muted-foreground">{t.salary}:</span> <span className="font-medium">{emp.salary} {t.currency}</span></div>
                  <div><span className="text-muted-foreground">{t.commissionRate}:</span> <span className="font-medium">{emp.commission_rate}%</span></div>
                  <div><span className="text-muted-foreground">{t.totalAdvances}:</span> <span className="font-medium text-amber-600">{emp.total_advances} {t.currency}</span></div>
                  <div><span className="text-muted-foreground">{t.totalCommission}:</span> <span className="font-medium text-emerald-600">{emp.total_commission} {t.currency}</span></div>
                </div>
                <div className="flex gap-2 mt-4">
                  <Button variant="outline" size="sm" className="flex-1" onClick={() => { setSelectedEmployee(emp); setAttendanceDialogOpen(true); }}>
                    <Calendar className="h-4 w-4 me-1" />{t.attendance}
                  </Button>
                  <Button variant="outline" size="sm" className="flex-1" onClick={() => { setSelectedEmployee(emp); setAdvanceDialogOpen(true); }}>
                    <DollarSign className="h-4 w-4 me-1" />{t.advances}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Add/Edit Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent><DialogHeader><DialogTitle>{selectedEmployee ? t.editEmployee : t.addEmployee}</DialogTitle></DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div><Label>{t.employeeName} *</Label><Input value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} required /></div>
                <div><Label>{t.position}</Label><Input value={formData.position} onChange={e => setFormData({...formData, position: e.target.value})} /></div>
                <div><Label>{t.phone}</Label><Input value={formData.phone} onChange={e => setFormData({...formData, phone: e.target.value})} dir="ltr" /></div>
                <div><Label>{t.email}</Label><Input type="email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} /></div>
                <div><Label>{t.salary}</Label><Input type="number" value={formData.salary} onChange={e => setFormData({...formData, salary: e.target.value})} /></div>
                <div><Label>{t.commissionRate} (%)</Label><Input type="number" step="0.1" value={formData.commission_rate} onChange={e => setFormData({...formData, commission_rate: e.target.value})} /></div>
                <div className="col-span-2"><Label>{t.hireDate}</Label><Input type="date" value={formData.hire_date} onChange={e => setFormData({...formData, hire_date: e.target.value})} /></div>
              </div>
              <div className="flex justify-end gap-2"><Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>{t.cancel}</Button><Button type="submit">{t.save}</Button></div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Attendance Dialog */}
        <Dialog open={attendanceDialogOpen} onOpenChange={setAttendanceDialogOpen}>
          <DialogContent><DialogHeader><DialogTitle>{t.recordAttendance} - {selectedEmployee?.name}</DialogTitle></DialogHeader>
            <form onSubmit={handleAttendance} className="space-y-4">
              <div><Label>{t.createdAt}</Label><Input type="date" value={attendanceData.date} onChange={e => setAttendanceData({...attendanceData, date: e.target.value})} /></div>
              <div><Label>{t.attendance}</Label>
                <Select value={attendanceData.status} onValueChange={v => setAttendanceData({...attendanceData, status: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="present">{t.present}</SelectItem>
                    <SelectItem value="absent">{t.absent}</SelectItem>
                    <SelectItem value="late">{t.late}</SelectItem>
                    <SelectItem value="leave">{t.leave}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div><Label>{t.notes}</Label><Input value={attendanceData.notes} onChange={e => setAttendanceData({...attendanceData, notes: e.target.value})} /></div>
              <div className="flex justify-end gap-2"><Button type="button" variant="outline" onClick={() => setAttendanceDialogOpen(false)}>{t.cancel}</Button><Button type="submit">{t.save}</Button></div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Advance Dialog */}
        <Dialog open={advanceDialogOpen} onOpenChange={setAdvanceDialogOpen}>
          <DialogContent><DialogHeader><DialogTitle>{t.addAdvance} - {selectedEmployee?.name}</DialogTitle></DialogHeader>
            <form onSubmit={handleAdvance} className="space-y-4">
              <div><Label>{t.amount}</Label><Input type="number" value={advanceAmount} onChange={e => setAdvanceAmount(e.target.value)} required /></div>
              <div className="flex justify-end gap-2"><Button type="button" variant="outline" onClick={() => setAdvanceDialogOpen(false)}>{t.cancel}</Button><Button type="submit">{t.save}</Button></div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Delete Dialog */}
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent><AlertDialogHeader><AlertDialogTitle>{t.deleteConfirm}</AlertDialogTitle><AlertDialogDescription>{selectedEmployee?.name}</AlertDialogDescription></AlertDialogHeader>
            <AlertDialogFooter><AlertDialogCancel>{t.cancel}</AlertDialogCancel><AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground">{t.delete}</AlertDialogAction></AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </Layout>
  );
}
