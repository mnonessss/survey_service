import { createContext } from "react";

export type AuthStatus = "loading" | "authenticated" | "denied";

export type AuthContextValue = {
  status: AuthStatus;
  userEmail: string;
  error: string;
};

export const AuthContext = createContext<AuthContextValue>({
  status: "loading",
  userEmail: "",
  error: "",
});
