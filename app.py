import streamlit as st
import google.generativeai as genai

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Unterrichts-Sparringspartner", page_icon="👩‍🏫", layout="wide")

# --- 2. API KEY SETUP ---
# Wir prüfen, ob der Key in den Secrets ist oder geben ein Eingabefeld (für lokales Testen)
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Google API Key eingeben", type="password")

if not api_key:
    st.warning("Bitte gib einen API Key ein, um zu starten.")
    st.stop()

genai.configure(api_key=api_key)

# --- 3. MODEL INITIALISIERUNG ---
@st.cache_resource
def get_model():
    # Wir nutzen ein Modell mit hoher Kapazität für komplexe didaktische Strukturen
    return genai.GenerativeModel('gemini-2.0-flash')

model = get_model()

# --- 4. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 5. DER "PÄDAGOGISCHE KERN" (SYSTEM PROMPT) ---
# Hier definieren wir die DNA des Bots basierend auf deinen Anforderungen.
system_instruction = """
Du bist ein erfahrener Didaktiker und Unterrichtsentwickler, spezialisiert auf den **Lehrplan 21 (Schweiz)**.
Deine Aufgabe ist es, Lehrpersonen als "Sparringspartner" bei der Planung zu unterstützen.

DEINE DIDAKTISCHE HALTUNG & PRINZIPIEN:
Bei jedem Vorschlag MUSST du folgende Prinzipien berücksichtigen:
1. **Offene Aufgabenstellungen:** Vermeide "Schritt-für-Schritt"-Rezepte. Setze auf das Churer Modell oder ähnliche öffnende Formen. Die Schüler sollen Lösungswege selbst finden.
2. **Universal Design for Learning (UDL):** Biete immer Optionen für Repräsentation, Handlung und Engagement an.
3. **Qualitätsmerkmale nach Hilbert Meyer:** Klare Strukturierung, hoher Anteil echter Lernzeit, inhaltliche Klarheit, sinnstiftendes Kommunizieren.
4. **Dialogisches Lernen (Ruf/Gallin):** Kernidee -> Auftrag -> Ich-Du-Wir -> Rückmeldung.
5. **Ermöglichungsdidaktik (Rolf Arnold):** Lernprozesse können nicht erzwungen, nur ermöglicht werden. Fokus auf Selbstwirksamkeit.
6. **Kompetenzorientierung (LP21):** Nicht nur Stoff, sondern Fähigkeiten (Wissen, Wollen, Können).
7. **Beziehungsarbeit:** Der Unterricht soll Interaktion und Beziehung stärken (Lehrperson als Coach).
8. **Future Skills:** Kreativität, Kollaboration (kooperativ), Kritisches Denken, Kommunikation.

DEIN OUTPUT-FORMAT:
- Strukturiere deine Antworten klar (Markdown, Überschriften, Bulletpoints).
- Sei konkret, aber lasse der Lehrperson Freiraum zur Ausgestaltung.
- Wenn nach einer Idee gefragt wird, liefere:
  a) **Kompetenzbezug** (LP21 Kurzreferenz)
  b) **Die "Große Frage" / Das Szenario** (Lernumgebung)
  c) **Lernjob / Offener Auftrag**
  d) **Differenzierungsmöglichkeiten (UDL)**
  e) **Möglicher Abschluss (Reflexion)**

TONALITÄT:
Professionell, wertschätzend, inspirierend, auf Augenhöhe (Kollege zu Kollege).
"""

# --- 6. SIDEBAR: KONTEXT EINSTELLUNGEN ---
with st.sidebar:
    st.header("⚙️ Planungs-Kontext")
    st.markdown("Definiere hier den Rahmen für die KI.")
    
    zyklus = st.selectbox("Zyklus / Stufe", 
                          ["Zyklus 1 (Kindergarten - 2. Klasse)", 
                           "Zyklus 2 (3. - 6. Klasse)", 
                           "Zyklus 3 (Sekundarstufe I)"])
    
    klasse = st.text_input("Spezifische Klasse (z.B. '1. Klasse Mischklasse')", value="1. Klasse")
    fach = st.text_input("Fach / Bereich", value="Mathematik")
    thema = st.text_input("Thema / Inhalt", value="Addition im Zahlenraum 20")
    
    st.markdown("---")
    reset_btn = st.button("Neuen Chat starten 🗑️")
    if reset_btn:
        st.session_state.messages = []
        st.rerun()

# --- 7. UI LOGIK & CHAT ---

st.title("🎓 Unterrichts-Planer AI")
st.markdown(f"**Aktueller Fokus:** {zyklus} | {klasse} | {fach}: *{thema}*")

# Willkommensnachricht (nur visuell, nicht im Prompt-History Speicher, um Token zu sparen)
if not st.session_state.messages:
    st.info("👋 Hallo! Ich bin bereit. Klicke unten auf **'Ideen generieren'**, um einen ersten Entwurf basierend auf deinen Einstellungen zu erhalten, oder stelle eine konkrete Frage.")

# Chat-Verlauf anzeigen
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# --- 8. EINGABE BEREICH ---

# Zwei Wege der Interaktion:
# A) Der "Magic Button" für den Start
# B) Das Chat-Feld für Verfeinerung

col1, col2 = st.columns([1, 4])

start_prompt = ""
if col1.button("🚀 Ideen generieren", use_container_width=True):
    start_prompt = f"Erstelle einen Unterrichtsentwurf für {zyklus}, {klasse} im Fach {fach} zum Thema '{thema}'. Berücksichtige besonders offene Aufträge und das Churer Modell."

user_input = st.chat_input("Verfeinere den Vorschlag oder stelle eine Frage...")

# Logik: Entweder Button oder Textinput löst Aktion aus
prompt_to_send = None

if start_prompt:
    prompt_to_send = start_prompt
elif user_input:
    prompt_to_send = user_input

# --- 9. VERARBEITUNG ---
if prompt_to_send:
    # 1. User Message anzeigen & speichern
    with st.chat_message("user"):
        st.markdown(prompt_to_send)
    st.session_state.messages.append({"role": "user", "parts": prompt_to_send})

    # 2. KI Antwort generieren
    with st.chat_message("model"):
        with st.spinner("Durchforste Lehrplan 21 und methodische Konzepte..."):
            try:
                # Wir bauen den Kontext für das Modell zusammen
                # System Instruction + Chat History + Neuer Prompt
                
                chat = model.start_chat(history=st.session_state.messages)
                
                # Wir fügen die System-Instruction "on the fly" in den Kontext ein 
                # (Gemini API handhabt System Instructions meist bei Model-Init, 
                # aber hier simulieren wir es durch einen prägnanten Pre-Prompt oder 
                # wir nutzen die System Instruction im API Call, falls unterstützt. 
                # Workaround für Streamlit 'chat': Wir senden die Persona beim ersten Call mit oder
                # nutzen einfach den Kontext.)
                
                # Bester Weg für Konsistenz: Wir hängen die System-Anweisung an den Kontext,
                # wenn der Chat leer ist, oder verlassen uns darauf, dass das Modell schlau ist.
                # Hier: Expliziter System-Instruction-Block im Modell-Call ist sauberer,
                # aber da wir `start_chat` nutzen:
                
                full_prompt = prompt_to_send
                if len(st.session_state.messages) == 1: # Erster Prompt
                    full_prompt = system_instruction + "\n\n" + f"Kontext: {zyklus}, {klasse}, {fach}, {thema}.\n\n" + prompt_to_send

                response = chat.send_message(prompt_to_send) # Hier senden wir nur den neuen Teil, history ist im Objekt
                
                # Fallback: Wenn wir stateless arbeiten wollen (besser für System Prompt Kontrolle):
                conversation = [
                    {"role": "user", "parts": system_instruction},
                    {"role": "model", "parts": "Verstanden. Ich bin bereit, als didaktischer Sparringspartner zu agieren."}
                ]
                # Bestehende History anhängen
                conversation.extend(st.session_state.messages)
                
                final_response = model.generate_content(conversation)
                
                st.markdown(final_response.text)
                st.session_state.messages.append({"role": "model", "parts": final_response.text})

            except Exception as e:
                st.error(f"Ein Fehler ist aufgetreten: {e}")
