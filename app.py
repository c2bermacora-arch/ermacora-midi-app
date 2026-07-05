import streamlit as st
import pretty_midi
import re
import os
import pandas as pd
import plotly.express as px

# =====================================================================
# INTERNER ENGINE-CODE
# =====================================================================
class ETSCS_Total_System:
    """
    Ermacora-Codera Total System (ETSCS)
    A text-to-MIDI translation engine based on eurythmic musical rules.
    """
    def __init__(self, text, base_octave=4, note_duration=0.250):
        self.text = text
        self.base_octave = base_octave
        self.std_duration = note_duration
        self.alphabet = {'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'H':11,'B':11}
        self.musical_alphabet_list = list(self.alphabet.keys())

    def process(self):
        midi = pretty_midi.PrettyMIDI()
        inst = pretty_midi.Instrument(program=19) # Church Organ
        current_time = 0.0

        tempo_mult = 1.0
        sentence_octave_offset = 0
        dec_active = False
        dec_step = 0
        dec_vals = [90, 70, 50, 30]
        sustain_active = False

        paragraphs = re.split(r'\n{2,}', self.text)

        for paragraph in paragraphs:
            tempo_mult = 1.0
            sentence_octave_offset = 0
            current_time += (self.std_duration * 0.25) * 3 

            sentences = re.split(r'([.!?]+)', paragraph)
            sentence_parts = []
            for i in range(0, len(sentences)-1, 2):
                sentence_parts.append(sentences[i] + sentences[i+1])
            if len(sentences) % 2 != 0:
                sentence_parts.append(sentences[-1])

            for sentence in sentence_parts:
                if '!!!' in sentence or '???' in sentence: sentence_octave_offset = 0
                elif '!!' in sentence: sentence_octave_offset = 2
                elif '!' in sentence: sentence_octave_offset = 1
                elif '??' in sentence: sentence_octave_offset = -2
                elif '?' in sentence: sentence_octave_offset = -1

                words = sentence.split()
                for w_idx, word in enumerate(words):
                    clean_w = re.sub(r'[^a-zA-ZäöüÄÖÜß]', '', word)
                    if not clean_w and not any(c in word for c in ',.:;'):
                        current_time += (self.std_duration * 0.25)
                        continue

                    is_first_word = (w_idx == 0)
                    is_last_word = (w_idx == len(words) - 1)

                    non_musical = [c for c in clean_w if c.upper() not in self.musical_alphabet_list]
                    word_base_dur = self.std_duration + (len(non_musical) * 0.050)

                    word_oct_shift = 1 if len(clean_w) >= 9 else 0
                    staccato = 0.4 if 0 < len(clean_w) < 3 else 1.0

                    last_pitch, consecutive = None, 0

                    for c_idx, char in enumerate(word):
                        if char == ',': tempo_mult = 0.5 if tempo_mult == 1.0 else 1.0
                        elif char == '.': tempo_mult = 1.0
                        elif char == ':': tempo_mult *= 2.0
                        elif char == ';': current_time += (self.std_duration * 0.5)

                        if '...' in word and not sustain_active:
                            inst.control_changes.append(pretty_midi.ControlChange(64, 127, current_time))
                            sustain_active = True
                        elif sustain_active and '.' in char:
                            inst.control_changes.append(pretty_midi.ControlChange(64, 0, current_time))
                            sustain_active = False

                        if c_idx > 0 and char.isalpha() and char.lower() == word[c_idx-1].lower():
                            dec_active = True
                            dec_step = 0

                        upper_c = char.upper()
                        if upper_c in self.alphabet:
                            pitch = (self.base_octave + sentence_octave_offset + word_oct_shift + 1) * 12 + self.alphabet[upper_c]

                            consecutive = (consecutive + 1) if pitch == last_pitch else 1
                            velocity = {1:70, 2:90, 3:110}.get(consecutive, 127)

                            if dec_active:
                                velocity = dec_vals[dec_step]
                                dec_step = min(dec_step + 1, len(dec_vals)-1)
                                if dec_step == len(dec_vals)-1: dec_active = False

                            if is_first_word: velocity = min(127, velocity + 15)

                            eff_dur = word_base_dur * tempo_mult * staccato
                            if is_last_word and c_idx == len(word)-1: eff_dur *= 1.4

                            reps = 2 if char.isupper() else 1
                            for r in range(reps):
                                v = min(127, velocity + (20 if r > 0 else 0))
                                inst.notes.append(pretty_midi.Note(v, pitch, current_time, current_time + eff_dur))

                                if consecutive == 2:
                                    inst.notes.append(pretty_midi.Note(v, pitch + 7, current_time, current_time + eff_dur))
                                elif consecutive >= 3:
                                    inst.notes.append(pretty_midi.Note(v, pitch + 4, current_time, current_time + eff_dur))
                                    inst.notes.append(pretty_midi.Note(v, pitch + 7, current_time, current_time + eff_dur))

                                if c_idx == len(word)-1: 
                                    inst.notes.append(pretty_midi.Note(v, pitch + 12, current_time, current_time + eff_dur))

                                current_time += eff_dur
                            last_pitch = pitch
                        else:
                            current_time += (self.std_duration * 0.25)

        midi.instruments.append(inst)
        return midi

# =====================================================================
# STREAMLIT UI & ADEQUATE VISUALISIERUNG
# =====================================================================

st.markdown("<h1 style='text-align: left;'>E-CODERA SYSTEM<br><span style='font-size: 20px; font-weight: normal;'>Developed by Felix Ermacora</span></h1>", unsafe_allow_html=True)

st.title("A SYSTEM That")
st.write("Converts linguistic structures into polyphonic MIDI data using algorithmic modeling.")

st.sidebar.header("System Parameters")
base_octave = st.sidebar.slider("Reference Octave", min_value=1, max_value=7, value=4)
note_duration = st.sidebar.slider("Standard Element Duration (Seconds)", min_value=0.05, max_value=1.0, value=0.25, step=0.01)

default_text = "Die Schöpfung: Siebentagewerk / Im Anfang schuf Gott den Himmel und die Erde Und die Erde war wüst und leer // The Creation: Seven-Day Work. In the beginning, God created the heaven and the earth. And the earth was waste and void. // Hē Ktisis: Hē tōn heptā hēmerōn ergasia. En archēi epoiēsen ho Theos ton ouranon kai tēn gēn. Hē de gē ēn aoratos kai akataskeuastos."
user_input = st.text_area("Input text for generative synthesis:", value=default_text, height=180)

if st.button("Generate & analyze MIDI architecture", type="primary"):
    if user_input.strip() == "":
        st.warning("Please input your text first.")
    else:
        system = ETSCS_Total_System(user_input, base_octave=base_octave, note_duration=note_duration)
        midi_data = system.process()
        
        filename = ""E_Codera_System_Felix_Ermacora.mid"
        midi_data.write(filename)
        
        st.success("MIDI architecture successfully calculated!")
        
        # --- DOWNLOAD BEREICH ---
        with open(filename, "rb") as f:
            st.download_button(
                label="📥 Download MIDI Architecture",
                data=f,
                file_name=filename,
                mime="audio/midi",
                use_container_width=True
            )
            
        st.info("🎵 **🎵 Playback Notice: Web browsers cannot natively playback raw MIDI matrix data. Please download the file and map it into your digital audio workspace (e.g., Ableton Live 12 or your AUM iPad matrix) to sculpt it with your custom synthesizer configurations and physical hardware chains.")
            
        # =====================================================================
        # VISUALISIERUNG: Interaktives MIDI Piano Roll
        # =====================================================================
        st.write("---")
        st.subheader("📊 Structural Visualization (Linguistic Frequency Pattern")
        
        notes_list = []
        for instrument in midi_data.instruments:
            for note in instrument.notes:
                notes_list.append({
                    "Note": pretty_midi.note_number_to_name(note.pitch),
                    "Midi Pitch": note.pitch,
                    "Start (s)": note.start,
                    "End (s)": note.end,
                    "Duration (s)": note.end - note.start,
                    "Velocity": note.velocity
                })
        
        if notes_list:
            df = pd.DataFrame(notes_list)
            df = df.sort_values(by="Midi Pitch")
            fig = px.bar(
                df,
                x="Duration (s)", # <--- SO IST ES KORREKT
                y="Note",
                base="Start (s)",
                orientation="h",
                color="Velocity",
                color_continuous_scale="Viridis",
                hover_data=["Midi Pitch", "Start (s)", "End (s)"],
                title="Sound-Timeline (Piano Roll)",
            )
            
            # Ausfallsichere Layout-Syntax!
            fig.update_layout(
                height=500,
                xaxis_title="Timeline (seconds)",
                yaxis_title="Pitch (Note)",
                coloraxis=dict(colorbar=dict(title="Velocity")),
                yaxis={'categoryorder': 'array', 'categoryarray': df['Note'].unique()},
                plot_bgcolor="rgba(20,20,20,0.05)",
                margin=dict(l=50, r=50, t=50, b=50)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("Generated notes (events)", len(df))
            m_col2.metric("Total duration of the piece", f"{midi_data.get_end_time():.2f} Sek.")
            m_col3.metric("Range of notes used", f"{df['Note'].nunique()} various tones")
            
        else:
            st.info("The text contained no musically usable characters from the defined alphabet.")
