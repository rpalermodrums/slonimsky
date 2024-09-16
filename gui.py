import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
import os
from slonimsky import (
    ScaleGenerator, ChordBuilder, ProgressionBuilder, MelodicPatternGenerator,
    Catalog, initialize_fluidsynth, play_scale, play_progression,
    validate_root_note, validate_bpm, validate_interval, validate_iterations
)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class SlonimskyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Slonimsky Musical Pattern Generator")
        self.create_widgets()
        self.scale_gen = ScaleGenerator()
        self.chord_builder = ChordBuilder()
        self.progression_builder = ProgressionBuilder()
        self.melodic_gen = MelodicPatternGenerator()
        self.catalog = Catalog()
        self.audio_available = initialize_fluidsynth()
        if not self.audio_available:
            messagebox.showwarning("Audio Unavailable", "FluidSynth initialization failed. Audio playback will be disabled.")

    def create_widgets(self):
        # Input Frame
        input_frame = ttk.LabelFrame(self.root, text="Inputs")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Root Note
        ttk.Label(input_frame, text="Root Note:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.root_note_var = tk.StringVar(value="C")
        ttk.Entry(input_frame, textvariable=self.root_note_var).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # BPM
        ttk.Label(input_frame, text="BPM:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.bpm_var = tk.IntVar(value=120)
        ttk.Entry(input_frame, textvariable=self.bpm_var).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Progression Pattern
        ttk.Label(input_frame, text="Progression Pattern:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.progression_var = tk.StringVar(value="I IV V")
        ttk.Entry(input_frame, textvariable=self.progression_var).grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Generate Button
        ttk.Button(input_frame, text="Generate Scales", command=self.generate_scales).grid(row=3, column=0, columnspan=2, padx=5, pady=10)

        # Catalog Frame
        catalog_frame = ttk.LabelFrame(self.root, text="Catalog")
        catalog_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Scales Listbox
        self.scales_listbox = tk.Listbox(catalog_frame)
        self.scales_listbox.pack(fill='both', expand=True)
        self.scales_listbox.bind('<<ListboxSelect>>', self.display_scale_graph)

        # Visualization Frame
        visualization_frame = ttk.LabelFrame(self.root, text="Visualization")
        visualization_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        self.figure = plt.Figure(figsize=(5,4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=visualization_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # Playback Controls Frame
        playback_frame = ttk.LabelFrame(self.root, text="Playback Controls")
        playback_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        ttk.Button(playback_frame, text="Play Selected Scale", command=self.play_selected_scale).pack(side='left', padx=5)
        ttk.Button(playback_frame, text="Play Progression", command=self.play_progression_thread).pack(side='left', padx=5)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Welcome to Slonimsky Musical Pattern Generator!")
        ttk.Label(self.root, textvariable=self.status_var, relief='sunken', anchor='w').grid(row=3, column=0, columnspan=2, sticky="ew")

        # Configure grid weights
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)

    def generate_scales(self):
        try:
            root_note = validate_root_note(self.root_note_var.get())
            bpm = self.bpm_var.get()
            validate_bpm(bpm)

            self.scale_gen.generate_custom_scales(num_notes=7, root_note=root_note)
            self.scale_gen.catalog_scales(root_note=root_note)
            all_scales = self.scale_gen.get_all_scales()

            self.catalog.scales = all_scales
            self.scales_listbox.delete(0, tk.END)
            for scale in all_scales:
                self.scales_listbox.insert(tk.END, scale.name)

            self.status_var.set("Scales generated and cataloged successfully.")
        except ValueError as ve:
            messagebox.showerror("Input Error", str(ve))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def display_scale_graph(self, event):
        selection = self.scales_listbox.curselection()
        if selection:
            index = selection[0]
            selected_scale = self.catalog.scales[index]
            self.ax.clear()
            self.ax.set_title(f"Scale: {selected_scale.name}")
            self.ax.plot(range(len(selected_scale.notes)), [1]*len(selected_scale.notes), 'ro')
            self.ax.set_yticks([])
            self.ax.set_xticks(range(len(selected_scale.notes)))
            self.ax.set_xticklabels(selected_scale.notes)
            self.canvas.draw()

    def play_selected_scale(self):
        if not self.audio_available:
            messagebox.showinfo("Audio Unavailable", "Audio playback is not available.")
            return
        selection = self.scales_listbox.curselection()
        if selection:
            index = selection[0]
            selected_scale = self.catalog.scales[index]
            threading.Thread(target=play_scale, args=(selected_scale, self.bpm_var.get()), daemon=True).start()
            self.status_var.set(f"Playing scale: {selected_scale.name}")
        else:
            messagebox.showinfo("No Selection", "Please select a scale to play.")

    def play_progression_thread(self):
        threading.Thread(target=self.play_progression, daemon=True).start()

    def play_progression(self):
        if not self.audio_available:
            messagebox.showinfo("Audio Unavailable", "Audio playback is not available.")
            return
        try:
            progression = self.progression_builder.build_progression(
                self.progression_var.get().split(),
                validate_root_note(self.root_note_var.get())
            )
            play_progression(progression, bpm=self.bpm_var.get())
            self.status_var.set("Playing chord progression...")
        except Exception as e:
            messagebox.showerror("Playback Error", str(e))

def main():
    root = tk.Tk()
    app = SlonimskyGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()