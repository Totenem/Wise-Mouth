"use client";
import { Suspense } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { MeetingRoom } from "@/components/MeetingRoom";

function Inner() {
  const { room } = useParams<{ room: string }>();
  const name = useSearchParams().get("name") || "Guest";
  return <MeetingRoom room={room} name={name} />;
}

export default function MeetingPage() {
  return (
    <Suspense fallback={<div className="p-8 text-slate-400">Joining...</div>}>
      <Inner />
    </Suspense>
  );
}
