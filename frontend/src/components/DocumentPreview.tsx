import { useState, useEffect, useRef } from 'react';
import { ZoomIn, ZoomOut, Download, Loader2 } from 'lucide-react';
import { ExtractedField } from '../App';
import mammoth from 'mammoth';

interface DocumentPreviewProps {
  fields: ExtractedField[];
  templatePath?: string; // Path to the DOCX template file
}

// Map field names to placeholder patterns in the template
const fieldPlaceholderMap: Record<string, string[]> = {
  'Case_County': ['«Case_County»', 'Case_County'],
  'Plaintiff_name_': ['«Plaintiff_name_»', 'Plaintiff_name_'],
  'Defendant_name': ['«Defendant_name»', 'Defendant_name'],
  'Venue_bases_on': ['«Venue_bases_on»', 'Venue_bases_on'],
  'Venue_Street_Address_': ['«Venue_Street_Address_»', 'Venue_Street_Address_'],
  'Venue_County_State': ['«Venue_County_State»', 'Venue_County_State'],
  'Current_Month_Year': ['«Current_Month_Year»', 'Current_Month_Year'],
  'Defendant_Street_Address_': ['«Defendant_Street_Address_»', 'Defendant_Street_Address_'],
  'Defendant_City': ['«Defendant_City»', 'Defendant_City'],
  'Defendant_State': ['«Defendant_State»', 'Defendant_State'],
  'Defendant_Zip_code': ['«Defendant_Zip_code»', 'Defendant_Zip_code'],
  'Defendant_County': ['«Defendant_County»', 'Defendant_County'],
  'Plaintiff_County_': ['«Plaintiff_County_»', 'Plaintiff_County_'],
  'Plaintiff_State_': ['«Plaintiff_State_»', 'Plaintiff_State_'],
  'Date_of_accident': ['«Date_of_accident»', 'Date_of_accident'],
  'LOA': ['«LOA»', 'LOA'],
  'LOA_County': ['«LOA_County»', 'LOA_County'],
  'LOA_State': ['«LOA_State»', 'LOA_State'],
  'hisher': ['«hisher»', 'hisher'],
  'heshe': ['«heshe»', 'heshe'],
};

export function DocumentPreview({ fields, templatePath = '/templates/cohan/premises/summons_complaint.docx' }: DocumentPreviewProps) {
  const [zoom, setZoom] = useState(70);
  const [htmlContent, setHtmlContent] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const previewRef = useRef<HTMLDivElement>(null);

  // Get field value by name
  const getFieldValue = (fieldName: string): string => {
    const field = fields.find(f => f.fieldName === fieldName);
    return field?.value || '';
  };

  // Get field tag for highlighting
  const getFieldTag = (fieldName: string): string => {
    const field = fields.find(f => f.fieldName === fieldName);
    return field?.tag || 'missing';
  };

  // Replace placeholders in HTML with field values and add highlighting
  const replacePlaceholders = (html: string): string => {
    let processedHtml = html;

    fields.forEach((field) => {
      const placeholders = fieldPlaceholderMap[field.fieldName] || [`«${field.fieldName}»`, field.fieldName];
      const value = field.value || `[${field.fieldName}]`;
      const tag = field.tag || 'missing';

      // Determine highlight class
      let highlightClass = 'bg-yellow-100';
      if (tag === 'missing') highlightClass = 'bg-red-100 border-b-2 border-red-400';
      if (tag === 'manual override') highlightClass = 'bg-blue-100 border-b-2 border-blue-400';

      // Replace each placeholder pattern
      placeholders.forEach(placeholder => {
        const regex = new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
        processedHtml = processedHtml.replace(
          regex,
          `<span class="${highlightClass} px-1 rounded">${value}</span>`
        );
      });
    });

    return processedHtml;
  };

  // Load and convert DOCX template
  useEffect(() => {
    const loadTemplate = async () => {
      setLoading(true);
      setError(null);

      try {
        // Fetch the DOCX file
        const response = await fetch(templatePath);
        if (!response.ok) {
          throw new Error(`Failed to load template: ${response.statusText}`);
        }

        const arrayBuffer = await response.arrayBuffer();

        // Convert DOCX to HTML using mammoth
        const result = await mammoth.convertToHtml({ arrayBuffer });
        const html = result.value;

        // Replace placeholders with field values
        const processedHtml = replacePlaceholders(html);

        setHtmlContent(processedHtml);
      } catch (err) {
        console.error('Error loading template:', err);
        setError(err instanceof Error ? err.message : 'Failed to load template');
      } finally {
        setLoading(false);
      }
    };

    loadTemplate();
  }, [templatePath]);

  // Re-process HTML when fields change
  useEffect(() => {
    if (htmlContent && !loading) {
      // Reload template to get fresh HTML, then replace placeholders
      fetch(templatePath)
        .then(res => res.arrayBuffer())
        .then(arrayBuffer => mammoth.convertToHtml({ arrayBuffer }))
        .then(result => {
          const processedHtml = replacePlaceholders(result.value);
          setHtmlContent(processedHtml);
        })
        .catch(err => console.error('Error updating preview:', err));
    }
  }, [fields, templatePath]);

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 10, 150));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 10, 50));

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden flex flex-col h-[calc(100vh-250px)]">
      <div className="border-b border-gray-200 px-4 py-3 bg-gray-50 flex items-center justify-between">
        <h2 className="font-semibold text-gray-900">Document Preview (Live)</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={handleZoomOut}
            className="p-1.5 hover:bg-gray-200 rounded transition-colors"
            title="Zoom out"
          >
            <ZoomOut className="w-4 h-4 text-gray-600" />
          </button>
          <span className="text-sm text-gray-600 min-w-[4rem] text-center">{zoom}%</span>
          <button
            onClick={handleZoomIn}
            className="p-1.5 hover:bg-gray-200 rounded transition-colors"
            title="Zoom in"
          >
            <ZoomIn className="w-4 h-4 text-gray-600" />
          </button>
          <div className="w-px h-6 bg-gray-300 mx-2" />
          <button
            className="p-1.5 hover:bg-gray-200 rounded transition-colors"
            title="Download"
          >
            <Download className="w-4 h-4 text-gray-600" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6 bg-gray-100">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Loader2 className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-2" />
              <p className="text-sm text-gray-600">Loading template...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-red-600">
              <p className="font-semibold mb-2">Error loading template</p>
              <p className="text-sm">{error}</p>
              <p className="text-xs text-gray-500 mt-2">
                Make sure the template file exists at: {templatePath}
              </p>
            </div>
          </div>
    ) : (
      <div className="flex justify-center items-start">
        <div
          ref={previewRef}
          className="bg-white shadow-lg text-gray-900"
          style={{
            transform: `scale(${zoom / 100})`,
            transformOrigin: 'top center',
            width: '9.5in',
            fontSize: '12pt',
            lineHeight: '1.5',
            padding: '3rem 3rem 1rem 3rem',
          }}
        >
          <div
            dangerouslySetInnerHTML={{ __html: htmlContent }}
            className="docx-preview"
            style={{
              fontFamily: 'Times New Roman, serif',
            }}
          />
        </div>
      </div>
    )}
  </div>
</div>
);
}