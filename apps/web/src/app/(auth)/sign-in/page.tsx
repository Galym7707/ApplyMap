"use client";

import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { AlertCircle } from "lucide-react";

const schema = z.object({
  email: z.string().email("Please enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type FormData = z.infer<typeof schema>;

export default function SignInPage() {
  const { login, isLoginPending, loginError } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = (data: FormData) => {
    login({ email: data.email, password: data.password });
  };

  const apiError =
    loginError && "response" in (loginError as object)
      ? ((loginError as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? "Invalid email or password")
      : null;

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F9F8F6] px-4 py-12">
      <div className="w-full max-w-sm">
        <Link href="/" className="mb-8 flex items-center justify-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-navy-950">
            <span className="text-xs font-bold text-white">SL</span>
          </div>
          <span className="text-base font-semibold text-slate-900">SourceLock</span>
        </Link>

        <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-slate-900">Welcome back</h1>
            <p className="mt-1 text-sm text-slate-500">Sign in to your SourceLock account.</p>
          </div>

          {apiError && (
            <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-50 px-3 py-2.5 text-sm text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {apiError}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="amara@example.com"
                {...register("email")}
                className={errors.email ? "border-red-400" : ""}
              />
              {errors.email && (
                <p className="text-xs text-red-600">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <Link href="#" className="text-xs text-navy-700 hover:underline">
                  Forgot password?
                </Link>
              </div>
              <Input
                id="password"
                type="password"
                placeholder="Your password"
                {...register("password")}
                className={errors.password ? "border-red-400" : ""}
              />
              {errors.password && (
                <p className="text-xs text-red-600">{errors.password.message}</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full bg-navy-950 text-white hover:bg-navy-900"
              size="lg"
              disabled={isLoginPending}
            >
              {isLoginPending ? "Signing in..." : "Sign in"}
            </Button>
          </form>

          <p className="mt-5 text-center text-sm text-slate-500">
            Don&rsquo;t have an account?{" "}
            <Link href="/sign-up" className="font-medium text-navy-950 hover:underline">
              Sign up free
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
