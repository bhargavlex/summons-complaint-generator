import { useState } from "react";
import { DocumentUpload } from "./screens/DocumentUpload";
import { ExtractionReview } from "./screens/ExtractionReview";
import { Navigation } from "./components/Navigation";

export type Screen =
  | "upload"
  | "extraction"
  | "library";

export default function App() {
  const [currentScreen, setCurrentScreen] =
    useState<Screen>("upload");

  const renderScreen = () => {
    switch (currentScreen) {
      case "upload":
        return <DocumentUpload onNavigate={setCurrentScreen} />;
      case "extraction":
        return (
          <ExtractionReview onNavigate={setCurrentScreen} />
        );
      default:
        return <DocumentUpload onNavigate={setCurrentScreen} />;
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