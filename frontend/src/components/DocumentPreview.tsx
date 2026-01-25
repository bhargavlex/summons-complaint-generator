import { useState } from 'react';
import { ZoomIn, ZoomOut, Download } from 'lucide-react';
import { ExtractedField } from '../App';

interface DocumentPreviewProps {
  fields: ExtractedField[];
}

export function DocumentPreview({ fields }: DocumentPreviewProps) {
  const [zoom, setZoom] = useState(80);

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 10, 150));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 10, 50));

  const getFieldValue = (fieldName: string): string => {
    const field = fields.find(f => f.fieldName === fieldName);
    return field?.value || '';
  };

  const getFieldTag = (fieldName: string): string => {
    const field = fields.find(f => f.fieldName === fieldName);
    return field?.tag || 'missing';
  };

  const getHighlightClass = (fieldName: string): string => {
    const tag = getFieldTag(fieldName);
    if (tag === 'missing') return 'bg-red-100 border-b-2 border-red-400';
    if (tag === 'manual override') return 'bg-blue-100 border-b-2 border-blue-400';
    return 'bg-yellow-100';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden flex flex-col h-[calc(100vh-280px)]">
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
        <div className="flex justify-center items-start min-h-full">
          <div
            className="bg-white shadow-lg p-12 text-gray-900"
            style={{
              transform: `scale(${zoom / 100})`,
              transformOrigin: 'top center',
              width: '8.5in',
              minHeight: '11in',
              fontSize: '12pt',
              lineHeight: '1.5',
            }}
          >
            {/* Document Header */}
            <div className="text-center mb-8">
              <div className="font-semibold">
                SUPERIOR COURT OF THE STATE OF{' '}
                <span className={getHighlightClass('Court Name')}>
                  {getFieldValue('Court Name').toUpperCase().replace('SUPERIOR COURT OF CALIFORNIA', 'CALIFORNIA')}
                </span>
              </div>
              <div className="font-semibold">
                COUNTY OF{' '}
                <span className={getHighlightClass('County')}>
                  {getFieldValue('County').toUpperCase()}
                </span>
              </div>
            </div>

            {/* Case Information */}
            <div className="border-t-2 border-b-2 border-black py-4 mb-6">
              <div className="flex justify-between">
                <div className="flex-1">
                  <div className="mb-2">
                    <span className={getHighlightClass('Plaintiff Name')}>
                      {getFieldValue('Plaintiff Name') || '[PLAINTIFF NAME]'}
                    </span>, an individual,
                  </div>
                  <div className="ml-16 mb-4">Plaintiff,</div>
                  <div className="ml-8">vs.</div>
                  <div className="mt-4 mb-2">
                    <span className={getHighlightClass('Defendant Name')}>
                      {getFieldValue('Defendant Name') || '[DEFENDANT NAME]'}
                    </span>, a California corporation; and DOES 1 through 10, inclusive,
                  </div>
                  <div className="ml-16">Defendants.</div>
                </div>
                <div className="w-64 pl-4 border-l-2 border-black">
                  <div className="mb-2">
                    <div className="text-sm">Case No.</div>
                    <div className={`font-semibold ${getHighlightClass('Case Number')}`}>
                      {getFieldValue('Case Number') || '[CASE NUMBER]'}
                    </div>
                  </div>
                  <div className="my-4">
                    <div className="font-semibold">SUMMONS</div>
                  </div>
                  <div className="text-sm space-y-1">
                    <div>
                      Trial Date:{' '}
                      <span className={getHighlightClass('Trial Date')}>
                        {getFieldValue('Trial Date') || '[NOT SET]'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Summons Content */}
            <div className="space-y-4">
              <div>
                <div className="font-semibold mb-2">NOTICE TO DEFENDANT:</div>
                <p className="mb-2">
                  <span className={getHighlightClass('Defendant Name')}>
                    {getFieldValue('Defendant Name') || '[DEFENDANT NAME]'}
                  </span>
                </p>
              </div>

              <p>
                YOU ARE BEING SUED BY PLAINTIFF:{' '}
                <span className={getHighlightClass('Plaintiff Name')}>
                  {getFieldValue('Plaintiff Name') || '[PLAINTIFF NAME]'}
                </span>
              </p>

              <div className="border border-black p-4 my-4">
                <p className="font-semibold mb-2">NOTICE!</p>
                <p className="text-sm">
                  You have been sued. The court may decide against you without your being heard unless you respond within 30 days. Read the information below.
                </p>
              </div>

              <p>
                You have <strong>30 CALENDAR DAYS</strong> after this summons and legal papers are served on you to file a written response at this court and have a copy served on the plaintiff. A letter or phone call will not protect you. Your written response must be in proper legal form if you want the court to hear your case.
              </p>

              <p>
                There may be a court form that you can use for your response. You can find these court forms and more information at the California Courts Online Self-Help Center (www.courtinfo.ca.gov/selfhelp), your county law library, or the courthouse nearest you.
              </p>

              <div className="mt-8">
                <div className="mb-2">
                  Date:{' '}
                  <span className={getHighlightClass('Filing Date')}>
                    {getFieldValue('Filing Date') || '[DATE]'}
                  </span>
                </div>
                <div className="mb-2">Clerk, by ________________, Deputy</div>
              </div>

              <div className="mt-8 pt-4 border-t border-gray-300">
                <div className="font-semibold mb-2">Attorney for Plaintiff:</div>
                <div>
                  <span className={getHighlightClass('Attorney Firm')}>
                    {getFieldValue('Attorney Firm') || '[ATTORNEY FIRM]'}
                  </span>
                </div>
                <div>
                  <span className={getHighlightClass('Attorney Address')}>
                    {getFieldValue('Attorney Address') || '[ADDRESS]'}
                  </span>
                </div>
                <div>
                  <span className={getHighlightClass('City, State, ZIP')}>
                    {getFieldValue('City, State, ZIP') || '[CITY, STATE, ZIP]'}
                  </span>
                </div>
                <div>
                  Phone:{' '}
                  <span className={getHighlightClass('Attorney Phone')}>
                    {getFieldValue('Attorney Phone') || '[PHONE]'}
                  </span>
                </div>
                <div>
                  Email:{' '}
                  <span className={getHighlightClass('Attorney Email')}>
                    {getFieldValue('Attorney Email') || '[EMAIL]'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}