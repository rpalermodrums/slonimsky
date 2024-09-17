import threading

import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pydantic import ValidationError
from tkinter import ttk, messagebox, filedialog, Menu
from tktooltip import ToolTip

from mingus.containers import Bar, Track, Composition
from mingus.midi import midi_file_out

from catalog import Catalog
from main import validate_arguments
from scales import ScaleGenerator, ChordBuilder, ProgressionBuilder, MelodicPatternGenerator
from playback import initialize_fluidsynth, play_scale, play_progression


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
            messagebox.showwarning(
                "Audio Unavailable",
                "FluidSynth initialization failed. Audio playback will be disabled."
            )
        self.create_menu()

    def create_menu(self):
        menu_bar = Menu(self.root)
        
        # File Menu
        file_menu = Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Export MIDI", command=self.export_midi)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Help Menu
        help_menu = Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menu_bar)

    def show_about(self):
        messagebox.showinfo("About", "Slonimsky Musical Pattern Generator\nVersion 1.0")

    def create_widgets(self):
        # Input Frame
        input_frame = ttk.LabelFrame(self.root, text="Inputs")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Root Note
        ttk.Label(input_frame, text="Root Note:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.root_note_var = tk.StringVar(value="C")
        root_note_entry = ttk.Entry(input_frame, textvariable=self.root_note_var, width=10)
        root_note_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.add_tooltip(root_note_entry, "Enter the root note (e.g., C, D#, F)")

        # BPM
        ttk.Label(input_frame, text="BPM:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.bpm_var = tk.IntVar(value=120)
        bpm_entry = ttk.Entry(input_frame, textvariable=self.bpm_var, width=10)
        bpm_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.add_tooltip(bpm_entry, "Set the tempo in BPM")

        # Progression Pattern
        ttk.Label(input_frame, text="Progression Pattern:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.progression_var = tk.StringVar(value="I IV V")
        progression_entry = ttk.Entry(input_frame, textvariable=self.progression_var, width=20)
        progression_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.add_tooltip(progression_entry, "Define the chord progression pattern (e.g., I IV V)")

        # Generate Button
        ttk.Button(input_frame, text="Generate Scales", command=self.generate_scales).grid(row=3, column=0, columnspan=2, padx=5, pady=10)

        # Catalog Frame
        catalog_frame = ttk.LabelFrame(self.root, text="Catalog")
        catalog_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Scales Listbox with Scrollbar
        scrollbar = ttk.Scrollbar(catalog_frame, orient="vertical")
        self.scales_listbox = tk.Listbox(catalog_frame, yscrollcommand=scrollbar.set, height=15)
        scrollbar.config(command=self.scales_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.scales_listbox.pack(side='left', fill='both', expand=True)
        self.scales_listbox.bind('<<ListboxSelect>>', self.display_scale_graph)

        # Visualization Frame
        visualization_frame = ttk.LabelFrame(self.root, text="Visualization")
        visualization_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        self.figure = plt.Figure(figsize=(6,5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=visualization_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # Playback Controls Frame
        playback_frame = ttk.LabelFrame(self.root, text="Playback Controls")
        playback_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        ttk.Button(playback_frame, text="Play Selected Scale", command=self.play_selected_scale).pack(side='left', padx=5, pady=5)
        ttk.Button(playback_frame, text="Play Progression", command=self.play_progression_thread).pack(side='left', padx=5, pady=5)
        ttk.Button(playback_frame, text="Export MIDI", command=self.export_midi).pack(side='left', padx=5, pady=5)

        # Status Bar
        self.status_var = tk.StringVar(value="Welcome to Slonimsky Musical Pattern Generator!")
        ttk.Label(self.root, textvariable=self.status_var, relief='sunken', anchor='w').grid(row=3, column=0, columnspan=2, sticky="ew")

        # Configure grid weights for responsiveness
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=3)
        self.root.rowconfigure(1, weight=1)

    def add_tooltip(self, widget, msg):
        ToolTip(widget, msg=msg)

    def generate_scales(self):
        try:
            root_note = self.root_note_var.get().strip().capitalize()
            bpm = self.bpm_var.get()
            progression_pattern = self.progression_var.get().strip()

            validate_arguments(root_note=root_note, bpm=bpm, progression_pattern=progression_pattern)

            self.scale_gen.generate_custom_scales(root_note=root_note)
            self.scale_gen.catalog_scales(root_note=root_note)
            all_scales = self.scale_gen.get_all_scales()

            self.catalog.scales = all_scales
            self.scales_listbox.delete(0, tk.END)
            for scale in all_scales:
                self.scales_listbox.insert(tk.END, scale.name)

            self.status_var.set("Scales generated and cataloged successfully.")
        except ValueError as ve:
            messagebox.showerror("Input Error", str(ve))
            self.status_var.set("Error: " + str(ve))
        except ValidationError as ve:
            messagebox.showerror("Validation Error", str(ve))
            self.status_var.set("Validation Error: " + str(ve))
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Error: " + str(e))

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
            self.ax.grid(True, which='both', linestyle='--', linewidth=0.5)
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
                self.root_note_var.get()
            )
            play_progression(progression, bpm=self.bpm_var.get())
            self.status_var.set("Playing chord progression...")
        except Exception as e:
            messagebox.showerror("Playback Error", str(e))
            self.status_var.set("Error: " + str(e))

    def export_midi(self):
        if not self.catalog.scales:
            messagebox.showinfo("No Scales", "No scales available to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".mid",
            filetypes=[("MIDI files", "*.mid"), ("All files", "*.*")]
        )
        if file_path:
            try:
                composition = Composition()
                bpm = self.bpm_var.get()

                for scale in self.catalog.scales:
                    track = Track()
                    bar = Bar()
                    for note_name in scale.notes:
                        bar + note_name
                    track + bar
                    composition.add_track(track)

                midi_file_out.write_Composition(file_path, composition, bpm)
                messagebox.showinfo("Export MIDI", f"MIDI file exported successfully to {file_path}")
                self.status_var.set(f"MIDI export successful: {file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))
                self.status_var.set("Error: " + str(e))


def main():
    root = tk.Tk()
    app = SlonimskyGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()