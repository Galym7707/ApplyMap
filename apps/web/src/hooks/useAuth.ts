"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { authApi, clearStoredAuthToken, getStoredAuthToken, setStoredAuthToken } from "@/lib/api";
import { useRouter } from "next/navigation";
import type { User } from "@/types";

export function useAuth() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: user, isLoading } = useQuery<User | null>({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      if (typeof window !== "undefined" && !getStoredAuthToken()) {
        return null;
      }
      try {
        const res = await authApi.me();
        return res.data.data as User;
      } catch {
        return null;
      }
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (res) => {
      const token = res.data.data?.access_token;
      if (token) setStoredAuthToken(token);
      queryClient.setQueryData(["auth", "me"], res.data.data?.user);
      router.push("/dashboard");
    },
  });

  const signupMutation = useMutation({
    mutationFn: authApi.signup,
    onSuccess: (res) => {
      const token = res.data.data?.access_token;
      if (token) setStoredAuthToken(token);
      queryClient.setQueryData(["auth", "me"], res.data.data?.user);
      router.push("/onboarding");
    },
  });

  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      clearStoredAuthToken();
      queryClient.clear();
      router.push("/");
    },
  });

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    login: loginMutation.mutate,
    signup: signupMutation.mutate,
    logout: logoutMutation.mutate,
    loginError: loginMutation.error,
    signupError: signupMutation.error,
    isLoginPending: loginMutation.isPending,
    isSignupPending: signupMutation.isPending,
  };
}
