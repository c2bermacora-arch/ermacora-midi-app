import streamlit as st
import mido
import io

class ErmacoderaScaleGenerator:
    def __init__(self, intensity=1.0):
        self.intensity = intensity
        # Volles eurythmisches Alphabet-Mapping für präzise Modulationskurven
        self.vowels = {'a', 'e', 'i', 'o', 'u', 'ä', 'ö', 'ü'}
        self.consonants = {
            'b': 45, 'c': 50, 'd': 55, 'f': 60, 'g': 65, 'h': 30, 'j': 70, 
            'k': 80, 'l': 40, 'm': 35, 'n': 38, 'p': 85, 'q': 90, 'r': 75, 
            's': 62, 't': 58, 'v': 48, 'w': 52, 'x': 95, 'y': 68, 'z': 64, 'ß': 63
        }
        # Spezifische Frequenz-Verschiebungen für Vokale (CC 21)
        self.vowel_shifts = {'a': 80, 'e': 95, 'i': 115, 'o': 60, 'u': 40, 'ä': 85, 'ö': 55, 'ü': 45}

    def process_text(self, text, base_note=60, tempo=120):
        mid = mido.MidiFile(type=0)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        # Exakte Zeiteinstellungen basierend auf BPM
        ticks_per_beat = mid.ticks_per_beat
        tempo_microseconds = mido.bpm2tempo(tempo)
        track.append(mido.MetaMessage('set_tempo', tempo=tempo_microseconds, time=0))
        
        # Konstante rhythmische Unterteilung (16tel Noten)
        step_time = int(ticks_per_beat / 4)
        
        # Initialer Zustand der Modulationsmatrix
        current_cc20 = 64
        current_cc21 = 64
        current_cc22 = 64

        cleaned_text = text.lower()
        
        for char in cleaned_text:
            if char.isspace():
                # Pausen-Struktur: Alle Noten aus, CCs verharren, Zeit vergeht
                track.append(mido.Message('note_off', note=base_note, velocity=0, time=step_time))
                continue
            
            # Interpunktion (Satzzeichen) erzeugt kleine harmonische Sprünge
            if char in {'.', ',', '!', '?'}:
                track.append(mido.Message('control_change', control=20, value=12, time=0))
                track.append(mido.Message('note_off', note=base_note, velocity=0, time=step_time * 2))
                continue

            # 1. Vokal-Modulation (Raumweite & Frequenzverschiebung)
            if char in self.vowels:
                # CC 20 (Space Width) weitet sich bei Vokalen
                current_cc20 = min(127, max(0, int(90 * self.intensity)))
                # CC 21 (Freq Shift) nutzt das spezifische Vokal-Profil
                vowel_val = self.vowel_shifts.get(char, 64)
                current_cc21 = min(127, max(0, int(vowel_val * self.intensity)))
                # CC 22 (Mod Intensity / Konsonanten) flacht ab
                current_cc22 = max(0, int(20 * (2.0 - self.intensity)))
            
            # 2. Konsonanten-Modulation (Plastische Textur)
            elif char in self.consonants:
                # CC 20 zieht sich im Frequenzraum zusammen
                current_cc20 = max(0, int(40 * (2.0 - self.intensity)))
                # CC 21 bleibt stabil im Mittelfeld
                current_cc21 = 50
                # CC 22 (Mod Intensity) wird durch das Konsonanten-Gewicht geformt
                consonant_val = self.consonants.get(char, 64)
                current_cc22 = min(127, max(0, int(consonant_val * self.intensity)))
            
            else:
                # Unbekannte Zeichen ignorieren oder neutral behandeln
                continue

            # CC-Modulationen zeitgleich mit dem Noten-Trigger abfeuern (time=0)
            track.append(mido.Message('control_change', control=20, value=current_cc20, time=0))
            track.append(mido.Message('control_change', control=21, value=current_cc21, time=0))
            track.append(mido.Message('control_change', control=22, value=current_cc22, time=0))
            
            # Note aktivieren und exakt nach der Step-Dauer wieder ausschalten
            track.append(mido.Message('note_on', note=base_note, velocity=95, time=0))
            track.append(mido.Message('note_off', note=base_note, velocity=0, time=step_time))
            
        return mid

# --- INTERNET INTERFACE (Streamlit Layout) ---
st.set_page_config(page_title="Ermacorea WebApp", layout="wide")

st.title("🎛️ Ermacorea: Eurythmische MIDI-Modulationsmatrix")
st.subheader("Konvertiere poetische Texte in komplexe, modulierte MIDI-Partituren")

# Layout-Aufteilung in zwei Spalten
col1, col2 = st.columns([1, 1])

with col1:
    st.header("1. Texteingabe & Parameter")
    user_text = st.text_area(
        "Gib hier deinen Text ein:", 
        value="Genesis. Am Anfang war das Wort und das Wort wurde Klang.", 
        height=280
    )
    
    st.markdown("---")
    st.subheader("Matrix-Skalierung")
    
    # Die Regler zur Live-Steuerung der Generierungs-Engine im Browser
    base_note = st.slider("Basisnote (MIDI)", min_value=21, max_value=108, value=60, help="60 entspricht dem eingestrichenen C")
    tempo = st.slider("Grundtempo (BPM)", min_value=40, max_value=240, value=120)
    intensity = st.slider("Modulations-Intensität (CC Skalierung)", min_value=0.1, max_value=2.0, value=1.0, step=0.1)

with col2:
    st.header("2. MIDI Export")
    st.write("Verarbeite den eingegebenen Text durch die eurythmische Matrix und lade die Datei direkt herunter.")
    
    status_box = st.empty()
    
    if st.button("🎵 MIDI-Datei generieren", type="primary", use_container_width=True):
        if not user_text.strip():
            status_box.error("Bitte gib zuerst einen Text auf der linken Seite ein.")
        else:
            with st.spinner("Berechne eurythmische Modulationspfade (CC 20, 21, 22)..."):
                try:
                    # Instanziierung des vollständigen Skalengenerators
                    generator = ErmacoderaScaleGenerator(intensity=intensity)
                    midi_obj = generator.process_text(user_text, base_note=base_note, tempo=tempo)
                    
                    # Konvertierung der Mido-Daten in einen virtuellen Bytestrom für den Browser-Download
                    midi_buffer = io.BytesIO()
                    midi_obj.save(file=midi_buffer)
                    midi_data = midi_buffer.getvalue()
                    
                    status_box.success("Generierung abgeschlossen! Deine eurythmische Partitur steht bereit.")
                    
                    # Der Download-Button triggert das Speichern im Webbrowser
                    st.download_button(
                        label="💾 Fertige MIDI-Datei herunterladen (.mid)",
                        data=midi_data,
                        file_name="ermacorea_modulated.mid",
                        mime="audio/midi",
                        use_container_width=True
                    )
                except Exception as e:
                    status_box.error(f"Fehler im Algorithmus: {str(e)}")
