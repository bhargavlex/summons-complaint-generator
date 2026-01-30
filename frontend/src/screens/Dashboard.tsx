import { FileText, Clock } from 'lucide-react';
import { Screen } from '../App';

interface DashboardProps {
  onNavigate: (screen: Screen) => void;
}

export function Dashboard({ onNavigate }: DashboardProps) {
  const stats = [
    { label: 'Total Documents', value: '247', icon: FileText, color: 'bg-blue-500' },
    { label: 'In Progress', value: '5', icon: Clock, color: 'bg-yellow-500' },
    // { label: 'Success Rate', value: '96%', icon: TrendingUp, color: 'bg-green-500' },
  ];

  const recentDocuments = [
    { id: 1, name: 'Summons - Doe v. Acme Corp', caseNo: '23CV12345', date: 'Jan 22, 2026', status: 'In Review' },
    { id: 2, name: 'Complaint - Smith v. Tech Inc', caseNo: '23CV12344', date: 'Jan 21, 2026', status: 'Completed' },
    { id: 3, name: 'Summons - Johnson v. City', caseNo: '23CV12343', date: 'Jan 20, 2026', status: 'Completed' },
    { id: 4, name: 'Motion - Brown v. State', caseNo: '23CV12342', date: 'Jan 19, 2026', status: 'In Progress' },
  ];

  return (
    <main className="container mx-auto px-6 py-8">
      <div className="mb-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">Welcome back</h2>
        <p className="text-gray-600">Manage your summons and complaint document generation workflow</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">{stat.label}</p>
                  <p className="text-3xl font-semibold text-gray-900">{stat.value}</p>
                </div>
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Documents */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Documents</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Document Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Case Number
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {recentDocuments.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50 transition-colors cursor-pointer">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{doc.name}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{doc.caseNo}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{doc.date}</td>
                  <td className="px-6 py-4 text-sm">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        doc.status === 'Completed'
                          ? 'bg-green-100 text-green-800'
                          : doc.status === 'In Review'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}
                    >
                      {doc.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={() => onNavigate('library')}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            View all documents →
          </button>
        </div>
      </div>
    </main>
  );
}
