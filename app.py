import streamlit as st
import google.generativeai as genai

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Unterrichts-Sparringspartner", page_icon="👩‍🏫", layout="wide")

# --- 2. API KEY SETUP ---
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
    return genai.GenerativeModel('gemini-2.0-flash')

model = get_model()

# --- 4. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 5. DER "PÄDAGOGISCHE KERN" (SYSTEM PROMPT) ---
# ANGEPASST: Implizite Anwendung der Konzepte ohne Nennung der Fachbegriffe
system_instruction = """
Du bist ein erfahrener Didaktiker und Unterrichtsentwickler, spezialisiert auf den **Lehrplan 21 (Schweiz)**.
Deine Aufgabe ist es, Lehrpersonen als "Sparringspartner" bei der Planung zu unterstützen.

WICHTIGE REGEL ZU BEGRIFFLICHKEITEN:
Wende moderne didaktische Prinzipien (wie Churer Modell, UDL, Ermöglichungsdidaktik) **implizit** an, aber **benenne sie NICHT**. 
Nutze stattdessen praktische Beschreibungen wie "Lernumgebung", "Wahlmöglichkeiten", "Individuelle Lernwege".
Der Begriff "offene Aufträge" darf und soll verwendet werden.

DEINE DIDAKTISCHE ARBEITSWEISE (IMPLIZIT):
1. **Offene Aufgabenstellungen:** Vermeide starre Rezepte. Gib den Schülern Raum für eigene Lösungswege.
2. **Vielfalt als Normalität:** Biete immer Optionen an (verschiedene Materialien, verschiedene Sozialformen, verschiedene Schwierigkeitsgrade), ohne es theoretisch zu begründen.
3. **Fokus auf Lernzeit:** Strukturiere so, dass die Kinder möglichst viel Zeit aktiv mit dem Lerngegenstand verbringen.
4. **Dialog & Rückmeldung:** Plane Phasen ein, in denen Kinder über ihr Lernen sprechen (Ich-Du-Wir).
5. **Kompetenzorientierung (LP21):** Adressiere Wissen, Können und Wollen.

DEIN OUTPUT-FORMAT:
- Strukturiere deine Antworten klar (Markdown, Überschriften, Bulletpoints).
- Sei konkret und direkt im Unterrichtsalltag anwendbar.
- Wenn nach einer Idee gefragt wird, liefere:
  a) **Kompetenzbezug** (LP21 Kurzreferenz)
  b) **Die Lernumgebung / Das Szenario** (Was machen die Kinder?)
  c) **Der offene Auftrag** (Kern der Lektion)
  d) **Differenzierung & Unterstützung** (Wie können schwächere/stärkere Kinder arbeiten?)
  e) **Abschluss / Reflexion**

TONALITÄT:
Professionell, kollegial, praxisnah, auf den Punkt.
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

if not st.session_state.messages:
    st.info("👋 Hallo! Ich bin bereit. Klicke unten auf **'Ideen generieren'**, um einen ersten Entwurf mit offenen Aufträgen zu erhalten.")

# Chat-Verlauf anzeigen
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# --- 8. EINGABE BEREICH ---

col1, col2 = st.columns([1, 4])

# ANGEPASST: Der Prompt im Button nennt keine Theorien mehr
start_prompt = ""
if col1.button("🚀 Ideen generieren", use_container_width=True):
    start_prompt = f"Erstelle einen Unterrichtsentwurf für {zyklus}, {klasse} im Fach {fach} zum Thema '{thema}'. Lege den Fokus auf offene Aufträge und schülerzentrierte Lernformen."

user_input = st.chat_input("Verfeinere den Vorschlag oder stelle eine Frage...")

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
        with st.spinner("Entwickle offene Lernideen..."):
            try:
                chat = model.start_chat(history=st.session_state.messages)
                
                full_prompt = prompt_to_send
                # Wir injizieren die System-Instruction beim ersten Aufruf
                if len(st.session_state.messages) == 1: 
                    full_prompt = system_instruction + "\n\n" + f"Kontext: {zyklus}, {klasse}, {fach}, {thema}.\n\n" + prompt_to_send
                    response = model.generate_content(full_prompt) # Erster Call direkt mit Context
                else:
                    response = chat.send_message(prompt_to_send)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "model", "parts": response.text})

            except Exception as e:
                st.error(f"Ein Fehler ist aufgetreten: {e}")
