"use client";
import { useParams } from "next/navigation";
import { ReportView } from "@/components/ReportView";

export default function ReportPage() {
  const { room } = useParams<{ room: string }>();
  return <ReportView id={room} />;
}
