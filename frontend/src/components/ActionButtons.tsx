import { FileCheck, Sparkles, Loader2 } from 'lucide-react';
import { Screen } from '../App';

interface ActionButtonsProps {
  onNavigate: (screen: Screen) => void;
  onRunLLM?: () => Promise<void>;
  extractionLoading?: boolean;
}

export function ActionButtons({ onNavigate, onRunLLM, extractionLoading = false }: ActionButtonsProps) {
  const handleFinalize = () => {
    alert('Finalizing document and generating PDF...');
    setTimeout(() => {
      onNavigate('library');
    }, 1000);
  };

  return (
    <div className="mt-6 flex items-center justify-end gap-4">
      {onRunLLM && (
        <button
          onClick={onRunLLM}
          disabled={extractionLoading}
          className="flex items-center gap-2 bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-colors shadow-sm disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {extractionLoading ? (
            <>
              <Loader2 className="w-5 h-4 animate-spin" />
              Extracting...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-4" />
              Run LLM Extraction
            </>
          )}
        </button>
      )}
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