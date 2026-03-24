"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
export default function StatusRedirect() {
  const router = useRouter();
  useEffect(() => { router.replace("/enrollment?tab=status"); }, [router]);
  return null;
}
