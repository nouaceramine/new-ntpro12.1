import { Card, CardContent } from './ui/card';
import { DollarSign, TrendingUp, AlertTriangle, Users, Package, Receipt } from 'lucide-react';

const iconMap = {
  revenue: DollarSign,
  trend: TrendingUp,
  warning: AlertTriangle,
  users: Users,
  products: Package,
  sales: Receipt
};

export const StatCard = ({ title, value, icon = 'revenue', color = 'primary', subtitle }) => {
  const Icon = iconMap[icon] || DollarSign;
  const colors = {
    primary: 'text-primary',
    green: 'text-green-500',
    orange: 'text-orange-500',
    red: 'text-red-500',
    blue: 'text-blue-500'
  };

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold">{value}</p>
            {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
          </div>
          <Icon className={`h-8 w-8 ${colors[color]}`} />
        </div>
      </CardContent>
    </Card>
  );
};

export const StatsGrid = ({ stats }) => (
  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
    {stats.map((stat, i) => (
      <StatCard key={i} {...stat} />
    ))}
  </div>
);
