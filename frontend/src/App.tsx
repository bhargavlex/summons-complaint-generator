import { useState } from "react";
import { DocumentUpload } from "./screens/DocumentUpload";
import { ExtractionReview } from "./screens/ExtractionReview";
import { Navigation } from "./components/Navigation";

export type Screen =
  | "upload"
  | "extraction"
  | "library";

export interface ExtractedField {
  id: string;
  fieldName: string;
  value: string;
  tag: "extracted" | "missing" | "manual override";
}

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>("upload");
  const [sessionUuid, setSessionUuid] = useState<string | null>(null);

  const renderScreen = () => {
    switch (currentScreen) {
      case "upload":
        return (
          <DocumentUpload
            onNavigate={setCurrentScreen}
            onSessionCreated={setSessionUuid}
          />
        );
      case "extraction":
        return (
          <ExtractionReview
            onNavigate={setCurrentScreen}
            sessionUuid={sessionUuid}
          />
        );
      default:
        return <DocumentUpload onNavigate={setCurrentScreen} onSessionCreated={setSessionUuid} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation
        currentScreen={currentScreen}
        onNavigate={setCurrentScreen}
      />
      {renderScreen()}
    </div>
  );
}