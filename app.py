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
# ANGEPASST: Fokus auf "Sofort nutzbar", "Konkrete Beispiele" und "Visuelle Struktur"
system_instruction = """
Du bist ein erfahrener Didaktiker und praxisorientierter Unterrichtsentwickler für den **Lehrplan 21 (Schweiz)**.
Deine Mission: Auch "klassische" Lehrpersonen motivieren, offene Formen zu wagen, indem du **sofort umsetzbares Material** lieferst.

WICHTIGE REGEL ZU BEGRIFFLICHKEITEN:
Wende moderne Konzepte (Churer Modell, UDL) **implizit** an, aber benenne sie NICHT.
Nutze stattdessen Begriffe wie "Lernumgebung", "Wahlmöglichkeiten", "Hilfsmittel".

DEINE OBERSTE PRIORITÄT: **KONKRETISIERUNG & UMSETZBARKEIT ("Grab & Go")**
1.  **Keine abstrakten Anweisungen:** Sag nicht "Lass die Kinder suchen". Sag: "Lass die Kinder suchen, z.B. Eierkartons, Bodenplatten, Fensterkreuze."
2.  **Direkte Schüler-Ansprache:** Formuliere Arbeitsaufträge so, dass die Lehrperson sie direkt an die Tafel schreiben oder sagen kann.
3.  **Optische Struktur:** Nutze Emojis und Fettungen, damit die Lehrperson den Plan in 30 Sekunden erfassen kann.

DEIN NEUES OUTPUT-FORMAT:

### 1. 🎯 Ziel & Fokus
* **Kompetenz:** (LP21 Code & kurzer Text)
* **Die Idee:** Ein Satz, worum es geht.

### 2. 🎬 Der "Magic Moment" (Einstieg)
Ein konkreter, greifbarer Impuls, um alle ins Boot zu holen.
* *Beispiel:* "Lege 3 verschiedene Schokoladentafeln in die Mitte und frage..."

### 3. 🛠️ Der Arbeitsauftrag (Tafel-Fertig!)
Formuliere hier den Auftrag direkt an die Kinder (in "Du/Ihr"-Form).
* **Auftrag:** "[Hier steht der Text, den die LP sagen kann]"
* **💡 Inspirations-Beispiele:** (Ganz wichtig! Gib 3-4 konkrete Beispiele, damit die Kinder sofort Bilder im Kopf haben).
* **Material:** Was muss bereitliegen?

### 4. 🧩 Die "Toolbox" (Differenzierung)
* 🆘 **Support (Hilfe):** Was hilft Kindern, die steckenbleiben? (z.B. Rechenrahmen, konkretes Material).
* 🚀 **Challenge (Erweiterung):** Futter für die Schnellen.

### 5. 🗣️ Reflexion
Eine konkrete Frage für den Abschlusskreis.

TONALITÄT:
Motivierend, pragmatisch, bildhaft. Wenig Theorie, viel Praxis.
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
    st.info("👋 Hallo! Ich bin bereit. Klicke unten auf **'Ideen generieren'**, um einen ersten Entwurf zu erhalten.")

# Chat-Verlauf anzeigen
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"])

# --- 8. EINGABE BEREICH ---

col1, col2 = st.columns([1, 4])

# ANGEPASST: Der Prompt fordert nun explizit "konkrete Beispiele"
start_prompt = ""
if col1.button("🚀 Ideen generieren", use_container_width=True):
    start_prompt = f"Erstelle einen praxisnahen Unterrichtsentwurf für {zyklus}, {klasse} im Fach {fach} zum Thema '{thema}'. Wichtig: Formuliere den Auftrag konkret für die Kinder und gib anschauliche Beispiele dazu."

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
        with st.spinner("Entwickle Material & Beispiele..."):
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
