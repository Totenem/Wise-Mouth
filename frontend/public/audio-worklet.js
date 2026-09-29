// Downsamples mic audio to 16 kHz mono PCM16 and posts ~100 ms frames.
class PCMProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.ratio = sampleRate / 16000;
    this.pos = 0;
    this.buf = [];
  }
  process(inputs) {
    const ch = inputs[0] && inputs[0][0];
    if (!ch) return true;
    while (this.pos < ch.length) {
      this.buf.push(ch[Math.floor(this.pos)]);
      this.pos += this.ratio;
    }
    this.pos -= ch.length;
    while (this.buf.length >= 1600) {
      const chunk = this.buf.splice(0, 1600);
      const out = new Int16Array(1600);
      for (let i = 0; i < 1600; i++) {
        const s = Math.max(-1, Math.min(1, chunk[i]));
        out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
      }
      this.port.postMessage(out.buffer, [out.buffer]);
    }
    return true;
  }
}
registerProcessor("pcm-processor", PCMProcessor);
