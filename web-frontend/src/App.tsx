import { Routes, Route, Navigate } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { OverviewPage } from "./pages/OverviewPage";
import { TopItemsPage } from "./pages/TopItemsPage";
import { ItemDetailPage } from "./pages/ItemDetailPage";
import { AlertsPage } from "./pages/AlertsPage";
import { ReviewPage } from "./pages/ReviewPage";

export default function App() {
  return (
    <AppLayout>
      <Routes>
        {/* Read-only pages: VIEWER / REVIEWER / ADMIN */}
        <Route
          path="/"
          element={
            <ProtectedRoute requiredRoles={["VIEWER", "REVIEWER", "ADMIN"]}>
              <OverviewPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/top-items"
          element={
            <ProtectedRoute requiredRoles={["VIEWER", "REVIEWER", "ADMIN"]}>
              <TopItemsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/items/:platform/:itemId"
          element={
            <ProtectedRoute requiredRoles={["VIEWER", "REVIEWER", "ADMIN"]}>
              <ItemDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/alerts"
          element={
            <ProtectedRoute requiredRoles={["VIEWER", "REVIEWER", "ADMIN"]}>
              <AlertsPage />
            </ProtectedRoute>
          }
        />

        {/* Review page: REVIEWER / ADMIN only */}
        <Route
          path="/review"
          element={
            <ProtectedRoute requiredRoles={["REVIEWER", "ADMIN"]}>
              <ReviewPage />
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppLayout>
  );
}
