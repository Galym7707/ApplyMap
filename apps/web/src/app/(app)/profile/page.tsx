"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { profileApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";

type ProfileForm = {
  full_name: string;
  country: string;
  graduation_year: string;
  curriculum: string;
  intended_major: string;
  sat_score: string;
  sat_math: string;
  sat_ebrw: string;
  act_score: string;
  ielts_score: string;
  ielts_listening: string;
  ielts_reading: string;
  ielts_writing: string;
  ielts_speaking: string;
  toefl_score: string;
  toefl_reading: string;
  toefl_listening: string;
  toefl_speaking: string;
  toefl_writing: string;
  duolingo_score: string;
  a_level_subjects: string;
  a_level_predicted: string;
  ap_subjects: string;
  ib_predicted_score: string;
  unt_score: string;
  nis_grade12_certificate_gpa: string;
  budget_range: string;
};

function numberOrUndefined(value: string) {
  return value.trim() ? Number(value) : undefined;
}

export default function ProfilePage() {
  const queryClient = useQueryClient();
  const form = useForm<ProfileForm>({
    defaultValues: {
      full_name: "",
      country: "",
      graduation_year: "",
      curriculum: "",
      intended_major: "",
      sat_score: "",
      sat_math: "",
      sat_ebrw: "",
      act_score: "",
      ielts_score: "",
      ielts_listening: "",
      ielts_reading: "",
      ielts_writing: "",
      ielts_speaking: "",
      toefl_score: "",
      toefl_reading: "",
      toefl_listening: "",
      toefl_speaking: "",
      toefl_writing: "",
      duolingo_score: "",
      a_level_subjects: "",
      a_level_predicted: "",
      ap_subjects: "",
      ib_predicted_score: "",
      unt_score: "",
      nis_grade12_certificate_gpa: "",
      budget_range: "",
    },
  });

  const { data, isLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: () => profileApi.get(),
  });

  useEffect(() => {
    const payload = data?.data?.data;
    if (!payload) return;
    const { user, profile } = payload;
    form.reset({
      full_name: user?.full_name ?? "",
      country: user?.country ?? "",
      graduation_year: profile?.graduation_year ? String(profile.graduation_year) : "",
      curriculum: profile?.curriculum ?? "",
      intended_major: profile?.intended_major ?? "",
      sat_score: profile?.sat_score ? String(profile.sat_score) : "",
      sat_math: profile?.sat_math ? String(profile.sat_math) : "",
      sat_ebrw: profile?.sat_ebrw ? String(profile.sat_ebrw) : "",
      act_score: profile?.act_score ? String(profile.act_score) : "",
      ielts_score: profile?.ielts_score ?? "",
      ielts_listening: profile?.ielts_listening ?? "",
      ielts_reading: profile?.ielts_reading ?? "",
      ielts_writing: profile?.ielts_writing ?? "",
      ielts_speaking: profile?.ielts_speaking ?? "",
      toefl_score: profile?.toefl_score ? String(profile.toefl_score) : "",
      toefl_reading: profile?.toefl_reading ? String(profile.toefl_reading) : "",
      toefl_listening: profile?.toefl_listening ? String(profile.toefl_listening) : "",
      toefl_speaking: profile?.toefl_speaking ? String(profile.toefl_speaking) : "",
      toefl_writing: profile?.toefl_writing ? String(profile.toefl_writing) : "",
      duolingo_score: profile?.duolingo_score ? String(profile.duolingo_score) : "",
      a_level_subjects: profile?.a_level_subjects ?? "",
      a_level_predicted: profile?.a_level_predicted ?? "",
      ap_subjects: profile?.ap_subjects ?? "",
      ib_predicted_score: profile?.ib_predicted_score ? String(profile.ib_predicted_score) : "",
      unt_score: profile?.unt_score ? String(profile.unt_score) : "",
      nis_grade12_certificate_gpa: profile?.nis_grade12_certificate_gpa ?? "",
      budget_range: profile?.budget_range ?? "",
    });
  }, [data, form]);

  const saveMutation = useMutation({
    mutationFn: async (values: ProfileForm) => {
      await profileApi.updateUser({
        full_name: values.full_name || undefined,
        country: values.country || undefined,
      });
      return profileApi.update({
        graduation_year: numberOrUndefined(values.graduation_year),
        curriculum: values.curriculum || undefined,
        intended_major: values.intended_major || undefined,
        sat_score: numberOrUndefined(values.sat_score),
        sat_math: numberOrUndefined(values.sat_math),
        sat_ebrw: numberOrUndefined(values.sat_ebrw),
        act_score: numberOrUndefined(values.act_score),
        ielts_score: values.ielts_score || undefined,
        ielts_listening: values.ielts_listening || undefined,
        ielts_reading: values.ielts_reading || undefined,
        ielts_writing: values.ielts_writing || undefined,
        ielts_speaking: values.ielts_speaking || undefined,
        toefl_score: numberOrUndefined(values.toefl_score),
        toefl_reading: numberOrUndefined(values.toefl_reading),
        toefl_listening: numberOrUndefined(values.toefl_listening),
        toefl_speaking: numberOrUndefined(values.toefl_speaking),
        toefl_writing: numberOrUndefined(values.toefl_writing),
        duolingo_score: numberOrUndefined(values.duolingo_score),
        a_level_subjects: values.a_level_subjects || undefined,
        a_level_predicted: values.a_level_predicted || undefined,
        ap_subjects: values.ap_subjects || undefined,
        ib_predicted_score: numberOrUndefined(values.ib_predicted_score),
        unt_score: numberOrUndefined(values.unt_score),
        nis_grade12_certificate_gpa: values.nis_grade12_certificate_gpa || undefined,
        budget_range: values.budget_range || undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      toast.success("Profile saved");
    },
    onError: () => toast.error("Profile could not be saved"),
  });

  if (isLoading) {
    return (
      <div className="p-8">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="mt-6 h-96 max-w-5xl rounded-3xl" />
      </div>
    );
  }

  return (
    <div className="bg-[#f7f5ef] px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Student profile</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">Your saved context</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-500">
            Keep this current. The Chancellor uses it for university fit, exam advice, and funding realism.
          </p>
        </div>

        <form onSubmit={form.handleSubmit((values) => saveMutation.mutate(values))} className="space-y-6">
          <section className="rounded-[28px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)]">
            <h2 className="text-lg font-semibold text-slate-900">Identity and academics</h2>
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <div className="space-y-2"><Label>Full name</Label><Input className="h-11 rounded-xl" {...form.register("full_name")} /></div>
              <div className="space-y-2"><Label>Country</Label><Input className="h-11 rounded-xl" {...form.register("country")} /></div>
              <div className="space-y-2"><Label>Graduation year</Label><Input type="number" className="h-11 rounded-xl" {...form.register("graduation_year")} /></div>
              <div className="space-y-2"><Label>Curriculum</Label><Input className="h-11 rounded-xl" placeholder="NIS Grade 12 Certificate, IB, A-Levels..." {...form.register("curriculum")} /></div>
              <div className="space-y-2 md:col-span-2"><Label>Intended major</Label><Input className="h-11 rounded-xl" {...form.register("intended_major")} /></div>
            </div>
          </section>

          <section className="rounded-[28px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)]">
            <h2 className="text-lg font-semibold text-slate-900">Exams</h2>
            <div className="mt-5 grid gap-4 md:grid-cols-3">
              <div className="space-y-2"><Label>SAT total</Label><Input type="number" className="h-11 rounded-xl" {...form.register("sat_score")} /></div>
              <div className="space-y-2"><Label>SAT Math</Label><Input type="number" className="h-11 rounded-xl" {...form.register("sat_math")} /></div>
              <div className="space-y-2"><Label>SAT Reading/Writing</Label><Input type="number" className="h-11 rounded-xl" {...form.register("sat_ebrw")} /></div>
              <div className="space-y-2"><Label>ACT</Label><Input type="number" className="h-11 rounded-xl" {...form.register("act_score")} /></div>
              <div className="space-y-2"><Label>Duolingo</Label><Input type="number" className="h-11 rounded-xl" {...form.register("duolingo_score")} /></div>
              <div className="space-y-2"><Label>UNT / ENT</Label><Input type="number" className="h-11 rounded-xl" {...form.register("unt_score")} /></div>
            </div>
            <div className="mt-5 grid gap-4 md:grid-cols-5">
              <div className="space-y-2"><Label>IELTS overall</Label><Input className="h-11 rounded-xl" {...form.register("ielts_score")} /></div>
              <div className="space-y-2"><Label>Listening</Label><Input className="h-11 rounded-xl" {...form.register("ielts_listening")} /></div>
              <div className="space-y-2"><Label>Reading</Label><Input className="h-11 rounded-xl" {...form.register("ielts_reading")} /></div>
              <div className="space-y-2"><Label>Writing</Label><Input className="h-11 rounded-xl" {...form.register("ielts_writing")} /></div>
              <div className="space-y-2"><Label>Speaking</Label><Input className="h-11 rounded-xl" {...form.register("ielts_speaking")} /></div>
            </div>
            <div className="mt-5 grid gap-4 md:grid-cols-5">
              <div className="space-y-2"><Label>TOEFL total</Label><Input type="number" className="h-11 rounded-xl" {...form.register("toefl_score")} /></div>
              <div className="space-y-2"><Label>Reading</Label><Input type="number" className="h-11 rounded-xl" {...form.register("toefl_reading")} /></div>
              <div className="space-y-2"><Label>Listening</Label><Input type="number" className="h-11 rounded-xl" {...form.register("toefl_listening")} /></div>
              <div className="space-y-2"><Label>Speaking</Label><Input type="number" className="h-11 rounded-xl" {...form.register("toefl_speaking")} /></div>
              <div className="space-y-2"><Label>Writing</Label><Input type="number" className="h-11 rounded-xl" {...form.register("toefl_writing")} /></div>
            </div>
          </section>

          <section className="rounded-[28px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)]">
            <h2 className="text-lg font-semibold text-slate-900">Curriculum scores and funding</h2>
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <div className="space-y-2"><Label>A-Level subjects</Label><Input className="h-11 rounded-xl" {...form.register("a_level_subjects")} /></div>
              <div className="space-y-2"><Label>A-Level predicted</Label><Input className="h-11 rounded-xl" {...form.register("a_level_predicted")} /></div>
              <div className="space-y-2"><Label>AP subjects</Label><Input className="h-11 rounded-xl" {...form.register("ap_subjects")} /></div>
              <div className="space-y-2"><Label>IB predicted score</Label><Input type="number" className="h-11 rounded-xl" {...form.register("ib_predicted_score")} /></div>
              <div className="space-y-2"><Label>NIS Grade 12 Certificate</Label><Input className="h-11 rounded-xl" {...form.register("nis_grade12_certificate_gpa")} /></div>
              <div className="space-y-2"><Label>Budget range</Label><Input className="h-11 rounded-xl" placeholder="Need full ride, $10k/year, etc." {...form.register("budget_range")} /></div>
            </div>
          </section>

          <div className="flex justify-end">
            <Button type="submit" disabled={saveMutation.isPending} className="bg-navy-950 text-white hover:bg-navy-900">
              {saveMutation.isPending ? "Saving..." : "Save profile"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
