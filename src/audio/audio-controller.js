const AUDIO_PATH = '../../data/audio.opus';

export class AudioController {
  constructor(duration, onUpdate) {
    this.duration = Number.isFinite(duration) && duration > 0 ? duration : 174.64;
    this.onUpdate = onUpdate;
    this.context = null;
    this.master = null;
    this.buffer = null;
    this.fetchPromise = null;
    this.bufferPromise = null;
    this.source = null;
    this.sourceId = 0;
    this.timer = 0;
    this.time = 0;
    this.running = false;
    this.volume = 0.85;
    this.muted = false;
    this.anchorTime = 0;
    this.anchorPosition = 0;
  }

  audioUrl() {
    return window.__VFS_AUDIO_URL || new URL(AUDIO_PATH, import.meta.url).href;
  }

  preload() {
    if (!this.fetchPromise) {
      this.fetchPromise = fetch(this.audioUrl())
        .then((response) => {
          if (!response.ok) throw new Error(`音频加载失败（${response.status}）`);
          return response.arrayBuffer();
        })
        .catch((error) => {
          this.fetchPromise = null;
          throw error;
        });
    }
    return this.fetchPromise;
  }

  createContext() {
    if (this.context) return this.context;
    const options = { latencyHint: 'playback' };
    try {
      this.context = new AudioContext({ ...options, sampleRate: 48000 });
    } catch {
      this.context = new AudioContext(options);
    }
    this.master = this.context.createGain();
    this.master.gain.value = this.muted ? 0 : this.volume;
    this.master.connect(this.context.destination);
    return this.context;
  }

  loadBuffer() {
    if (this.buffer) return Promise.resolve(this.buffer);
    if (!this.bufferPromise) {
      this.bufferPromise = this.preload()
        .then((data) => this.createContext().decodeAudioData(data.slice(0)))
        .then((buffer) => {
          this.buffer = buffer;
          return buffer;
        })
        .catch((error) => {
          this.bufferPromise = null;
          throw error;
        });
    }
    return this.bufferPromise;
  }

  async play() {
    const context = this.createContext();
    const resumed = context.resume();
    const buffer = await this.loadBuffer();
    await resumed;
    if (this.time >= buffer.duration - 0.01) this.time = 0;
    this.running = true;
    this.startSource(this.time);
    this.startTicker();
    this.emit();
  }

  pause() {
    const time = this.currentTime;
    this.stopSource();
    this.stopTicker();
    this.running = false;
    this.time = time;
    this.emit();
  }

  seek(time) {
    const limit = this.buffer ? this.buffer.duration : this.duration;
    this.time = Math.max(0, Math.min(limit, Number.isFinite(time) ? time : 0));
    if (this.running) this.startSource(this.time);
    this.emit();
  }

  setMuted(muted) {
    this.muted = Boolean(muted);
    if (this.master && this.context) {
      this.master.gain.setTargetAtTime(this.muted ? 0 : this.volume, this.context.currentTime, 0.015);
    }
  }

  get currentTime() {
    if (!this.running || !this.context) return this.time;
    const limit = this.buffer ? this.buffer.duration : this.duration;
    return Math.min(limit, this.anchorPosition + (this.context.currentTime - this.anchorTime));
  }

  startSource(offset) {
    this.stopSource();
    const context = this.context;
    const limit = Math.max(0, this.buffer.duration - 0.001);
    const position = Math.max(0, Math.min(limit, offset));
    const source = context.createBufferSource();
    source.buffer = this.buffer;
    source.connect(this.master);
    const id = ++this.sourceId;
    source.onended = () => {
      if (id !== this.sourceId || !this.running) return;
      this.source = null;
      this.running = false;
      this.time = this.buffer.duration;
      this.stopTicker();
      this.emit();
    };
    source.start(0, position);
    this.source = source;
    this.anchorTime = context.currentTime;
    this.anchorPosition = position;
  }

  stopSource() {
    this.sourceId++;
    if (!this.source) return;
    this.source.onended = null;
    try {
      this.source.stop();
    } catch {
      // Source may already have ended.
    }
    this.source.disconnect();
    this.source = null;
  }

  startTicker() {
    this.stopTicker();
    this.timer = setInterval(() => {
      if (this.running) this.emit();
    }, 50);
  }

  stopTicker() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = 0;
    }
  }

  emit() {
    this.onUpdate?.({ time: this.currentTime, running: this.running });
  }
}
