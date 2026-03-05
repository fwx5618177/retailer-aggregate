/**
 * Route guard component that enforces authentication and role-based access.
 *
 * Usage:
 *   <Route path="/review" element={
 *     <ProtectedRoute requiredRoles={["REVIEWER", "ADMIN"]}>
 *       <ReviewPage />
 *     </ProtectedRoute>
 *   } />
 */
import type { ReactNode } from "react";
import { useAuth, type Role } from "./AuthContext";

interface ProtectedRouteProps {
  children: ReactNode;
  /** If provided, user must have at least one of these roles. */
  requiredRoles?: Role[];
}

export function ProtectedRoute({
  children,
  requiredRoles,
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, hasAnyRole, login } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-gray-500">正在验证身份...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="card p-8 text-center max-w-md">
          <h2 className="text-xl font-semibold mb-4">需要登录</h2>
          <p className="text-gray-500 mb-6">
            请登录后访问此页面。
          </p>
          <button
            onClick={login}
            className="btn-primary px-6 py-2 rounded-lg"
          >
            登录
          </button>
        </div>
      </div>
    );
  }

  if (requiredRoles && requiredRoles.length > 0 && !hasAnyRole(...requiredRoles)) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="card p-8 text-center max-w-md">
          <h2 className="text-xl font-semibold mb-4 text-danger">权限不足</h2>
          <p className="text-gray-500 mb-2">
            您的账户没有访问此页面的权限。
          </p>
          <p className="text-sm text-gray-400">
            所需角色: {requiredRoles.join(" / ")}
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
