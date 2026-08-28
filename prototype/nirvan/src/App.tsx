import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppProvider } from "./context/AppContext";
import ProtectedRoute, { ProjectRequired } from "./components/ProtectedRoute";

import Landing from "./pages/Landing";
import About from "./pages/About";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import HomeDashboard from "./pages/HomeDashboard";
import CategorySelection from "./pages/CategorySelection";
import ProjectProfile from "./pages/ProjectProfile";
import ApprovalRoadmapPage from "./pages/ApprovalRoadmapPage";
import ApprovalDetails from "./pages/ApprovalDetails";
import DocumentVault from "./pages/DocumentVault";
import ApplicationTracker from "./pages/ApplicationTracker";
import SmartAlerts from "./pages/SmartAlerts";
import SchemeMatcher from "./pages/SchemeMatcher";
import DepartmentsToContact from "./pages/DepartmentsToContact";

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          <Route path="/dashboard" element={<ProtectedRoute><HomeDashboard /></ProtectedRoute>} />
          <Route path="/select/:category" element={<ProtectedRoute><CategorySelection /></ProtectedRoute>} />
          <Route path="/project" element={<ProtectedRoute><ProjectProfile /></ProtectedRoute>} />

          <Route
            path="/roadmap"
            element={
              <ProtectedRoute>
                <ApprovalRoadmapPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/roadmap/:id"
            element={
              <ProtectedRoute>
                <ProjectRequired>
                  <ApprovalDetails />
                </ProjectRequired>
              </ProtectedRoute>
            }
          />
          <Route path="/documents" element={<ProtectedRoute><DocumentVault /></ProtectedRoute>} />
          <Route path="/applications" element={<ProtectedRoute><ApplicationTracker /></ProtectedRoute>} />
          <Route path="/alerts" element={<ProtectedRoute><SmartAlerts /></ProtectedRoute>} />
          <Route path="/schemes" element={<ProtectedRoute><SchemeMatcher /></ProtectedRoute>} />

          <Route path="/departments" element={<ProtectedRoute><DepartmentsToContact /></ProtectedRoute>} />

          <Route path="*" element={<Landing />} />
        </Routes>
      </BrowserRouter>
    </AppProvider>
  );
}
