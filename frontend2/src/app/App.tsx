import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppProviders } from "./providers/AppProviders.tsx";
import { AppLayout } from "../components/layout/AppLayout.tsx";
import { AuthLayout } from "../components/layout/AuthLayout.tsx";
import { ErrorBoundary } from "../components/ErrorBoundary.tsx";
import { useAuth } from "../hooks/useAuth.ts";
import { DashboardPage } from "../pages/Dashboard.tsx";
import { ResumeUploadPage } from "../pages/ResumeUpload.tsx";
import { AnalysisPage } from "../pages/Analysis.tsx";
import { TimelinePage } from "../pages/Timeline.tsx";
import { JobRecommendationsPage } from "../pages/JobRecommendations.tsx";
import { YouTubeRecommendationsPage } from "../pages/YouTubeRecommendations.tsx";
import { LoginPage } from "../pages/Login.tsx";
import { SignupPage } from "../pages/Signup.tsx";
import type { ReactElement } from "react";

const ProtectedRoute = ({ children }: { children: ReactElement }) => {
  const { isAuthenticated, isInitialized } = useAuth();

  if (!isInitialized) {
    return null; // Show nothing while checking auth status
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

const AppRouter = () => (
  <Routes>
    <Route
      path="/login"
      element={
        <AuthLayout>
          <LoginPage />
        </AuthLayout>
      }
    />
    <Route
      path="/signup"
      element={
        <AuthLayout>
          <SignupPage />
        </AuthLayout>
      }
    />
    <Route
      element={
        <ProtectedRoute>
          <AppLayout />
        </ProtectedRoute>
      }
    >
      <Route index element={<DashboardPage />} />
      <Route path="resume" element={<ResumeUploadPage />} />
      <Route path="analysis" element={<AnalysisPage />} />
      <Route path="timeline" element={<TimelinePage />} />
      <Route path="jobs" element={<JobRecommendationsPage />} />
      <Route path="youtube" element={<YouTubeRecommendationsPage />} />
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
);

export const App = () => (
  <ErrorBoundary>
    <AppProviders>
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
    </AppProviders>
  </ErrorBoundary>
);

export default App;
