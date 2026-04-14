"use client";

import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApplyMapLogo } from "@/components/brand/ApplyMapLogo";
import { useAuth } from "@/hooks/useAuth";
import { AlertCircle } from "lucide-react";

const schema = z
  .object({
    full_name: z.string().min(2, "Name must be at least 2 characters"),
    email: z.string().email("Please enter a valid email"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string(),
  })
  .refine((d) => d.password === d.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type FormData = z.infer<typeof schema>;

export default function SignUpPage() {
  const { signup, isSignupPending, signupError } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = (data: FormData) => {
    signup({ email: data.email, password: data.password, full_name: data.full_name });
  };

  const apiError =
    signupError && "response" in (signupError as object)
      ? ((signupError as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? "Sign up failed")
      : null;

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F9F8F6] px-5 py-12">
      <div className="w-full max-w-xl">
        {/* Logo */}
        <Link href="/" className="mb-10 flex items-center justify-center gap-3">
          <ApplyMapLogo className="h-16" />
        </Link>

        <div className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm sm:p-10 md:p-12">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-slate-900">Create your account</h1>
            <p className="mt-2 text-base text-slate-500">
              Start mapping your applications for free.
            </p>
          </div>

          {apiError && (
            <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-50 px-3 py-2.5 text-sm text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {apiError}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="full_name" className="text-base">Full name</Label>
              <Input
                id="full_name"
                placeholder="Amara Osei"
                {...register("full_name")}
                className={`h-12 px-4 text-base ${errors.full_name ? "border-red-400" : ""}`}
              />
              {errors.full_name && (
                <p className="text-xs text-red-600">{errors.full_name.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-base">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="amara@example.com"
                {...register("email")}
                className={`h-12 px-4 text-base ${errors.email ? "border-red-400" : ""}`}
              />
              {errors.email && (
                <p className="text-xs text-red-600">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-base">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="At least 8 characters"
                {...register("password")}
                className={`h-12 px-4 text-base ${errors.password ? "border-red-400" : ""}`}
              />
              {errors.password && (
                <p className="text-xs text-red-600">{errors.password.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-base">Confirm password</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="Re-enter your password"
                {...register("confirmPassword")}
                className={`h-12 px-4 text-base ${errors.confirmPassword ? "border-red-400" : ""}`}
              />
              {errors.confirmPassword && (
                <p className="text-xs text-red-600">{errors.confirmPassword.message}</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full bg-navy-950 text-base text-white hover:bg-navy-900"
              size="xl"
              disabled={isSignupPending}
            >
              {isSignupPending ? "Creating account..." : "Create account"}
            </Button>
          </form>

          <p className="mt-6 text-center text-base text-slate-500">
            Already have an account?{" "}
            <Link href="/sign-in" className="font-medium text-navy-950 hover:underline">
              Sign in
            </Link>
          </p>
        </div>

        <p className="mt-4 text-center text-xs text-slate-400">
          By creating an account you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </div>
  );
}
