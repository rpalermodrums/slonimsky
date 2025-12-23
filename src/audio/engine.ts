import * as Tone from "tone";
import type { NoteEvent } from "@/core/types";

type AudioEngineState = "stopped" | "playing" | "paused";

interface NoteChangeEvent {
  midi: number | null;
  index: number | null;
}

type NoteCallback = (event: NoteChangeEvent) => void;

class AudioEngine {
  private synth: Tone.PolySynth | null = null;
  private scheduledEvents: number[] = [];
  private _state: AudioEngineState = "stopped";
  private _isInitialized = false;
  private noteCallbacks: Set<NoteCallback> = new Set();

  get state(): AudioEngineState {
    return this._state;
  }

  get isInitialized(): boolean {
    return this._isInitialized;
  }

  async initialize(): Promise<void> {
    if (this._isInitialized) return;

    await Tone.start();

    this.synth = new Tone.PolySynth(Tone.Synth, {
      oscillator: { type: "triangle" },
      envelope: {
        attack: 0.02,
        decay: 0.1,
        sustain: 0.3,
        release: 0.8,
      },
    }).toDestination();

    this._isInitialized = true;
  }

  setTempo(bpm: number): void {
    Tone.getTransport().bpm.value = bpm;
  }

  getTempo(): number {
    return Tone.getTransport().bpm.value;
  }

  schedulePattern(events: NoteEvent[], loop = false): void {
    if (!this.synth) {
      throw new Error("AudioEngine not initialized. Call initialize() first.");
    }

    this.clearScheduledEvents();

    const transport = Tone.getTransport();

    if (loop && events.length > 0) {
      const lastEvent = events[events.length - 1];
      transport.loopEnd = `${lastEvent.time + lastEvent.duration}:0:0`;
      transport.loop = true;
    } else {
      transport.loop = false;
    }

    for (let i = 0; i < events.length; i++) {
      const event = events[i];
      const noteIndex = i;
      const id = transport.schedule((time) => {
        const noteName = Tone.Frequency(event.pitch, "midi").toNote();
        const durationSeconds = Tone.Time(`${event.duration}:0:0`).toSeconds();
        this.synth?.triggerAttackRelease(
          noteName,
          durationSeconds,
          time,
          event.velocity / 127
        );
        Tone.getDraw().schedule(() => {
          this.emitNoteChange({ midi: event.pitch, index: noteIndex });
        }, time);
        Tone.getDraw().schedule(() => {
          this.emitNoteChange({ midi: null, index: null });
        }, time + durationSeconds * 0.9);
      }, `${event.time}:0:0`);

      this.scheduledEvents.push(id);
    }
  }

  play(): void {
    if (!this._isInitialized) {
      throw new Error("AudioEngine not initialized. Call initialize() first.");
    }

    const transport = Tone.getTransport();

    if (this._state === "paused") {
      transport.start();
    } else {
      transport.stop();
      transport.position = 0;
      transport.start();
    }

    this._state = "playing";
  }

  pause(): void {
    Tone.getTransport().pause();
    this._state = "paused";
  }

  stop(): void {
    const transport = Tone.getTransport();
    transport.stop();
    transport.position = 0;
    this._state = "stopped";
  }

  private clearScheduledEvents(): void {
    const transport = Tone.getTransport();
    for (const id of this.scheduledEvents) {
      transport.clear(id);
    }
    this.scheduledEvents = [];
  }

  dispose(): void {
    this.stop();
    this.clearScheduledEvents();
    this.synth?.dispose();
    this.synth = null;
    this._isInitialized = false;
    this.noteCallbacks.clear();
  }

  onNoteChange(callback: NoteCallback): () => void {
    this.noteCallbacks.add(callback);
    return () => this.noteCallbacks.delete(callback);
  }

  private emitNoteChange(event: NoteChangeEvent): void {
    for (const cb of this.noteCallbacks) {
      cb(event);
    }
  }
}

export const audioEngine = new AudioEngine();
