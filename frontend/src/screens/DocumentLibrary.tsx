import { useState } from 'react';
import { Search, Filter, Download, Eye, Trash2, Calendar } from 'lucide-react';
import { Screen } from '../App';

interface DocumentLibraryProps {
  onNavigate: (screen: Screen) => void;
}

interface Document {
  id: number;
  name: string;
  caseNo: string;
  type: string;
  date: string;
  status: string;
  plaintiff: string;
  defendant: string;
}

const documents: Document[] = [
  {
    id: 1,
    name: 'Summons - Doe v. Acme Corp',
    caseNo: '23CV12345',
    type: 'Summons',
    date: 'Jan 22, 2026',
    status: 'In Review',
    plaintiff: 'John Doe',
    defendant: 'Acme Corporation',
  },
  {
    id: 2,
    name: 'Complaint - Smith v. Tech Inc',
    caseNo: '23CV12344',
    type: 'Complaint',
    date: 'Jan 21, 2026',
    status: 'Completed',
    plaintiff: 'Jane Smith',
    defendant: 'Tech Inc',
  },
  {
    id: 3,
    name: 'Summons - Johnson v. City',
    caseNo: '23CV12343',
    type: 'Summons',
    date: 'Jan 20, 2026',
    status: 'Completed',
    plaintiff: 'Robert Johnson',
    defendant: 'City of Los Angeles',
  },
  {
    id: 4,
    name: 'Motion - Brown v. State',
    caseNo: '23CV12342',
    type: 'Motion',
    date: 'Jan 19, 2026',
    status: 'In Progress',
    plaintiff: 'Sarah Brown',
    defendant: 'State of California',
  },
  {
    id: 5,
    name: 'Complaint - Wilson v. Bank',
    caseNo: '23CV12341',
    type: 'Complaint',
    date: 'Jan 18, 2026',
    status: 'Completed',
    plaintiff: 'Michael Wilson',
    defendant: 'First National Bank',
  },
  {
    id: 6,
    name: 'Summons - Davis v. Corp',
    caseNo: '23CV12340',
    type: 'Summons',
    date: 'Jan 17, 2026',
    status: 'Completed',
    plaintiff: 'Emily Davis',
    defendant: 'Global Corp',
  },
];

export function DocumentLibrary({ onNavigate }: DocumentLibraryProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('All');

  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch =
      doc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.caseNo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.plaintiff.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.defendant.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = filterStatus === 'All' || doc.status === filterStatus;
    
    return matchesSearch && matchesFilter;
  });

  return (
    <main className="container mx-auto px-6 py-8">
      <div className="mb-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">Document Library</h2>
        <p className="text-gray-600">Browse and manage all generated legal documents</p>
      </div>

      {/* Search and Filter Bar */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by name, case number, plaintiff, or defendant..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option>All</option>
              <option>Completed</option>
              <option>In Progress</option>
              <option>In Review</option>
            </select>
          </div>
        </div>
      </div>

      {/* Documents Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 mb-6">
        {filteredDocuments.map((doc) => (
          <div
            key={doc.id}
            className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
          >
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 mb-1">{doc.name}</h3>
                  <p className="text-sm text-gray-500">Case #{doc.caseNo}</p>
                </div>
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
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-gray-500">Type:</span>
                  <span className="font-medium text-gray-900">{doc.type}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600">{doc.date}</span>
                </div>
                <div className="text-sm text-gray-600">
                  <div><strong>Plaintiff:</strong> {doc.plaintiff}</div>
                  <div><strong>Defendant:</strong> {doc.defendant}</div>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-4 border-t border-gray-200">
                <button className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors">
                  <Eye className="w-4 h-4" />
                  View
                </button>
                <button className="flex items-center justify-center gap-2 px-3 py-2 bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors">
                  <Download className="w-4 h-4" />
                </button>
                <button className="flex items-center justify-center gap-2 px-3 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Results Summary */}
      <div className="text-center text-gray-600">
        Showing {filteredDocuments.length} of {documents.length} documents
      </div>
    </main>
  );
}
