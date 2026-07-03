import configparser
import pretty_midi
import json
import re

# ==========================================
# 1. KONFIGURATION & SETUP
# ==========================================
config_string = """[HEADER]
TITLE="Ermacodera Scale System"
ARTIST="Felix Ermacora"
VERSION="1.0"
MODE="XY"

[SOURCE]
TEXT = Input your source text to generate MIDI sequences via the Ermacodera Scaling algorithm.

[PITCH]
ALPHABET=C,D,E,F,G,A,H,B
BASE_OCTAVE=4

[TIMING]
REST_UNIT=1/16
NOTE_DURATION=250
REMOVED_CHAR_WEIGHT=50

[ARTICULATION]
SHORT_WORD_MAX_LENGTH=3
LONG_WORD_MIN_LENGTH=7
STACCATO_FACTOR=0.75"""

config = configparser.ConfigParser()
config.read_string(config_string)

# Variablen aus der Config extrahieren
source_text = config['SOURCE']['text']
alphabet_str = config['PITCH']['alphabet']
musical_alphabet = [char.strip().upper() for char in alphabet_str.split(',')]
base_octave = int(config['PITCH']['base_octave'])

note_base_duration_sec = int(config['TIMING']['note_duration']) / 1000.0
removed_char_weight_sec = int(config['TIMING']['removed_char_weight']) / 1000.0

def parse_rest_unit(rest_unit_str, base_duration_sec):
    try:
        numerator, denominator = map(int, rest_unit_str.split('/'))
        return (numerator / denominator) * base_duration_sec * 4 
    except ValueError:
        print(f"Warning: Could not parse REST_UNIT '{rest_unit_str}'. Using default of (1/4) * base_duration_sec.")
        return (1/4) * base_duration_sec

rest_unit_duration_sec = parse_rest_unit(config['TIMING']['rest_unit'], note_base_duration_sec)

short_word_max_length = int(config['ARTICULATION']['short_word_max_length'])
long_word_min_length = int(config['ARTICULATION']['long_word_min_length'])
staccato_factor = float(config['ARTICULATION']['staccato_factor'])


# ==========================================
# 2. HILFSFUNKTIONEN
# ==========================================
letter_to_midi_offset = {
    'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'H': 11, 'B': 11
}

def get_midi_pitch(letter, octave):
    """Berechnet den MIDI-Pitch. C4 = 60."""
    if letter.upper() in letter_to_midi_offset:
        # Formel: (Octave + 1) * 12 + Offset
        # C4 -> (4 + 1) * 12 + 0 = 60
        return (octave + 1) * 12 + letter_to_midi_offset[letter.upper()]
    return None


# ==========================================
# 3. ERMACODERA SCALE GENERATOR
# ==========================================
class ErmacoderaScaleGenerator:
    def __init__(self):
        # 1. Das eurythmische Mapping für Vokale
        self.eurythmy_vowels = {
            'a': {"space_width": 1.0, "freq_shift": 1.5, "character": "open"},     # Weite / Offenheit
            'e': {"space_width": 0.2, "freq_shift": 0.8, "character": "dense"},    # Widerstand / Kompression
            'i': {"space_width": 0.0, "freq_shift": 2.0, "character": "focused"},  # Vertikalität / Strahlend
            'o': {"space_width": 0.6, "freq_shift": 0.7, "character": "warm"},     # Umfassung / Rund
            'u': {"space_width": 0.1, "freq_shift": 0.3, "character": "deep"}      # Tiefe / Erstarrung
        }

        # 2. Das eurythmische Mapping für Konsonanten
        self.eurythmy_consonants = {
            'h': {"mod_type": "noise", "mod_intensity": 0.8},       # Hauch / Rauschen
            'b': {"mod_type": "gate", "mod_intensity": 0.9},        # Umhüllung / Grenze
            'p': {"mod_type": "gate", "mod_intensity": 1.0},        # Umhüllung / Grenze
            'l': {"mod_type": "fluid", "mod_intensity": 0.7},       # Flüssig / Chorus-artig
            'r': {"mod_type": "granular", "mod_intensity": 0.85},   # Rollend / Wirbel
            's': {"mod_type": "distortion", "mod_intensity": 0.75}  # Trennend / Scharf
        }

    def analyze_text(self, text):
        dataset = []
        current_octave_shift = 0   
        current_base_mode = "Normal"  
        clean_text = text.strip()

        for i, char in enumerate(clean_text):
            step_data = {
                "char": char,
                "index": i,
                "octave_shift": current_octave_shift,
                "base_mode": current_base_mode,
                "space_width": 0.5,        
                "freq_shift": 1.0,         
                "character": "neutral",
                "mod_type": "none",
                "mod_intensity": 0.0,
                "transient_sharpness": 0.5,
                "is_double_operator": False
            }

            # --- REGEL 1: Großbuchstaben als Zustands-Trigger ---
            if char.isupper() and char.isalpha():
                current_base_mode = f"Shift_{char}"
                step_data["base_mode"] = current_base_mode
                step_data["transient_sharpness"] = 0.9

            # --- REGEL 2: Satzzeichen als progressive Zähler & Resets ---
            elif char == '?':
                current_octave_shift += 1
                if current_octave_shift > 2:  
                    current_octave_shift = 0
                step_data["octave_shift"] = current_octave_shift

            elif char == '!':
                current_octave_shift -= 1
                if current_octave_shift < -2: 
                    current_octave_shift = 0
                step_data["octave_shift"] = current_octave_shift

            # --- REGEL 3: Doppelbuchstaben als Operatoren ---
            if i > 0 and char.lower() == clean_text[i-1].lower() and char.isalpha():
                step_data["is_double_operator"] = True
                step_data["transient_sharpness"] = 0.1

            # --- REGEL 4: Eurythmische Matrix-Zuweisung ---
            lower_char = char.lower()

            if lower_char in self.eurythmy_vowels:
                vowel_rules = self.eurythmy_vowels[lower_char]
                step_data["space_width"] = vowel_rules["space_width"]
                step_data["freq_shift"] = vowel_rules["freq_shift"]
                step_data["character"] = vowel_rules["character"]

            elif lower_char in self.eurythmy_consonants:
                consonant_rules = self.eurythmy_consonants[lower_char]
                step_data["mod_type"] = consonant_rules["mod_type"]
                step_data["mod_intensity"] = consonant_rules["mod_intensity"]

                if consonant_rules["mod_type"] == "gate":
                    step_data["space_width"] = 0.1

            elif char.isalpha():
                step_data["character"] = "percussive_pass"

            dataset.append(step_data)

        return dataset


# ==========================================
# 4. PREPROCESSING & ANALYSE
# ==========================================
def main():
    global source_text
    print("--- Start Processing ---")
    
    word_analysis = {} 
    current_word_start_idx = -1
    non_musical_letters_count = 0
    total_alpha_count_in_word = 0

    for i, char_in_text in enumerate(source_text):
        if char_in_text.isalpha():
            if current_word_start_idx == -1:
                current_word_start_idx = i
            total_alpha_count_in_word += 1
            if char_in_text.upper() not in musical_alphabet:
                non_musical_letters_count += 1
        else:
            if current_word_start_idx != -1:
                word_analysis[(current_word_start_idx, i - 1)] = {
                    'non_musical_count': non_musical_letters_count,
                    'total_alpha_count': total_alpha_count_in_word
                }
                current_word_start_idx = -1
                non_musical_letters_count = 0
                total_alpha_count_in_word = 0

    if current_word_start_idx != -1:
        word_analysis[(current_word_start_idx, len(source_text) - 1)] = {
            'non_musical_count': non_musical_letters_count,
            'total_alpha_count': total_alpha_count_in_word
        }

    generator = ErmacoderaScaleGenerator()
    eurythmy_data_list = generator.analyze_text(source_text)


    # ==========================================
    # 5. MIDI GENERIERUNG MIT CC MODULATIONEN
    # ==========================================
    CC_SPACE_WIDTH = 20
    CC_FREQ_SHIFT = 21
    CC_MOD_INTENSITY = 22

    midi_cc = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)
    current_time = 0.0
    last_pitch = None
    consecutive_count = 0

    for i, eurythmy_entry in enumerate(eurythmy_data_list):
        char = eurythmy_entry['char']

        # Zeit-Reset bei Satzzeichen 
        if char in ['?', '!']:
            current_time += rest_unit_duration_sec
            continue

        # Wort-Kontext abrufen
        current_word_info = next((info for (w_start, w_end), info in word_analysis.items() if w_start <= i <= w_end), None)

        dynamic_duration = note_base_duration_sec
        current_octave_modifier = 0
        current_duration_factor = 1.0

        if current_word_info:
            dynamic_duration += (current_word_info['non_musical_count'] * removed_char_weight_sec)
            if current_word_info['total_alpha_count'] <= short_word_max_length:
                current_duration_factor = staccato_factor
            elif current_word_info['total_alpha_count'] >= long_word_min_length:
                current_octave_modifier = 1

        upper_char = char.upper()
        if upper_char in musical_alphabet:
            total_shift = eurythmy_entry['octave_shift'] + current_octave_modifier
            midi_pitch = get_midi_pitch(upper_char, base_octave + total_shift)

            if midi_pitch is not None:
                # CC Nachrichten VOR der Note einfügen
                instrument.control_changes.append(pretty_midi.ControlChange(CC_SPACE_WIDTH, int(eurythmy_entry['space_width'] * 127), current_time))
                instrument.control_changes.append(pretty_midi.ControlChange(CC_FREQ_SHIFT, int(min(eurythmy_entry['freq_shift'] / 2.0, 1.0) * 127), current_time))
                instrument.control_changes.append(pretty_midi.ControlChange(CC_MOD_INTENSITY, int(eurythmy_entry['mod_intensity'] * 127), current_time))

                # Velocity & Crescendo Logik
                if midi_pitch == last_pitch: 
                    consecutive_count += 1
                else: 
                    consecutive_count = 1
                
                last_pitch = midi_pitch

                vel = 70
                if consecutive_count == 2: 
                    vel = 95
                elif consecutive_count >= 3: 
                    vel = 115

                final_dur = dynamic_duration * current_duration_factor

                # Note hinzufügen
                note = pretty_midi.Note(velocity=vel, pitch=midi_pitch, start=current_time, end=current_time + final_dur)
                instrument.notes.append(note)

                # Quinten-Schichtung
                if consecutive_count == 2:
                    instrument.notes.append(pretty_midi.Note(velocity=vel, pitch=midi_pitch + 7, start=current_time, end=current_time + final_dur))

                current_time += final_dur

                # Verdopplung bei Großbuchstaben
                if char.isupper():
                    current_time += 0.01 # Minimaler Gap
                    instrument.notes.append(pretty_midi.Note(velocity=min(vel + 20, 127), pitch=midi_pitch, start=current_time, end=current_time + final_dur))
                    current_time += final_dur
        else:
            current_time += rest_unit_duration_sec
            last_pitch = None

    midi_cc.instruments.append(instrument)
    output_filename = 'genesis_modulated.mid'
    midi_cc.write(output_filename)
    
    print(f"Erfolgreich generiert: {output_filename} mit CC-Modulationen.")

    # ==========================================
    # 6. ZUSAMMENFASSUNG AUSGEBEN
    # ==========================================
    import time
    import os

    # Warte kurz, damit die Datei sicher auf der Festplatte landet
    time.sleep(0.5) 

    if os.path.exists(output_filename):
        midi_data = pretty_midi.PrettyMIDI(output_filename)
        print(f"\n--- Datei Info ---")
        print(f"Datei: {output_filename}")
        print(f"Dauer: {midi_data.get_end_time():.2f} Sekunden")
        print(f"Anzahl der Instrumente: {len(midi_data.instruments)}")

        for i, inst in enumerate(midi_data.instruments):
            print(f"\nInstrument {i}: {inst.name if inst.name else 'Unnamed'}")
            print(f" - Noten: {len(inst.notes)}")
            print(f" - Control Changes (CC): {len(inst.control_changes)}")
    else:
        print("Fehler: MIDI-Datei konnte nicht gefunden werden.")
    # --- HIER IST DIE BENUTZEROBERFLÄCHE FÜR STREAMLIT ---
import streamlit as st

st.title("Ermacodera Scale System")
st.write("Enter any source text to transform it into a MIDI file using the Ermacodera Scaling system.")

# Das Text-Eingabefeld
user_input = st.text_area("any Source text:", value=source_text, height=200)

if st.button("MIDI generieren"):
    # Wir überschreiben die Quelle kurz mit deiner Eingabe
    source_text = user_input
    
    # Hier rufen wir die Logik auf
    main() 
    
    st.success("Die MIDI-Datei wurde erfolgreich generiert!")
    
    # Den Download-Button anzeigen
    with open("genesis_modulated.mid", "rb") as f:
        st.download_button(
            label="Download MIDI-Datei",
            data=f,
            file_name="Ermacodera_System_Output.mid",
            mime="audio/midi"
        )
