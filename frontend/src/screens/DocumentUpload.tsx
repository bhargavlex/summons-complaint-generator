import { useState, useRef } from 'react';
import { Upload, FileText, X, ChevronRight } from 'lucide-react';
import { Screen } from '../App';

interface DocumentUploadProps {
  onNavigate: (screen: Screen) => void;
}

interface UploadedFile {
  id: string;
  name: string;
  size: string;
  type: string;
  file: File; // Store the actual File object
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB in bytes
const ALLOWED_TYPES = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain', 'application/msword'];

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function getFileType(mimeType: string): string {
  if (mimeType === 'application/pdf') return 'PDF';
  if (mimeType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') return 'DOCX';
  if (mimeType === 'application/msword') return 'DOC';
  if (mimeType === 'text/plain') return 'TXT';
  return 'Unknown';
}

export function DocumentUpload({ onNavigate }: DocumentUploadProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFirm, setSelectedFirm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    if (file.size > MAX_FILE_SIZE) {
      return `File "${file.name}" exceeds the maximum size of 10MB`;
    }
    if (!ALLOWED_TYPES.includes(file.type)) {
      return `File "${file.name}" is not a supported type. Please upload PDF, DOCX, or TXT files.`;
    }
    return null;
  };

  const processFiles = (fileList: FileList | File[]) => {
    const fileArray = Array.from(fileList);
    const newFiles: UploadedFile[] = [];
    const errors: string[] = [];

    fileArray.forEach((file) => {
      const error = validateFile(file);
      if (error) {
        errors.push(error);
        return;
      }

      const uploadedFile: UploadedFile = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        name: file.name,
        size: formatFileSize(file.size),
        type: getFileType(file.type),
        file: file,
      };
      newFiles.push(uploadedFile);
    });

    if (errors.length > 0) {
      alert(errors.join('\n'));
    }

    if (newFiles.length > 0) {
      setFiles((prevFiles) => [...prevFiles, ...newFiles]);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const handleFileInput = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
      // Reset the input so the same file can be selected again
      e.target.value = '';
    }
  };

  const removeFile = (id: string) => {
    setFiles(files.filter(f => f.id !== id));
  };

  const handleProceed = () => {
    if (files.length === 0) {
      alert('Please upload at least one document');
      return;
    }
    if (!selectedFirm) {
      alert('Please select a firm');
      return;
    }
    if (!selectedCategory) {
      alert('Please select a case category');
      return;
    }
    // TODO: Upload files to backend API here
    // For now, just navigate to the next screen
    onNavigate('extraction');
  };

  return (
    <main className="container mx-auto px-6 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">Upload Legal Documents</h2>
          <p className="text-gray-600">Upload your legal documents to extract fields automatically</p>
        </div>
        
        {/* Firm Selection */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Choose Firm</h3>
          <select
            value={selectedFirm}
            onChange={(e) => setSelectedFirm(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select a firm...</option>
            <option value="cohan-law">Cohan Law PLLC</option>
            <option value="raphaelson-Levine">Raphaelson & Levine Law Firm, P.C.</option>
          </select>
        </div>

        {/* Case Category Selection */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Choose Case Category</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { id: 'premises', name: 'Premises', desc: 'Injury claims occurring on another\'s property' },
              { id: 'mva', name: 'Motor Vehicle Accident', desc: 'Personal injury or property damage from vehicle collisions' },
              { id: 'med-mal', name: 'Medical Malpractice', desc: 'Claims involving professional negligence by healthcare providers' },
              { id: 'other', name: 'Other', desc: 'General or miscellaneous legal matters' },
            ].map((category) => (
              <label
                key={category.id}
                className={`flex items-start p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                  selectedCategory === category.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-300'
                }`}
              >
                <input
                  type="radio"
                  name="caseCategory"
                  value={category.id}
                  checked={selectedCategory === category.id}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-4 h-4 mt-1 text-blue-600 focus:ring-blue-500"
                />
                <div className="ml-3">
                  <span className="font-medium text-gray-900 block">{category.name}</span>
                  <span className="text-sm text-gray-500">{category.desc}</span>
                </div>
              </label>
            ))}
          </div>
        </div>
        
        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.doc,.docx,.txt,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
          onChange={handleFileChange}
          className="hidden"
        />

        {/* Upload Area */}
        <div
          className={`border-2 border-dashed rounded-lg p-12 mb-6 text-center transition-colors ${
            dragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 bg-white hover:border-gray-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="flex flex-col items-center">
            <div className="bg-blue-100 p-4 rounded-full mb-4">
              <Upload className="w-8 h-8 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Drop your files here, or browse
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Supports: PDF, DOCX, TXT (Max 10MB per file)
            </p>
            <button
              onClick={handleFileInput}
              className="bg-[#175784] text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Browse Files
            </button>
          </div>
        </div>

        {/* Uploaded Files List */}
        {files.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="font-semibold text-gray-900">Uploaded Files ({files.length})</h3>
            </div>
            <div className="divide-y divide-gray-200">
              {files.map((file) => (
                <div key={file.id} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50">
                  <div className="flex items-center gap-3">
                    <div className="bg-red-100 p-2 rounded">
                      <FileText className="w-5 h-5 text-red-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{file.name}</p>
                      <p className="text-sm text-gray-500">{file.size} • {file.type}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => removeFile(file.id)}
                    className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => onNavigate('dashboard')}
            className="text-gray-600 hover:text-gray-900 transition-colors"
          >
            ← Back to Dashboard
          </button>
          <button
            onClick={handleProceed}
            className="flex items-center gap-2 bg-[#175784] text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={files.length === 0}
          >
            Proceed to Extraction
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    </main>
  );
}