import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { jwtVerify, SignJWT } from "jose";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const SECRET = new TextEncoder().encode(process.env.NEXTAUTH_SECRET);

interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  user: UserProfile;
}

interface RefreshResponse {
  access_token: string;
  refresh_token: string;
}

async function refreshAccessToken(refreshToken: string): Promise<TokenResponse | null> {
  try {
    const response = await fetch(`${API_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      return null;
    }

    const data: RefreshResponse = await response.json();
    
    const userResponse = await fetch(`${API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${data.access_token}` },
    });

    if (!userResponse.ok) {
      return null;
    }

    const user: UserProfile = await userResponse.json();

    return {
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      user,
    };
  } catch {
    return null;
  }
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Credentials({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        try {
          const response = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          });

          if (!response.ok) {
            return null;
          }

          const data: TokenResponse = await response.json();

          return {
            id: data.user.id,
            email: data.user.email,
            name: data.user.full_name,
            accessToken: data.access_token,
            refreshToken: data.refresh_token,
          };
        } catch {
          return null;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.accessToken = (user as Record<string, unknown>).accessToken;
        token.refreshToken = (user as Record<string, unknown>).refreshToken;
      }

      if (token.accessToken) {
        try {
          const { payload } = await jwtVerify(token.accessToken as string, SECRET, {
            algorithms: ["HS256"],
          });
          const exp = payload.exp as number;
          const now = Math.floor(Date.now() / 1000);
          
          if (exp && exp - now < 300 && token.refreshToken) {
            const refreshed = await refreshAccessToken(token.refreshToken as string);
            if (refreshed) {
              token.accessToken = refreshed.access_token;
              token.refreshToken = refreshed.refresh_token;
            }
          }
        } catch {
          if (token.refreshToken) {
            const refreshed = await refreshAccessToken(token.refreshToken as string);
            if (refreshed) {
              token.accessToken = refreshed.access_token;
              token.refreshToken = refreshed.refresh_token;
            } else {
              return null;
            }
          } else {
            return null;
          }
        }
      }

      return token;
    },
    async session({ session, token }) {
      if (token?.accessToken) {
        (session as unknown as Record<string, unknown>).accessToken = token.accessToken;
      }
      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
  session: {
    strategy: "jwt",
    maxAge: 30 * 60,
  },
});
