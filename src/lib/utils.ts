import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind CSS classes with clsx
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Normalize a value to be within 0-11 (pitch class range)
 */
export function normalizePitchClass(value: number): number {
  return ((value % 12) + 12) % 12;
}

/**
 * Convert MIDI note number to pitch class
 */
export function midiToPitchClass(midi: number): number {
  return normalizePitchClass(midi);
}

/**
 * Convert pitch class and octave to MIDI note number
 */
export function pitchClassToMidi(pitchClass: number, octave: number = 4): number {
  return pitchClass + (octave + 1) * 12;
}

/**
 * Format a number with leading zeros
 */
export function padNumber(num: number, length: number): string {
  return num.toString().padStart(length, "0");
}

/**
 * Capitalize first letter of a string
 */
export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Generate a range of numbers
 */
export function range(start: number, end: number): number[] {
  return Array.from({ length: end - start }, (_, i) => start + i);
}

/**
 * Clamp a number between min and max
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}
