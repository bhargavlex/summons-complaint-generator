import { useState, useEffect, useCallback } from 'react';
import mammoth from 'mammoth';
import { DocumentPreview } from '../components/DocumentPreview';
import { ExtractedFieldsTable } from '../components/ExtractedFieldsTable';
import { ActionButtons } from '../components/ActionButtons';
import { ProgressBar } from '../components/ProgressBar';
import { Screen } from '../App';
import type { ExtractedField } from '../App';
import { apiClient } from '../api/client';
import type { FieldValueResponse } from '../api/client';
import { Loader2 } from 'lucide-react';

function mapApiFieldToExtracted(f: FieldValueResponse): ExtractedField {
  let tag: ExtractedField['tag'] = 'missing';
  if (f.manual_value != null && f.manual_value !== '') tag = 'manual override';
  else if ((f.current_value ?? '').trim() !== '') tag = 'extracted';
  return {
    id: String(f.field_value_id),
    fieldName: f.display_name,
    value: f.current_value ?? '',
    tag,
  };
}

interface ExtractionReviewProps {
  onNavigate: (screen: Screen) => void;
  sessionUuid: string | null;
}

export function ExtractionReview({ onNavigate, sessionUuid }: ExtractionReviewProps) {
  const [fields, setFields] = useState<ExtractedField[]>([]);
  const [fieldsLoading, setFieldsLoading] = useState(false);
  const [fieldsError, setFieldsError] = useState<string | null>(null);
  const [previewHtml, setPreviewHtml] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [showPreview, setShowPreview] = useState(true);

  const loadFields = useCallback(async () => {
    if (!sessionUuid) return;
    setFieldsLoading(true);
    setFieldsError(null);
    try {
      const list = await apiClient.getSessionFields(sessionUuid);
      setFields(list.map(mapApiFieldToExtracted));
    } catch (err) {
      setFieldsError(err instanceof Error ? err.message : 'Failed to load fields');
    } finally {
      setFieldsLoading(false);
    }
  }, [sessionUuid]);

  useEffect(() => {
    loadFields();
  }, [loadFields]);

  const loadPreview = useCallback(async () => {
    if (!sessionUuid) return;
    setPreviewLoading(true);
    try {
      const blob = await apiClient.getPreviewBlob(sessionUuid);
      const arrayBuffer = await blob.arrayBuffer();
      const result = await mammoth.convertToHtml({ arrayBuffer });
      setPreviewHtml(result.value);
      setShowPreview(true);
    } catch (err) {
      console.error('Preview load failed:', err);
    } finally {
      setPreviewLoading(false);
    }
  }, [sessionUuid]);

  useEffect(() => {
    if (sessionUuid && fields.length > 0) {
      loadPreview();
    }
  }, [sessionUuid, fields.length]); // Load preview once we have fields; re-run only when session or field count changes

  const updateField = async (id: string, newValue: string) => {
    if (!sessionUuid) return;
    const fieldValueId = Number(id);
    if (Number.isNaN(fieldValueId)) return;
    try {
      await apiClient.updateField(sessionUuid, fieldValueId, newValue);
      setFields(prev =>
        prev.map(f =>
          f.id === id
            ? { ...f, value: newValue, tag: 'manual override' as const }
            : f
        )
      );
      await loadPreview();
    } catch (err) {
      console.error('Update field failed:', err);
    }
  };

  const handleGeneratePreview = () => {
    setShowPreview(true);
    loadPreview();
  };

  const [extractionLoading, setExtractionLoading] = useState(false);
  const handleRunLLM = async () => {
    if (!sessionUuid) return;
    setExtractionLoading(true);
    try {
      const result = await apiClient.runExtraction(sessionUuid);
      if (result.success) {
        await loadFields();
        await loadPreview();
      } else {
        alert(result.message || 'LLM extraction did not run. Upload at least one PDF and try again.');
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'LLM extraction failed.');
    } finally {
      setExtractionLoading(false);
    }
  };

  if (!sessionUuid) {
    return (
      <main className="container mx-auto px-6 py-8">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 text-center">
          <p className="text-amber-800 font-medium">No session selected.</p>
          <p className="text-amber-700 text-sm mt-2">Start by choosing a firm and case type, then proceed to extraction.</p>
          <button
            onClick={() => onNavigate('upload')}
            className="mt-4 text-[#175784] hover:underline"
          >
            ← Back to Upload
          </button>
        </div>
      </main>
    );
  }

  return (
    <>
      <ProgressBar />
      <main className="container mx-auto px-6 py-8">
        {fieldsLoading ? (
          <div className="flex items-center justify-center gap-2 text-gray-600 py-12">
            <Loader2 className="w-6 h-6 animate-spin" />
            Loading fields...
          </div>
        ) : fieldsError ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-800 font-medium">{fieldsError}</p>
            <button onClick={loadFields} className="mt-4 text-red-700 hover:underline">Retry</button>
          </div>
        ) : (
          <div className={`grid gap-6 ${showPreview ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1'}`}>
            {showPreview && (
              <DocumentPreview
                fields={fields}
                previewHtml={previewHtml}
                previewLoading={previewLoading}
                onRefreshPreview={loadPreview}
                onDownloadPreview={() => sessionUuid && apiClient.getPreview(sessionUuid)}
              />
            )}
            <ExtractedFieldsTable
              fields={fields}
              updateField={updateField}
              onGeneratePreview={handleGeneratePreview}
              showPreview={showPreview}
            />
          </div>
        )}
        <ActionButtons
          onNavigate={onNavigate}
          onRunLLM={handleRunLLM}
          extractionLoading={extractionLoading}
        />
      </main>
    </>
  );
}