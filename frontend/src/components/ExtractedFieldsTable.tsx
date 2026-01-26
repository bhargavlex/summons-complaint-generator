import { useState } from 'react';
import { Edit2, Save, X, Download, FileText } from 'lucide-react';
import { ExtractedField } from '../App';

interface ExtractedFieldsTableProps {
  fields: ExtractedField[];
  updateField: (id: string, newValue: string) => void;
  onGeneratePreview?: () => void;
  showPreview?: boolean;
}

export function ExtractedFieldsTable({ fields, updateField, onGeneratePreview, showPreview = false }: ExtractedFieldsTableProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const handleEdit = (field: ExtractedField) => {
    setEditingId(field.id);
    setEditValue(field.value);
  };

  const handleSave = (id: string) => {
    updateField(id, editValue);
    setEditingId(null);
    setEditValue('');
  };

  const handleCancel = () => {
    setEditingId(null);
    setEditValue('');
  };

  const handleExport = () => {
    alert('Exporting extracted fields as CSV...');
  };

  const getTagClass = (tag: string) => {
    switch (tag) {
      case 'extracted':
        return 'bg-green-100 text-green-700';
      case 'missing':
        return 'bg-red-100 text-red-700';
      case 'manual override':
        return 'bg-blue-100 text-blue-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden flex flex-col h-[calc(100vh-250px)]">
      <div className="border-b border-gray-200 px-4 py-3 bg-gray-50 flex items-center justify-between">
        <h2 className="font-semibold text-gray-900">Extracted Fields</h2>
        <div className="flex items-center gap-2">
          {onGeneratePreview && (
            <button
              onClick={onGeneratePreview}
              className="flex items-center gap-2 bg-[#175784] text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm"
            >
              <FileText className="w-4 h-4" />
              {showPreview ? 'Refresh Preview' : 'Generate Preview'}
            </button>
          )}
          <button
            onClick={handleExport}
            className="flex items-center gap-2 text-sm text-[#175784] hover:text-blue-700 hover:bg-blue-50 px-3 py-1.5 rounded transition-colors"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Field Name
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Value
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Tag
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider w-24">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {fields.map((field) => (
              <tr key={field.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                  {field.fieldName}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  {editingId === field.id ? (
                    <input
                      type="text"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      className="w-full px-2 py-1 border border-blue-500 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                      autoFocus
                    />
                  ) : (
                    <span className={field.value === '' ? 'text-gray-400 italic' : ''}>
                      {field.value || '[Empty]'}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getTagClass(field.tag)}`}>
                    {field.tag}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm">
                  {editingId === field.id ? (
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleSave(field.id)}
                        className="p-1.5 text-green-600 hover:bg-green-50 rounded transition-colors"
                        title="Save"
                      >
                        <Save className="w-4 h-4" />
                      </button>
                      <button
                        onClick={handleCancel}
                        className="p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors"
                        title="Cancel"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => handleEdit(field)}
                      className="p-1.5 text-[#175784] hover:bg-blue-50 rounded transition-colors"
                      title="Edit"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="border-t border-gray-200 px-4 py-3 bg-gray-50">
        <p className="text-sm text-gray-600">
          <span className="font-semibold">{fields.length}</span> fields •{' '}
          <span className="text-green-600 font-semibold">
            {fields.filter(f => f.tag === 'extracted').length}
          </span> extracted •{' '}
          <span className="text-red-600 font-semibold">
            {fields.filter(f => f.tag === 'missing').length}
          </span> missing •{' '}
          <span className="text-blue-600 font-semibold">
            {fields.filter(f => f.tag === 'manual override').length}
          </span> manually edited
        </p>
      </div>
    </div>
  );
}