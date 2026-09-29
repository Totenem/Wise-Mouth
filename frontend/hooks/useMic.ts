"use client";
import { useCallback, useEffect, useRef, useState } from "react";

export function useMic(onFrame: (b: ArrayBuffer) => void) {
  const [active, setActive] = useState(false);
  const [muted, setMuted] = useState(false);
  const [level, setLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [camera, setCamera] = useState<MediaStream | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const ctx = useRef<AudioContext | null>(null);
  const cb = useRef(onFrame);
  cb.current = onFrame;

  const start = useCallback(async () => {
    try {
      setError(null);
      const s = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
      });
      const ac = new AudioContext();
      await ac.audioWorklet.addModule("/audio-worklet.js");
      const src = ac.createMediaStreamSource(s);
      const node = new AudioWorkletNode(ac, "pcm-processor");
      const analyser = ac.createAnalyser();
      analyser.fftSize = 256;
      node.port.onmessage = (e) => cb.current(e.data as ArrayBuffer);
      src.connect(node);
      src.connect(analyser);
      const buf = new Uint8Array(analyser.frequencyBinCount);
      stream.current = s;
      ctx.current = ac;
      const tick = () => {
        if (!ctx.current) return;
        analyser.getByteTimeDomainData(buf);
        let peak = 0;
        for (const v of buf) peak = Math.max(peak, Math.abs(v - 128));
        setLevel(peak / 128);
        requestAnimationFrame(tick);
      };
      tick();
      setActive(true);
      setMuted(false);
    } catch (e) {
      setError(
        e instanceof Error && e.name === "NotAllowedError"
          ? "Microphone permission denied."
          : "Could not start the microphone.",
      );
    }
  }, []);

  const toggleMute = useCallback(() => {
    const next = !muted;
    stream.current?.getAudioTracks().forEach((t) => (t.enabled = !next));
    setMuted(next);
    return next;
  }, [muted]);

  const toggleCamera = useCallback(async () => {
    if (camera) {
      camera.getTracks().forEach((t) => t.stop());
      setCamera(null);
      return;
    }
    try {
      setCamera(await navigator.mediaDevices.getUserMedia({ video: true }));
    } catch {
      setError("Camera unavailable.");
    }
  }, [camera]);

  const stop = useCallback(() => {
    stream.current?.getTracks().forEach((t) => t.stop());
    camera?.getTracks().forEach((t) => t.stop());
    ctx.current?.close();
    ctx.current = null;
    stream.current = null;
    setActive(false);
    setCamera(null);
  }, [camera]);

  useEffect(
    () => () => {
      stream.current?.getTracks().forEach((t) => t.stop());
      ctx.current?.close();
    },
    [],
  );
  return { active, muted, level, error, camera, start, toggleMute, toggleCamera, stop };
}
