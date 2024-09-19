import networkx as nx
import threading

from typing import List
from graph.chord_graph import ChordGraphBuilder
from models import NoteEvent, RhythmicPattern, Motif, ChordEvent
from playback import play_note_sequence
from graph.integrated_music_graph import IntegratedMusicGraph
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
from scales import ScaleGenerator
from playback import initialize_fluidsynth, play_scale, play_progression
from melody import MelodyGenerator
from models import NoteEvent, RhythmicPattern, Motif

class SlonimskyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Slonimsky Musical Pattern Generator")
        self.create_widgets()
        self.scale_gen = ScaleGenerator()
        self.chord_builder = ChordGraphBuilder()
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
        generate_button = ttk.Button(input_frame, text="Generate Melody", command=self.generate_melody)
        generate_button.grid(row=3, column=0, columnspan=2, pady=10)

        # Graph Display Frame
        graph_frame = ttk.LabelFrame(self.root, text="Graph Visualization")
        graph_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Configure grid weights for resizing
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        graph_frame.grid_rowconfigure(0, weight=1)
        graph_frame.grid_columnconfigure(0, weight=1)

        # Matplotlib Figure
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # Melody Listbox
        melody_frame = ttk.LabelFrame(self.root, text="Generated Melody")
        melody_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        self.melody_listbox = tk.Listbox(melody_frame, height=5)
        self.melody_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Status Bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken', anchor='w')
        status_bar.grid(row=3, column=0, sticky="ew")

        # Initialize Integrated Graph
        self.integrated_graph = None

    def add_tooltip(self, widget, text):
        ToolTip(widget, text)

    def generate_melody(self):
        threading.Thread(target=self._generate_melody_thread, daemon=True).start()

    def _generate_melody_thread(self):
        try:
            root_note = self.root_note_var.get().strip().upper()
            bpm = self.bpm_var.get()
            progression_pattern = self.progression_var.get().strip().split()

            # Validate inputs
            validate_arguments(root_note=root_note, bpm=bpm, progression_pattern=progression_pattern)

            # Generate scale
            main_scale = self.scale_gen.generate_scale(root_note)

            # Build Chord Progression
            chord_progression = self.chord_builder.build_chords(progression_pattern, main_scale)

            # Define rhythms and motifs (could be expanded or loaded from configurations)
            rhythms = [
                RhythmicPattern(pattern='quarter', tempo=bpm, accent='strong'),
                RhythmicPattern(pattern='eighth', tempo=bpm, accent='weak'),
            ]

            motifs = [
                Motif(name='motif1', contour='ascending', length=4),
                Motif(name='motif2', contour='descending', length=4),
            ]

            # Build integrated graph
            integrated_graph_builder = IntegratedMusicGraph()
            scale_notes = []
            for note in main_scale.notes:
                note_event = NoteEvent(
                    note=note + '4',
                    time=0.0,
                    chord='',
                    beat_type='neutral',
                    consonance='consonant' if note in main_scale.generate_notes() else 'dissonant'
                )
                scale_notes.append(note_event)
            
            integrated_graph_builder.build_full_graph(
                scale_notes=scale_notes,
                chords=chord_progression,
                rhythms=rhythms,
                motifs=motifs
            )
            self.integrated_graph = integrated_graph_builder.get_integrated_graph()

            # Visualize the graph
            self.visualize_graph()

            # Generate Melody
            melody_gen = MelodyGenerator(self.integrated_graph)
            melody = melody_gen.generate_melody_dijkstra()
            self.display_melody(melody)
            self.status_var.set("Melody generated successfully.")

            # Play Melody
            if self.audio_available:
                play_note_sequence(melody, bpm=bpm)
        except ValidationError as ve:
            messagebox.showerror("Validation Error", str(ve))
            self.status_var.set("Validation Error")
        except ValueError as ve:
            messagebox.showerror("Input Error", str(ve))
            self.status_var.set("Input Error")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Error generating melody")

    def visualize_graph(self):
        if not self.integrated_graph:
            return

        self.ax.clear()
        self.ax.set_title("Integrated Music Graph")

        # Use Spring Layout for better visualization
        pos = nx.spring_layout(self.integrated_graph, k=0.5, iterations=50)

        # Draw nodes with different colors based on their layer or type
        node_colors = []
        for node in self.integrated_graph.nodes(data=True):
            if node[1].get('functional_role', '').lower() == 'tonic':
                node_colors.append('gold')
            elif node[1].get('functional_role', '').lower() == 'dominant':
                node_colors.append('red')
            elif node[1].get('functional_role', '').lower() == 'subdominant':
                node_colors.append('blue')
            else:
                node_colors.append('grey')

        nx.draw_networkx_nodes(self.integrated_graph, pos, ax=self.ax, node_color=node_colors, node_size=500)
        nx.draw_networkx_labels(self.integrated_graph, pos, ax=self.ax, font_size=10, font_family="sans-serif")

        # Draw edges with different styles based on layer
        for layer, color, style in [
            ('chord-rhythm', 'green', 'solid'),
            ('rhythm-motif', 'purple', 'dashed'),
            ('harmony-motif', 'orange', 'dotted'),
            ('modal_interchange', 'brown', 'dashdot')
        ]:
            edges = [
                (u, v) for u, v, d in self.integrated_graph.edges(data=True)
                if d.get('layer') == layer or d.get('modal_interchange') == True
            ]
            if edges:
                nx.draw_networkx_edges(
                    self.integrated_graph,
                    pos,
                    edgelist=edges,
                    edge_color=color,
                    style=style,
                    ax=self.ax,
                    alpha=0.7
                )

        self.ax.axis('off')
        self.canvas.draw()

    def display_melody(self, melody: List[str]):
        self.melody_listbox.delete(0, tk.END)
        for idx, note in enumerate(melody, start=1):
            self.melody_listbox.insert(tk.END, f"{idx}: {note}")

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