"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { authApi } from "@/lib/api";
import { useRouter } from "next/navigation";
import type { User } from "@/types";

export function useAuth() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: user, isLoading } = useQuery<User | null>({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      try {
        if (typeof window !== "undefined" && !localStorage.getItem("sourcelock_token")) {
          return null;
        }
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
      if (token) localStorage.setItem("sourcelock_token", token);
      queryClient.setQueryData(["auth", "me"], res.data.data?.user);
      router.push("/dashboard");
    },
  });

  const signupMutation = useMutation({
    mutationFn: authApi.signup,
    onSuccess: (res) => {
      const token = res.data.data?.access_token;
      if (token) localStorage.setItem("sourcelock_token", token);
      queryClient.setQueryData(["auth", "me"], res.data.data?.user);
      router.push("/onboarding");
    },
  });

  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      localStorage.removeItem("sourcelock_token");
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
