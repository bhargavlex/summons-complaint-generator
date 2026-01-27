import { FileCheck, Sparkles } from 'lucide-react';
import { Screen } from '../App';

interface ActionButtonsProps {
  onNavigate: (screen: Screen) => void;
}

export function ActionButtons({ onNavigate }: ActionButtonsProps) {
  const handleRunLLM = () => {
    alert('Running LLM extraction on uploaded legal documents...');
  };

  const handleFinalize = () => {
    alert('Finalizing document and generating PDF...');
    setTimeout(() => {
      onNavigate('library');
    }, 1000);
  };

  return (
    <div className="mt-6 flex items-center justify-end gap-4">
      <button
        onClick={handleRunLLM}
        className="flex items-center gap-2 bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-colors shadow-sm"
      >
        <Sparkles className="w-5 h-4" />
        Run LLM Extraction
      </button>
      <button
        onClick={handleFinalize}
        className="flex items-center gap-2 bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors shadow-sm"
      >
        <FileCheck className="w-5 h-4" />
        Finalize Document
      </button>
    </div>
  );
}