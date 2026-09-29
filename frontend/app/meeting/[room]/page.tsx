"use client";
import { Suspense } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { FullPageLoader } from "@/components/Loading";
import { MeetingRoom } from "@/components/MeetingRoom";

function Inner() {
  const { room } = useParams<{ room: string }>();
  const name = useSearchParams().get("name") || "Guest";
  return <MeetingRoom room={room} name={name} />;
}

export default function MeetingPage() {
  return (
    <Suspense fallback={<FullPageLoader messages={["Joining the room...", "Setting things up..."]} />}>
      <Inner />
    </Suspense>
  );
}
