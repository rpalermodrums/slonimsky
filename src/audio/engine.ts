import * as Tone from "tone";
import type { NoteEvent } from "@/core/types";

type AudioEngineState = "stopped" | "playing" | "paused";

interface NoteChangeEvent {
  midi: number | null;
  index: number | null;
}

type NoteCallback = (event: NoteChangeEvent) => void;
type LoopCallback = () => void;
type CountInCallback = (beat: number) => void;
type CountInCompleteCallback = () => void;

class AudioEngine {
  private synth: Tone.PolySynth | null = null;
  private scheduledEvents: number[] = [];
  private _state: AudioEngineState = "stopped";
  private _isInitialized = false;
  private noteCallbacks: Set<NoteCallback> = new Set();
  private loopCallbacks: Set<LoopCallback> = new Set();
  private countInCompleteCallbacks: Set<CountInCompleteCallback> = new Set();
  private loopEventId: number | null = null;
  private clickSynth: Tone.MembraneSynth | null = null;

  get state(): AudioEngineState {
    return this._state;
  }

  get isInitialized(): boolean {
    return this._isInitialized;
  }

  async initialize(): Promise<void> {
    if (this._isInitialized) return;

    await Tone.start();

    const context = Tone.getContext();

    if (context.state === "suspended") {
      await context.resume();
    }

    this.synth = new Tone.PolySynth(Tone.Synth, {
      oscillator: { type: "triangle" },
      envelope: {
        attack: 0.01,
        decay: 0.15,
        sustain: 0.4,
        release: 0.6,
      },
      volume: 0,
    }).toDestination();

    this.clickSynth = new Tone.MembraneSynth({
      pitchDecay: 0.008,
      octaves: 2,
      envelope: {
        attack: 0.001,
        decay: 0.3,
        sustain: 0,
        release: 0.1,
      },
      volume: -6,
    }).toDestination();

    await new Promise((resolve) => setTimeout(resolve, 50));

    this._isInitialized = true;
  }

  setTempo(bpm: number): void {
    Tone.getTransport().bpm.value = bpm;
  }

  getTempo(): number {
    return Tone.getTransport().bpm.value;
  }

  schedulePatternWithCountIn(
    events: NoteEvent[],
    loop: boolean,
    countInBeats: number,
    onBeat: CountInCallback
  ): void {
    if (!this.synth || !this.clickSynth) {
      throw new Error("AudioEngine not initialized. Call initialize() first.");
    }

    this.clearScheduledEvents();
    const transport = Tone.getTransport();

    for (let beat = 0; beat < countInBeats; beat++) {
      const clickId = transport.schedule((time) => {
        const pitch = beat === 0 ? "G4" : "C4";
        this.clickSynth?.triggerAttackRelease(pitch, "16n", time, 0.8);
        
        Tone.getDraw().schedule(() => {
          onBeat(beat + 1);
        }, time);
      }, `${beat}:0:0`);
      this.scheduledEvents.push(clickId);
    }

    const countInCompleteId = transport.schedule((time) => {
      Tone.getDraw().schedule(() => {
        this.emitCountInComplete();
      }, time);
    }, `${countInBeats}:0:0`);
    this.scheduledEvents.push(countInCompleteId);

    const offsetEvents = events.map((e) => ({
      ...e,
      time: e.time + countInBeats,
    }));

    if (loop && offsetEvents.length > 0) {
      const lastEvent = offsetEvents[offsetEvents.length - 1];
      const loopEndTime = lastEvent.time + lastEvent.duration;
      transport.loopStart = `${countInBeats}:0:0`;
      transport.loopEnd = `${loopEndTime}:0:0`;
      transport.loop = true;

      if (this.loopEventId !== null) {
        transport.clear(this.loopEventId);
      }
      this.loopEventId = transport.schedule(() => {
        this.emitLoopComplete();
      }, `${loopEndTime - 0.01}:0:0`);
    } else {
      transport.loop = false;
    }

    for (let i = 0; i < offsetEvents.length; i++) {
      const event = offsetEvents[i];
      const noteIndex = i;
      const durationSeconds = Tone.Time(`${event.duration}:0:0`).toSeconds();

      const id = transport.schedule((time) => {
        const noteName = Tone.Frequency(event.pitch, "midi").toNote();
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

  schedulePattern(events: NoteEvent[], loop = false): void {
    if (!this.synth) {
      throw new Error("AudioEngine not initialized. Call initialize() first.");
    }

    this.clearScheduledEvents();

    const transport = Tone.getTransport();

    // Reset loopStart to beginning (may have been set by count-in playback)
    transport.loopStart = 0;

    if (loop && events.length > 0) {
      const lastEvent = events[events.length - 1];
      const loopEndTime = lastEvent.time + lastEvent.duration;
      transport.loopEnd = `${loopEndTime}:0:0`;
      transport.loop = true;

      if (this.loopEventId !== null) {
        transport.clear(this.loopEventId);
      }
      this.loopEventId = transport.schedule(() => {
        this.emitLoopComplete();
      }, `${loopEndTime - 0.01}:0:0`);
    } else {
      transport.loop = false;
    }

    for (let i = 0; i < events.length; i++) {
      const event = events[i];
      const noteIndex = i;
      const durationSeconds = Tone.Time(`${event.duration}:0:0`).toSeconds();
      
      const id = transport.schedule((time) => {
        const noteName = Tone.Frequency(event.pitch, "midi").toNote();
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
      transport.start("+0.05");
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

  preview(events: NoteEvent[], maxNotes = 4): void {
    if (!this.synth) return;

    this.stop();
    this.clearScheduledEvents();

    const previewEvents = events.slice(0, maxNotes);
    const transport = Tone.getTransport();
    transport.loop = false;

    for (let i = 0; i < previewEvents.length; i++) {
      const event = previewEvents[i];
      const noteIndex = i;
      const durationSeconds = Tone.Time(`${event.duration}:0:0`).toSeconds();
      
      const id = transport.schedule((time) => {
        const noteName = Tone.Frequency(event.pitch, "midi").toNote();
        this.synth?.triggerAttackRelease(
          noteName,
          durationSeconds * 0.8,
          time,
          event.velocity / 127
        );
        
        Tone.getDraw().schedule(() => {
          this.emitNoteChange({ midi: event.pitch, index: noteIndex });
        }, time);
      }, `${event.time}:0:0`);

      this.scheduledEvents.push(id);
    }

    const lastEvent = previewEvents[previewEvents.length - 1];
    const endTime = lastEvent.time + lastEvent.duration;
    const stopId = transport.schedule(() => {
      this.stop();
      this.emitNoteChange({ midi: null, index: null });
    }, `${endTime}:0:0`);
    this.scheduledEvents.push(stopId);

    transport.position = 0;
    transport.start("+0.05");
    this._state = "playing";
  }

  dispose(): void {
    this.stop();
    this.clearScheduledEvents();
    this.synth?.dispose();
    this.clickSynth?.dispose();
    this.synth = null;
    this.clickSynth = null;
    this._isInitialized = false;
    this.noteCallbacks.clear();
    this.loopCallbacks.clear();
    this.countInCompleteCallbacks.clear();
  }

  onNoteChange(callback: NoteCallback): () => void {
    this.noteCallbacks.add(callback);
    return () => this.noteCallbacks.delete(callback);
  }

  onLoopComplete(callback: LoopCallback): () => void {
    this.loopCallbacks.add(callback);
    return () => this.loopCallbacks.delete(callback);
  }

  onCountInComplete(callback: CountInCompleteCallback): () => void {
    this.countInCompleteCallbacks.add(callback);
    return () => this.countInCompleteCallbacks.delete(callback);
  }

  private emitNoteChange(event: NoteChangeEvent): void {
    for (const cb of this.noteCallbacks) {
      cb(event);
    }
  }

  private emitLoopComplete(): void {
    for (const cb of this.loopCallbacks) {
      cb();
    }
  }

  private emitCountInComplete(): void {
    for (const cb of this.countInCompleteCallbacks) {
      cb();
    }
    this.countInCompleteCallbacks.clear();
  }
}

export const audioEngine = new AudioEngine();
