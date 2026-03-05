/**
 * OIDC Authentication Context.
 *
 * Provides login/logout/token-refresh and role-based access control.
 * Integrates with Keycloak via standard OIDC Authorization Code + PKCE flow.
 *
 * In local dev (VITE_AUTH_DISABLED=true), authentication is bypassed and all
 * users get ADMIN role for convenience.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

/* ─── Types ─── */

export type Role = "VIEWER" | "REVIEWER" | "ADMIN";

export interface AuthUser {
  sub: string;
  name: string;
  email?: string;
  roles: Role[];
}

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  login: () => void;
  logout: () => void;
  hasRole: (role: Role) => boolean;
  hasAnyRole: (...roles: Role[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/* ─── OIDC Config ─── */

const OIDC_AUTHORITY =
  import.meta.env.VITE_OIDC_AUTHORITY ??
  "http://localhost:8180/realms/sea-retailer";
const OIDC_CLIENT_ID =
  import.meta.env.VITE_OIDC_CLIENT_ID ?? "sea-retailer-web";
const OIDC_REDIRECT_URI =
  import.meta.env.VITE_OIDC_REDIRECT_URI ?? window.location.origin;
const AUTH_DISABLED = import.meta.env.VITE_AUTH_DISABLED === "true";

/* ─── Token storage keys ─── */

const TOKEN_KEY = "access_token";
const REFRESH_KEY = "refresh_token";
const USER_KEY = "auth_user";

/* ─── Helpers ─── */

/** Generate a random code verifier for PKCE. */
function generateCodeVerifier(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return btoa(String.fromCharCode(...array))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=/g, "");
}

/** SHA-256 hash for PKCE code challenge. */
async function generateCodeChallenge(verifier: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=/g, "");
}

/** Parse JWT payload without verification (client-side display only). */
function parseJwtPayload(token: string): Record<string, unknown> {
  try {
    const base64Url = token.split(".")[1] ?? "";
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(base64));
  } catch {
    return {};
  }
}

/** Extract user info from Keycloak JWT. */
function extractUser(token: string): AuthUser {
  const payload = parseJwtPayload(token);
  const realmAccess = (payload.realm_access as { roles?: string[] }) ?? {};
  const roles = (realmAccess.roles ?? [])
    .map((r: string) => r.toUpperCase())
    .filter((r): r is Role => ["VIEWER", "REVIEWER", "ADMIN"].includes(r));

  return {
    sub: (payload.sub as string) ?? "unknown",
    name:
      (payload.preferred_username as string) ??
      (payload.name as string) ??
      "User",
    email: payload.email as string | undefined,
    roles: roles.length > 0 ? roles : ["VIEWER"],
  };
}

/* ─── Local dev mock user ─── */

const LOCAL_MOCK_USER: AuthUser = {
  sub: "local-dev",
  name: "Local Developer",
  email: "dev@localhost",
  roles: ["ADMIN", "REVIEWER", "VIEWER"],
};

/* ─── Provider ─── */

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(() => {
    if (AUTH_DISABLED) {
      return {
        user: LOCAL_MOCK_USER,
        accessToken: null,
        isAuthenticated: true,
        isLoading: false,
      };
    }
    const savedToken = localStorage.getItem(TOKEN_KEY);
    const savedUser = localStorage.getItem(USER_KEY);
    if (savedToken && savedUser) {
      return {
        user: JSON.parse(savedUser) as AuthUser,
        accessToken: savedToken,
        isAuthenticated: true,
        isLoading: false,
      };
    }
    return {
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: true,
    };
  });

  /* ── Handle OIDC callback ── */
  useEffect(() => {
    if (AUTH_DISABLED) return;

    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const storedVerifier = sessionStorage.getItem("pkce_code_verifier");

    if (code && storedVerifier) {
      // Exchange authorization code for tokens
      const exchangeCode = async () => {
        try {
          const tokenUrl = `${OIDC_AUTHORITY}/protocol/openid-connect/token`;
          const body = new URLSearchParams({
            grant_type: "authorization_code",
            client_id: OIDC_CLIENT_ID,
            redirect_uri: OIDC_REDIRECT_URI,
            code,
            code_verifier: storedVerifier,
          });

          const resp = await fetch(tokenUrl, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body,
          });

          if (!resp.ok) {
            throw new Error(`Token exchange failed: ${resp.status}`);
          }

          const data = await resp.json();
          const accessToken = data.access_token as string;
          const refreshToken = data.refresh_token as string | undefined;

          const user = extractUser(accessToken);

          localStorage.setItem(TOKEN_KEY, accessToken);
          if (refreshToken) localStorage.setItem(REFRESH_KEY, refreshToken);
          localStorage.setItem(USER_KEY, JSON.stringify(user));
          sessionStorage.removeItem("pkce_code_verifier");

          setState({
            user,
            accessToken,
            isAuthenticated: true,
            isLoading: false,
          });

          // Clean URL
          window.history.replaceState({}, "", window.location.pathname);
        } catch (err) {
          console.error("[auth] Token exchange error:", err);
          setState((s) => ({ ...s, isLoading: false }));
        }
      };
      exchangeCode();
    } else {
      setState((s) => ({ ...s, isLoading: false }));
    }
  }, []);

  /* ── Token refresh ── */
  useEffect(() => {
    if (AUTH_DISABLED || !state.accessToken) return;

    const payload = parseJwtPayload(state.accessToken);
    const exp = (payload.exp as number) ?? 0;
    // Refresh 60 seconds before expiry
    const refreshAt = exp * 1000 - Date.now() - 60_000;

    if (refreshAt <= 0) return;

    const timer = setTimeout(async () => {
      const refreshToken = localStorage.getItem(REFRESH_KEY);
      if (!refreshToken) return;

      try {
        const tokenUrl = `${OIDC_AUTHORITY}/protocol/openid-connect/token`;
        const body = new URLSearchParams({
          grant_type: "refresh_token",
          client_id: OIDC_CLIENT_ID,
          refresh_token: refreshToken,
        });

        const resp = await fetch(tokenUrl, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body,
        });

        if (!resp.ok) throw new Error("Refresh failed");

        const data = await resp.json();
        const newAccessToken = data.access_token as string;
        const newRefreshToken =
          (data.refresh_token as string | undefined) ?? refreshToken;
        const user = extractUser(newAccessToken);

        localStorage.setItem(TOKEN_KEY, newAccessToken);
        localStorage.setItem(REFRESH_KEY, newRefreshToken);
        localStorage.setItem(USER_KEY, JSON.stringify(user));

        setState({
          user,
          accessToken: newAccessToken,
          isAuthenticated: true,
          isLoading: false,
        });
      } catch (err) {
        console.error("[auth] Token refresh error:", err);
        // Force re-login
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_KEY);
        localStorage.removeItem(USER_KEY);
        setState({
          user: null,
          accessToken: null,
          isAuthenticated: false,
          isLoading: false,
        });
      }
    }, refreshAt);

    return () => clearTimeout(timer);
  }, [state.accessToken]);

  /* ── Login ── */
  const login = useCallback(async () => {
    if (AUTH_DISABLED) return;

    const verifier = generateCodeVerifier();
    const challenge = await generateCodeChallenge(verifier);
    sessionStorage.setItem("pkce_code_verifier", verifier);

    const authUrl = new URL(
      `${OIDC_AUTHORITY}/protocol/openid-connect/auth`,
    );
    authUrl.searchParams.set("response_type", "code");
    authUrl.searchParams.set("client_id", OIDC_CLIENT_ID);
    authUrl.searchParams.set("redirect_uri", OIDC_REDIRECT_URI);
    authUrl.searchParams.set("scope", "openid profile email");
    authUrl.searchParams.set("code_challenge", challenge);
    authUrl.searchParams.set("code_challenge_method", "S256");

    window.location.href = authUrl.toString();
  }, []);

  /* ── Logout ── */
  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);

    setState({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
    });

    if (!AUTH_DISABLED) {
      const logoutUrl = `${OIDC_AUTHORITY}/protocol/openid-connect/logout?post_logout_redirect_uri=${encodeURIComponent(OIDC_REDIRECT_URI)}&client_id=${OIDC_CLIENT_ID}`;
      window.location.href = logoutUrl;
    }
  }, []);

  /* ── Role checks ── */
  const hasRole = useCallback(
    (role: Role) => state.user?.roles.includes(role) ?? false,
    [state.user],
  );

  const hasAnyRole = useCallback(
    (...roles: Role[]) => roles.some((r) => state.user?.roles.includes(r)),
    [state.user],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      login,
      logout,
      hasRole,
      hasAnyRole,
    }),
    [state, login, logout, hasRole, hasAnyRole],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/* ─── Hook ─── */

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
