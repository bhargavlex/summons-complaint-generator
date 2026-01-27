import { useState } from 'react';
import { DocumentPreview } from '../components/DocumentPreview';
import { ExtractedFieldsTable } from '../components/ExtractedFieldsTable';
import { ActionButtons } from '../components/ActionButtons';
import { ProgressBar } from '../components/ProgressBar';
import { Screen } from '../App';

export interface ExtractedField {
  id: string;
  fieldName: string;
  value: string;
  tag: 'extracted' | 'missing' | 'manual override';
}

const initialFields: ExtractedField[] = [
  { id: '1', fieldName: 'Plaintiff Name', value: 'JOHN DOE', tag: 'extracted' },
  { id: '2', fieldName: 'Defendant Name', value: '', tag: 'missing' },
  { id: '3', fieldName: 'Case Number', value: '23CV12345', tag: 'extracted' },
  { id: '4', fieldName: 'Court Name', value: 'Superior Court of California', tag: 'extracted' },
  { id: '5', fieldName: 'County', value: 'Los Angeles', tag: 'extracted' },
  { id: '6', fieldName: 'Attorney Firm', value: 'Smith & Associates LLP', tag: 'extracted' },
  { id: '7', fieldName: 'Attorney Address', value: '123 Legal Street, Suite 100', tag: 'extracted' },
  { id: '8', fieldName: 'City, State, ZIP', value: 'Los Angeles, CA 90012', tag: 'extracted' },
  { id: '9', fieldName: 'Attorney Phone', value: '(555) 123-4567', tag: 'extracted' },
  { id: '10', fieldName: 'Attorney Email', value: 'contact@smithlaw.com', tag: 'extracted' },
  { id: '11', fieldName: 'Filing Date', value: 'January 22, 2026', tag: 'extracted' },
  { id: '12', fieldName: 'Trial Date', value: '', tag: 'missing' },
];

interface ExtractionReviewProps {
  onNavigate: (screen: Screen) => void;
}

export function ExtractionReview({ onNavigate }: ExtractionReviewProps) {
  const [fields, setFields] = useState<ExtractedField[]>(initialFields);
  const [showPreview, setShowPreview] = useState(false);

  const updateField = (id: string, newValue: string) => {
    setFields(prevFields =>
      prevFields.map(field =>
        field.id === id
          ? { ...field, value: newValue, tag: 'manual override' as const }
          : field
      )
    );
  };

  const handleGeneratePreview = () => {
    setShowPreview(true);
  };

  return (
    <>
      <ProgressBar />
      <main className="container mx-auto px-6 py-8">
        <div className={`grid gap-6 ${showPreview ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1'}`}>
          {showPreview && (
            <DocumentPreview fields={fields} />
          )}
          <ExtractedFieldsTable
            fields={fields}
            updateField={updateField}
            onGeneratePreview={handleGeneratePreview}
            showPreview={showPreview}
          />
        </div>
        <ActionButtons onNavigate={onNavigate} />
      </main>
    </>
  );
}