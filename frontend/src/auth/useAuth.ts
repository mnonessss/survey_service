import { useContext } from "react";
import { AuthContext } from "./authContextState";

export function useAuth() {
  return useContext(AuthContext);
}
