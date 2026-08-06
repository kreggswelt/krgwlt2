import os
import requests
from urllib.parse import quote
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

EXAMPLES = [
    "Selbstliebe im Alltag",
    "Die Kraft der kleinen Schritte",
    "Achtsamkeit im hektischen Leben",
    "Grenzen setzen ohne Schuldgefühle",
    "Gedankenmuster erkennen und verändern",
    "Gesunde Routinen für innere Ruhe",
    "Der Mut, Nein zu sagen",
    "Dankbarkeit als tägliche Praxis",
    "Selbstvertrauen nach einer Niederlage",
    "Emotionale Intelligenz im Umgang mit Konflikten",
    "Loslassen lernen: Die Kunst des Vergebens",
    "Die Macht der Selbstgespräche",
    "Routinen für ein fokussiertes Leben",
    "Perfektionismus überwinden",
    "Selbstfürsorge als Fundament des Wohlbefindens"
]

THEMES = [
    "Positive Psychologie und Glücksforschung (Dankbarkeit, Optimismus, Flow)",
    "Achtsamkeit und Meditation (Präsenz, Atmung, innere Ruhe)",
    "Selbstwert und Selbstvertrauen (Selbstliebe, Selbstakzeptanz)",
    "Emotionale Gesundheit (Gefühle verstehen, Stressabbau, Resilienz)",
    "Persönliches Wachstum (Ziele, Gewohnheiten, Disziplin)",
    "Beziehungen und Kommunikation (Empathie, Grenzen, aktives Zuhören)"
]

def generate_german_psychology_topics(num_topics=100):
    """Generate psychology / self-improvement topics in German."""

    system = (
        "Du bist Psychologe und Life-Coach. "
        "Generiere kurze, einprägsame Themen aus Selbsthilfe und Positiver Psychologie auf Deutsch. "
        "Jedes Thema soll eine praktische Idee für mentale Gesundheit, persönliches Wachstum "
        "oder emotionales Wohlbefinden vermitteln. "
        "Keine Nummern. Jedes Thema in einer neuen Zeile. "
        "Sei konkret, motivierend und abwechslungsreich - keine generischen Formeln."
    )

    prompt = (
        f"Generiere {num_topics} einzigartige und kraftvolle Themen für Selbsthilfe, Psychologie "
        f"und Selbstverbesserung auf Deutsch."
        f"\n\nBeispiele für den gewünschten Stil:"
        f"\n" + "\n".join(f"- {ex}" for ex in EXAMPLES) +
        "\n\nZu erkundende Themen (Abwechslung!):"
        "\n" + "\n".join(f"- {t}" for t in THEMES) +
        "\n\nWICHTIG: Jedes Thema muss einzigartig, konkret und praktisch anwendbar sein."
        "\nNur Themen, eines pro Zeile, keine Nummerierung."
    )

    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "temperature": 1.3
    }

    print(f"[topics] {num_topics} Psychologie-Selbsthilfe-Themen generieren...")

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"].strip()

        topics = [line.strip() for line in text.split('\n') if line.strip()]

        cleaned_topics = []
        for topic in topics:
            topic = topic.lstrip('0123456789.-) ')
            if len(topic) > 15 and not topic.startswith('['):
                cleaned_topics.append(topic)

        if len(cleaned_topics) < num_topics:
            print(f"[topics] {len(cleaned_topics)} generiert, ergänze mit lokalen Themen...")
            fallback_needed = num_topics - len(cleaned_topics)
            cleaned_topics.extend(get_fallback_topics()[:fallback_needed])

        return cleaned_topics[:num_topics]

    except Exception as e:
        print(f"[topics] API-Fehler: {e}. Verwende lokale Themen.")
        return get_fallback_topics()[:num_topics]

def get_fallback_topics():
    """200 psychology / self-improvement topics (fallback when API is unavailable)."""
    return [
        "Selbstliebe im Alltag",
        "Die Kraft der kleinen Schritte",
        "Achtsamkeit im hektischen Leben",
        "Grenzen setzen ohne Schuldgefühle",
        "Gedankenmuster erkennen und verändern",
        "Gesunde Routinen für innere Ruhe",
        "Der Mut, Nein zu sagen",
        "Dankbarkeit als tägliche Praxis",
        "Selbstvertrauen nach einer Niederlage",
        "Emotionale Intelligenz im Umgang mit Konflikten",
        "Loslassen lernen: Die Kunst des Vergebens",
        "Die Macht der Selbstgespräche",
        "Routinen für ein fokussiertes Leben",
        "Perfektionismus überwinden",
        "Selbstfürsorge als Fundament des Wohlbefindens",
        "Wie man Stress in Energie verwandelt",
        "Die Psychologie der Gewohnheiten",
        "Gesundes Selbstwertgefühl aufbauen",
        "Mit Ängsten umgehen lernen",
        "Warum Pausen dich produktiver machen",
        "Selbstdisziplin ohne Selbstbestrafung",
        "Positive Gedanken kultivieren",
        "Die Kunst des aktiven Zuhörens",
        "Emotionen benennen und verstehen",
        "Besser mit Kritik umgehen",
        "Die Wissenschaft des Glücks",
        "Innere Ruhe in stürmischen Zeiten",
        "Von Vergleich zu Inspiration",
        "Grenzen für gesunde Beziehungen",
        "Selbstmitgefühl in schwierigen Momenten",
        "Wie man negative Gedankenspiralen stoppt",
        "Die Kraft der Morgenroutine",
        "Achtsames Essen für mehr Wohlbefinden",
        "Die Verbindung zwischen Körper und Geist",
        "Bessere Entscheidungen durch Klarheit",
        "Wie man Aufschieberitis überwindet",
        "Die Psychologie des Glücks",
        "Selbstachtung im digitalen Zeitalter",
        "Freundlichkeit beginnt bei dir selbst",
        "Wachstumsdenken: Der Schlüssel zum Lernen",
        "Die Bedeutung von Pausen für die Kreativität",
        "Wie man mit Unsicherheit umgeht",
        "Selbstwirksamkeit stärken",
        "Die Kunst der gesunden Selbstbeobachtung",
        "Emotionale Regulation im Alltag",
        "Warum Bewegung die Stimmung hebt",
        "Die Kraft der Visualisierung",
        "Akzeptanz: Was ist, ist",
        "Selbstvertrauen im Beruf stärken",
        "Der Umgang mit innerer Kritik",
        "Flow-Zustände im Alltag finden",
        "Wie man alte Muster durchbricht",
        "Die Psychologie der Motivation",
        "Ruhig bleiben in Konfliktsituationen",
        "Selbstachtung und Selbstfürsorge",
        "Die Bedeutung von Schlaf für die Psyche",
        "Wie man sich selbst nicht verliert",
        "Empathie: Die Brücke zu anderen",
        "Die Kraft der Vergebung",
        "Mehr Zufriedenheit durch weniger Erwartungen",
        "Selbstbewusstsein: Es ist erlernbar",
        "Grenzen in der Arbeit setzen",
        "Wie man mit Rückschlägen umgeht",
        "Die Psychologie hinter guten Gewohnheiten",
        "Innere Stärke durch Selbstreflexion",
        "Wie man seine Emotionen steuert",
        "Die Kunst, im Moment zu leben",
        "Selbstwert und soziale Medien",
        "Von Angst zu Mut",
        "Die Bedeutung von Selbstakzeptanz",
        "Wie man mit Einsamkeit umgeht",
        "Positive Affirmationen richtig nutzen",
        "Die Psychologie des Loslassens",
        "Mehr Energie durch Achtsamkeit",
        "Wie man seine Komfortzone erweitert",
        "Selbstfürsorge für Überarbeitete",
        "Die Kunst, sich selbst zu vergeben",
        "Emotionale Grenzen verstehen",
        "Wie man innere Klarheit findet",
        "Die Psychologie der Dankbarkeit",
        "Optimismus trainieren",
        "Wie man aus Fehlern lernt",
        "Selbstmitgefühl im Alltag",
        "Die Macht der Gedanken",
        "Gesunde Eifersucht verstehen",
        "Wie man Gelassenheit entwickelt",
        "Die Wissenschaft der Resilienz",
        "Selbstbewusst kommunizieren",
        "Wie man Ängste entkräftet",
        "Die Kunst des Nein-Sagens",
        "Mehr Freude an den kleinen Dingen",
        "Wie man Stressfallen erkennt",
        "Die Psychologie der Veränderung",
        "Selbstvertrauen durch Kompetenz",
        "Wie man mit Prokrastination umgeht",
        "Die Bedeutung von Selbstreflexion",
        "Achtsame Kommunikation",
        "Wie man innere Ruhe findet",
        "Die Kraft der täglichen Dankbarkeit",
        "Selbstdisziplin aufbauen",
        "Wie man seine Denkmuster hinterfragt",
        "Die Psychologie der Zufriedenheit",
        "Emotionale Freiheit erreichen",
        "Wie man negative Gewohnheiten abbaut",
        "Selbstfürsorge und Grenzen",
        "Die Kunst, Geduld zu entwickeln",
        "Wie man sein Selbstwertgefühl schützt",
        "Die Macht der Prioritäten",
        "Gesunde Work-Life-Balance",
        "Wie man mit Enttäuschungen umgeht",
        "Die Psychologie des Erfolgs",
        "Selbstbewusstsein in sozialen Situationen",
        "Wie man seine Stärken erkennt",
        "Die Bedeutung von Selbstachtung",
        "Innere Motivation finden",
        "Wie man Ärger produktiv nutzt",
        "Die Kraft der positiven Selbstwahrnehmung",
        "Mehr Fokus durch weniger Ablenkung",
        "Wie man mit Druck umgeht",
        "Die Psychologie der Freundschaft",
        "Selbstvertrauen und Selbstwert",
        "Wie man sich selbst motiviert",
        "Die Kunst des bewussten Lebens",
        "Emotionale Stabilität entwickeln",
        "Wie man seine Ziele erreicht",
        "Die Bedeutung von Selbstliebe",
        "Achtsamkeit für den Alltag",
        "Wie man innere Blockaden löst",
        "Die Psychologie der Hoffnung",
        "Selbstfürsorge in stressigen Zeiten",
        "Wie man seine Gefühle zulässt",
        "Die Kraft der Routine",
        "Mehr Selbstvertrauen im Alltag",
        "Wie man mit Perfektionismus umgeht",
        "Die Kunst des Verzeihens",
        "Positive Psychologie für den Alltag",
        "Wie man seine Komfortzone verlässt",
        "Die Bedeutung von innerer Stärke",
        "Selbstbewusstsein aufbauen",
        "Wie man negative Muster erkennt",
        "Die Psychologie der Ausdauer",
        "Mehr Gelassenheit im Alltag",
        "Wie man sich selbst treu bleibt",
        "Die Kraft der Achtsamkeit",
        "Selbstvertrauen stärken im Beruf",
        "Wie man mit Veränderungen umgeht",
        "Die Kunst der Selbstfürsorge",
        "Emotionale Intelligenz trainieren",
        "Wie man Glück aktiv gestaltet",
        "Die Psychologie der Entscheidungen",
        "Mehr Mut im Alltag",
        "Wie man innere Kritiker beruhigt",
        "Die Bedeutung von gesunden Grenzen",
        "Selbstwirksamkeit und Zuversicht",
        "Wie man mit Niederlagen umgeht",
        "Die Kraft der kleinen Erfolge",
        "Achtsames Atmen für innere Ruhe",
        "Wie man sein Mindset verändert",
        "Die Psychologie der Selbstliebe",
        "Mehr Energie durch besseren Schlaf",
        "Wie man seine Zeit bewusst nutzt",
        "Die Kunst des Loslassens",
        "Selbstvertrauen in Beziehungen",
        "Wie man mit Zweifeln umgeht",
        "Die Macht der Gewohnheiten",
        "Innere Ruhe durch Meditation",
        "Wie man sich selbst wertschätzt",
        "Die Psychologie des Durchhaltens",
        "Mehr Zufriedenheit im Alltag",
        "Wie man mit Kritik umgeht",
        "Die Kunst, sich selbst zu lieben",
        "Selbstfürsorge als Priorität",
        "Wie man seine Denkweise optimiert",
        "Die Bedeutung von Selbstvertrauen",
        "Emotionale Klarheit gewinnen",
        "Wie man seine Stärken nutzt",
        "Die Kraft der Achtsamkeit im Beruf",
        "Mehr Selbstachtung im Alltag",
        "Wie man innere Balance findet",
        "Die Psychologie der Veränderung",
        "Selbstbewusstsein durch Selbstkenntnis",
        "Wie man Ängste überwindet",
        "Die Kunst der emotionalen Freiheit",
        "Mehr Ruhe im hektischen Alltag",
        "Wie man seine Grenzen respektiert",
        "Die Bedeutung von Selbstreflexion",
        "Selbstfürsorge für die Psyche",
        "Wie man seine Gedanken steuert",
        "Die Kraft der positiven Einstellung",
        "Mehr Selbstvertrauen in schwierigen Zeiten",
        "Wie man mit Stress umgeht",
        "Die Psychologie der Zufriedenheit",
        "Innere Stärke finden",
        "Wie man sich selbst organisiert",
        "Die Kunst der Achtsamkeit",
        "Mehr Lebensfreude im Alltag",
        "Wie man seine Komfortzone erweitert",
        "Die Bedeutung von Selbstliebe und Akzeptanz",
        "Selbstvertrauen durch kleine Erfolge",
        "Wie man seine Emotionen reguliert",
        "Die Kraft der bewussten Atmung",
        "Mehr Fokus und Klarheit",
        "Wie man innere Ruhe bewahrt",
        "Die Psychologie der Gewohnheiten",
        "Selbstfürsorge im hektischen Alltag",
        "Wie man mit Erwartungen umgeht",
        "Die Kunst, sich selbst zu motivieren",
        "Mehr Selbstbewusstsein im Alltag",
        "Wie man seine Ängste versteht",
        "Die Bedeutung von emotionaler Gesundheit",
        "Selbstvertrauen und innere Ruhe",
        "Wie man positive Gewohnheiten etabliert",
        "Die Kraft der Selbstakzeptanz",
        "Mehr Gelassenheit durch Achtsamkeit",
        "Wie man seine Grenzen kennt",
        "Die Psychologie der inneren Ruhe",
        "Selbstfürsorge und Selbstwertgefühl",
        "Wie man seine Gedanken ordnet",
        "Die Kunst, im Gleichgewicht zu bleiben",
        "Mehr Zufriedenheit durch Selbstliebe",
    ]

def save_topics_to_file(topics, filename="topics.txt"):
    """Save topics to file."""
    with open(filename, "w", encoding="utf-8") as f:
        for topic in topics:
            f.write(f"{topic}\n")
    print(f"[topics] {len(topics)} Themen in {filename} gespeichert")

def main():
    """Generate and save psychology / self-improvement topics."""
    print("=" * 60)
    print("=== Generator für Psychologie- und Selbsthilfe-Themen ===")
    print("=" * 60)

    try:
        with open("topics.txt", "r", encoding="utf-8") as f:
            existing_topics = [line.strip() for line in f if line.strip()]

        if len(existing_topics) >= 50:
            print(f"[topics] {len(existing_topics)} Themen gefunden. Keine neuen Themen erforderlich.")
            return
        else:
            print(f"[topics] Nur {len(existing_topics)} Themen gefunden. Generiere neue...")
    except FileNotFoundError:
        print("[topics] Datei topics.txt existiert nicht. Generiere neue Themen...")
        existing_topics = []

    num_to_generate = 100
    new_topics = generate_german_psychology_topics(num_to_generate)

    all_topics = existing_topics + new_topics
    unique_topics = []
    seen = set()
    for topic in all_topics:
        if topic.lower() not in seen:
            unique_topics.append(topic)
            seen.add(topic.lower())

    save_topics_to_file(unique_topics)

    print("=" * 60)
    print(f"✅ {len(unique_topics)} einzigartige und kraftvolle Themen generiert!")
    print("=" * 60)

if __name__ == "__main__":
    main()
