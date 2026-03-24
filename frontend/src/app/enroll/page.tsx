"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
export default function EnrollRedirect() {
  const router = useRouter();
  useEffect(() => { router.replace("/enrollment"); }, [router]);
  return null;
}
