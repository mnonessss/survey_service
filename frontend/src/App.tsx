import { Route, Routes } from "react-router-dom";
import { AuthProvider, RequireAuth } from "./auth/AuthContext";
import { AppLayout } from "./components/AppLayout";
import Dashboard from "./pages/Dashboard";
import SurveyEditor from "./pages/SurveyEditor";
import SurveyResponses from "./pages/SurveyResponses";
import PublicSurvey from "./pages/PublicSurvey";

function Protected({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <AppLayout>{children}</AppLayout>
    </RequireAuth>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/s/:token" element={<PublicSurvey />} />
        <Route
          path="/"
          element={
            <Protected>
              <Dashboard />
            </Protected>
          }
        />
        <Route
          path="/surveys/:id"
          element={
            <Protected>
              <SurveyEditor />
            </Protected>
          }
        />
        <Route
          path="/surveys/:id/responses"
          element={
            <Protected>
              <SurveyResponses />
            </Protected>
          }
        />
      </Routes>
    </AuthProvider>
  );
}
