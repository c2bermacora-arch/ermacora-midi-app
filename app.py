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
TEXT = Die Schöpfung: Siebentagewerk1 Im Anfang schuf Gott den Himmel und die Erde. 2 Und die Erde war wüst und leer, und Finsternis war über der Tiefe; und der Geist Gottes schwebte über dem Wasser. 3 Und Gott sprach: Es werde Licht! Und es wurde Licht. 4 Und Gott sah das Licht, dass es gut war; und Gott schied das Licht von der Finsternis. 5 Und Gott nannte das Licht Tag, und die Finsternis nannte er Nacht. Und es wurde Abend, und es wurde Morgen: ein Tag. 6 Und Gott sprach: Es werde eine Wölbung mitten im Wasser, und es sei eine Scheidung zwischen dem Wasser und dem Wasser! 7 Und Gott machte die Wölbung und schied das Wasser, das unterhalb der Wölbung, von dem Wasser, das oberhalb der Wölbung war. Und es geschah so. 8 Und Gott nannte die Wölbung Himmel. Und es wurde Abend, und es wurde Morgen: ein zweiter Tag. 9 Und Gott sprach: Es soll sich das Wasser unterhalb des Himmels an einen Ort sammeln, und es werde das Trockene sichtbar! Und es geschah so. 10 Und Gott nannte das Trockene Erde, und die Ansammlung des Wassers nannte er Meere. Und Gott sah, dass es gut war. 11 Und Gott sprach: Die Erde lasse Gras hervorsprossen, Kraut, das Samen hervorbringt, Fruchtbäume, die auf der Erde Früchte tragen nach ihrer Art, in denen ihr Same ist! Und es geschah so. 12 Und die Erde brachte Gras hervor, Kraut, das Samen hervorbringt nach seiner Art, und Bäume, die Früchte tragen, in denen ihr Same ist nach ihrer Art. Und Gott sah, dass es gut war. 13 Und es wurde Abend, und es wurde Morgen: ein dritter Tag. 14 Und Gott sprach: Es sollen Lichter an der Wölbung des Himmels werden, um zu scheiden zwischen Tag und Nacht, und sie werden dienen als Zeichen und Zeiten und Tagen und Jahren; 15 und sie werden als Lichter an der Wölbung des Himmels dienen, um auf die Erde zu leuchten! Und es geschah so. 16 Und Gott machte die beiden großen Lichter: das größere Licht zur Beherrschung des Tages und das kleinere Licht zur Beherrschung der Nacht und die Sterne. 17 Und Gott setzte sie an die Wölbung des Himmels, über die Erde zu leuchten 18 und zu herrschen über den Tag und über die Nacht und zwischen dem Licht und der Finsternis zu scheiden. Und Gott sah, dass es gut war. 19 Und es wurde Abend, und es wurde Morgen: ein vierter Tag. 20 Und Gott sprach: Es soll das Wasser vom Gewimmel lebender Wesen wimmeln, und Vögel sollen über der Erde fliegen unter der Wölbung des Himmels! 21 Und Gott schuf die großen Seeungeheuer und alle sich regenden lebenden Wesen, von denen das Wasser wimmelt, nach ihrer Art, und alle geflügelten Vögel, nach ihrer Art. Und Gott sah, dass es gut war. 22 Und Gott segnete sie und sprach: Seid fruchtbar und vermehrt euch, und füllt das Wasser in den Meeren, und die Vögel sollen sich vermehren auf der Erde! 23 Und es wurde Abend, und es wurde Morgen: ein fünfter Tag. 24 Und Gott sprach: Die Erde bringe lebende Wesen hervor nach ihrer Art: Vieh und kriechende Tiere und Tiere der Erde nach ihrer Art! Und es geschah so. 25 Und Gott machte die Tiere der Erde nach ihrer Art und das Vieh nach seiner Art und alle kriechenden Tiere auf dem Erdboden nach ihrer Art. Und Gott sah, dass es gut war. 26 Und Gott sprach: Lasst uns Menschen machen als unser Bild, uns ähnlich! Sie sollen herrschen über die Fische des Meeres und über die Vögel des Himmels und über das Vieh und über die ganze Erde und über alle kriechenden Tiere, die auf der Erde kriechen! 27 Und Gott schuf den Menschen als sein Bild, als Bild Gottes schuf er ihn; als Mann und Frau schuf er sie. 28 Und Gott segnete sie, und Gott sprach zu ihnen: Seid fruchtbar und vermehrt euch, und füllt die Erde, und macht sie untertan; und herrscht über die Fische des Meeres und über die Vögel des Himmels und über alle Tiere, die sich auf der Erde regen! 29 Und Gott sprach: Siehe, gebe ich euch alles Samen tragende Kraut, das auf der Fläche der ganzen Erde ist, und jeden Baum, an dem Samen tragende Baumfrucht ist: es soll euch zur Nahrung dienen; 30 aber allen Tieren der Erde und allen Vögeln des Himmels und allem, was sich auf der Erde regt, in dem eine lebende Seele ist, alles grüne Kraut zur Speise. Und es geschah so. 31 Und Gott sah alles, was er gemacht hatte, und siehe, es war sehr gut. Und es wurde Abend, und es wurde Morgen: der sechste Tag.

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
    midi_data = pretty_midi.PrettyMIDI(output_filename)
    print(f"\n--- Datei Info ---")
    print(f"Datei: {output_filename}")
    print(f"Dauer: {midi_data.get_end_time():.2f} Sekunden")
    print(f"Anzahl der Instrumente: {len(midi_data.instruments)}")

    for i, inst in enumerate(midi_data.instruments):
        print(f"\nInstrument {i}: {inst.name if inst.name else 'Unnamed'}")
        print(f" - Noten: {len(inst.notes)}")
        print(f" - Control Changes (CC): {len(inst.control_changes)}")

if __name__ == "__main__":
    main()
