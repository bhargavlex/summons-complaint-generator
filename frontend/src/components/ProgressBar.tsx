
export function ProgressBar() {
  const steps = [
    { id: 1, name: 'Upload Documents', completed: true },
    { id: 2, name: 'Extract Fields', completed: true },
    { id: 3, name: 'Review & Edit', completed: false, current: true },
    { id: 4, name: 'Finalize S&C', completed: false },
  ];

  const completedSteps = steps.filter(s => s.completed).length;
  const progressPercentage = Math.round((completedSteps / steps.length) * 100);

  return (
    <div className="bg-white border-b border-gray-200 shadow-sm">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-700">Summons & Complaint Progress</h3>
          <span className="text-sm font-medium text-gray-700">{progressPercentage}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-500"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>
    </div>
  );
}
