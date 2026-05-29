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
    "Das kleine Abenteuer eines Wolkenkindes, das nicht regnen wollte",
    "Wie ein kleiner Sternenfisch das Leuchten im Meer fand",
    "Die geheimnisvolle Reise eines Herbstblattes um die Welt",
    "Der Drache, der lieber Geschichten vorlas statt Feuer zu spucken",
    "Die Fee, die ihre Kristallflügel im Mondschein verlor",
    "Das geheimnisvolle Uhrwerk, das die Zeit anhalten konnte",
    "Der Bär, der Ballett tanzen lernen wollte",
    "Die verzauberte Blume, die nur im Dunkeln leuchtete"
]

THEMES = [
    "Magie und Fantasie (Drachen, Feen, Einhörner, Zauberer)",
    "Abenteuer in der Natur (verzauberte Wälder, Ozeane, Berge)",
    "Magische Gegenstände die lebendig werden (Spielzeug, Bücher)",
    "Fantasiereisen (zu den Sternen, unter das Meer)",
    "Freundschaft und Gefühle (Mut, Güte, Teilen)",
    "Kleine alltägliche Wunder (Jahreszeiten, Pflanzen, Tiere)"
]

def generate_german_kids_topics(num_topics=100):
    """Generate beautiful, imaginative German children's story topics."""

    system = (
        "Du bist ein Kinderbuchautor mit überbordender Fantasie. "
        "Generiere MAGISCHE und POETISCHE Geschichtentitel für Kinder (3-8 Jahre) auf Deutsch. "
        "Jeder Titel soll eine wundervolle Welt voller Abenteuer, Zauberei und Zärtlichkeit heraufbeschwören. "
        "Variiere die Satzanfänge: 'Der/Die/Das... der/die/das...', 'Wie...', 'Die Abenteuer von...', "
        "'Die Reise von...', 'Das Geheimnis von...', 'Die Legende von...' "
        "Keine Nummern. Jeder Titel in einer neuen Zeile. "
        "Sei poetisch und originell - keine generischen Formeln wie 'Der Hund lernt...'"
    )

    prompt = (
        f"Generiere {num_topics} einzigartige und wunderschöne Titel für Kindergeschichten auf Deutsch."
        f"\n\nBeispiele für den gewünschten Stil:"
        f"\n" + "\n".join(f"- {ex}" for ex in EXAMPLES) +
        "\n\nZu erkundende Themen (Abwechslung!):"
        "\n" + "\n".join(f"- {t}" for t in THEMES) +
        "\n\nWICHTIG: Jeder Titel muss einzigartig, poetisch sein und Lust auf die Geschichte machen."
        "\nNur Titel, einer pro Zeile, keine Nummerierung."
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

    print(f"[topics] {num_topics} wunderschöne deutsche Geschichtentitel generieren...")

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
    """200 beautiful German story topics (fallback when API is unavailable)."""
    return [
        "Der kleine Drache, der Angst vor Flammen hatte, aber fliegen lernte",
        "Die Sternenfee, die eines Sommerabends vom Himmel fiel",
        "Die Reise eines Wassertropfens von der Quelle bis zum Meer",
        "Das Geheimnis des Gartens, der nur nachts erblühte",
        "Wie eine kleine Wolke zu einem wunderschönen Regenbogen wurde",
        "Die Spieluhr, die die Melodie aller Erinnerungen spielte",
        "Das Abenteuer eines Papierbootes, das den Ozean überquerte",
        "Das Geheimnis der alten Standuhr, die die Zeit anhalten konnte",
        "Die Legende vom Kristallberg, der im Mondlicht erstrahlte",
        "Das Kätzchen, das eine versteckte Stadt in den Wolken entdeckte",
        "Die unglaubliche Reise einer Feder, die vom Wind getragen wurde",
        "Wie eine kleine Schneeflocke lernte, etwas Besonderes zu sein",
        "Das Geheimnis des Waldes, in dem die Bäume Geschichten flüsterten",
        "Der kleine Stern, der mit den Glühwürmchen spielen wollte",
        "Das Abenteuer eines Zauberbuchs, dessen Geschichten lebendig wurden",
        "Der magische Samen, der bis zum Himmel wuchs",
        "Das Spiegelbild im Wasser, das der beste Freund eines Mädchens wurde",
        "Wie ein Stück Mond in einen verwunschenen Teich fiel",
        "Das Einhorn, das die Quelle aller Farben suchte",
        "Die wundersame Reise eines Herbstblattes um die Welt",
        "Die kleine Hexe, die den Trank der ewigen Freundschaft braute",
        "Der Bär, der beschloss, wie ein Schmetterling zu tanzen",
        "Das Geheimnis der Geige, die die Waldtiere zum Tanzen brachte",
        "Die Rakete aus Spielzeug, die den Mars erkunden wollte",
        "Wie ein verlorenes Lächeln in einem Wunschbrunnen wiedergefunden wurde",
        "Das Glühwürmchen, das das schönste Licht der Welt suchte",
        "Der Drachen, der so hoch flog, dass er die Sterne berührte",
        "Die Rose, die nur im silbernen Mondlicht erblühte",
        "Das Abenteuer eines Schneemanns, der den Frühling sehen wollte",
        "Das Geheimnis des goldenen Schlüssels, der die Traumtür öffnete",
        "Die kleine Meerjungfrau, die ihre Stimme gegen Flügel tauschte",
        "Der kleine Roboter, der die Wärme der Sonne spüren lernte",
        "Wie Sonne und Mond die Hüter des Himmels wurden",
        "Die geheime Kristallhöhle, die Schlaflieder sang",
        "Das Kind, das mit den Tieren sprach und ihre Sprache verstand",
        "Die Schäfchenwolke, die nie Regen bringen wollte",
        "Wie ein kleiner Kieselstein zum wertvollsten Schatz wurde",
        "Die Frühlingsfee, die die schlafenden Blumen weckte",
        "Der hundertjährige Baum, der die Erinnerungen der Welt bewahrte",
        "Die Reise eines Sonnenstrahls durch die Jahreszeiten",
        "Die kleine Bärin, die lernte, am Nachthimmel zu leuchten",
        "Das Geheimnis des Sandes, der die Spuren der Schritte bewahrte",
        "Wie eine Schneeflocke ihre sechs verlorenen Geschwister wiederfand",
        "Der Otter, der den schönsten Damm am Fluss baute",
        "Der Wind, der den Blättern das Tanzen beibrachte",
        "Das Abenteuer einer Flaschenpost, die um die halbe Welt reiste",
        "Der Schmetterling, der auf dem Rücken eines Wals den Ozean überquerte",
        "Wie ein kleiner Löwenzahnsamen das Reisen lernte",
        "Die Sternschnuppe, die auf der Erde einen Freund zum Spielen suchte",
        "Das Geheimnis der schwebenden Insel hinter dem Nebel",
        "Das kleine Gespenst, das Angst vor der Dunkelheit hatte",
        "Wie ein Regenbogen lernte, dass er auch ohne seine Farben schön ist",
        "Die Uhr, die die Zeit zurückdrehen konnte und dem Großvater gehörte",
        "Die Reise einer Freudenträne, die überall Blumen wachsen ließ",
        "Die Katze, die Decken aus Mondlicht webte",
        "Wie eine langsame, aber zielstrebige Schnecke das große Rennen gewann",
        "Der Jahrmarkt der Tiere, wo jeder willkommen war",
        "Das Geheimnis des Spiegels, der nicht das Gesicht, sondern das Herz zeigte",
        "Der kleine Pinguin, der fliegen lernen wollte wie ein Albatros",
        "Wie ein Marienkäfer mit sieben Punkten seinen achten Punkt fand",
        "Die Legende vom Leuchtturm, der die Träume in den Schlaf führte",
        "Die Eule, die Geschichten aus aller Welt sammelte",
        "Der Weg aus gelben Backsteinen, der ins Land der Umarmungen führte",
        "Wie ein auf Post-it gemaltes Lächeln von Hand zu Hand reiste",
        "Der Wal, der den Kindern des Ozeans Schlaflieder sang",
        "Das kleine Schaukelpferd, das durch die Träume eines Kindes galoppierte",
        "Die Zauberlaterne, die die Wege in der Dunkelheit erleuchtete",
        "Wie ein Teddybär lernte, traurige Herzen zu heilen",
        "Das Geheimnis des Wunschbrunnens, der nur im Morgengrauen funktionierte",
        "Das Abenteuer eines rosa Wollfadens, der eine Freundschaftsdecke strickte",
        "Der Dinosaurier, der lieber Blumen aß statt Fleisch",
        "Wie die Farben des Herbstes lernten, anmutig zu fallen",
        "Das Geheimnis des Baumhauses, das jede Nacht das Land wechselte",
        "Die kleine Teetasse, die kalte Herzen wärmte",
        "Die Reise einer Kerze, die den Weg nach Hause erleuchtete",
        "Wie ein stacheliger Igel ganz weiche Freunde fand",
        "Das verlassene Klavier, das nach hundert Jahren zum ersten Mal wieder spielte",
        "Der Schatten, der lieber ein Freund sein wollte als zu erschrecken",
        "Wie ein Loch in einem Baum zur Tür einer Zauberwelt wurde",
        "Die kleine innere Stimme, die einem Kind beibrachte, sich selbst zu lieben",
        "Die Reise eines roten Schals durch die Jahreszeiten und Länder",
        "Der Komodowaran, der davon träumte, sanft wie ein Kätzchen zu sein",
        "Wie ein Tintenfleck auf einem Blatt Papier zum Meisterwerk wurde",
        "Die Hüterin der Träume, die Albträume von schönen Träumen trennte",
        "Die kleine Lokomotive, die sich nicht aus ihrem Tunnel traute",
        "Wie ein zerbrochener Spiegel lernte, dass seine Scherben noch schön waren",
        "Das Abenteuer eines Reiskorns, das die Welt ernähren wollte",
        "Die Zahnfee, die ihren Zauberstaub verloren hatte",
        "Das Geheimnis des Narwalhorns, das Wünsche erfüllte",
        "Wie eine alte Eiche und eine junge Eichel ihre Weisheit teilten",
        "Der Farbendieb, der die Welt grau und traurig machte",
        "Die kleine Flamme, die sich nicht traute zu leuchten",
        "Wie eine Pfotenabdruck im Schnee zur Schatzkarte wurde",
        "Das Geheimnis des zugefrorenen Sees, auf dem die Nordlichter tanzten",
        "Die kleine Erbse, die keine Suppe werden wollte, sondern reisen",
        "Die Legende vom Kolibri, der das Feuer zu den Menschen brachte",
        "Wie ein Regenstab lernte, Musik zu machen",
        "Das Kind, das jeden Abend Sterne in seinem Garten pflanzte",
        "Das geheime Rezept der Kekse, die Flügel verliehen",
        "Die Reise einer Engelsfeder, die vom Himmel fiel",
        "Wie ein knurrender Magen zu einer lustigen Symphonie wurde",
        "Die kleine Wanderbibliothek, die durch die Dörfer reiste",
        "Die Nachtigall, die den Vögeln das Singen im Chor beibrachte",
        "Wie ein Kreisverkehr zum fröhlichsten Platz der Welt wurde",
        "Das Abenteuer eines Stromkabels, das eine Lichterkette werden wollte",
        "Das Geheimnis des Dachbodens, wo vergessene Spielzeuge wieder zum Leben erwachten",
        "Wie ein kleines Mädchen ihren Schatten zähmte und mutig wurde",
        "Der Zaubereismann, der Eiscreme mit Erinnerungen herstellte",
        "Ein Sternbild, das sich langweilte und auf die Erde herabstieg",
        "Die Reise einer Seifenblase, die die Sonne berühren wollte",
        "Wie eine Muschel das Rauschen des Ozeans tausend Jahre lang bewahrte",
        "Die Kuckucksuhr, die etwas anderes singen wollte als die Stunde",
        "Das Ungeheuer unter dem Bett, das eigentlich Angst vor Kindern hatte",
        "Wie eine magische Brille die verborgene Schönheit der Welt zeigte",
        "Die kleine Biene, die die letzte Blume der Welt rettete",
        "Das Geheimnis des Morgennebels, der eine Parallelwelt verbarg",
        "Wie ein schnurloses Telefon das wichtigste Wort der Welt übermittelte",
        "Das Abenteuer einer Kastanie, die ihre Kastanien wie Botschaften warf",
        "Das Küken, das sich nicht aus dem Ei traute aus Angst vor der Welt",
        "Wie ein Sommersprossen-Gesicht zur Schatzkarte der Schönheit wurde",
        "Die Legende der Glühwürmchen, die die Geheimnisse des Waldes hüten",
        "Der kleine Tannenbaum, der ein Weihnachtsbaum werden wollte",
        "Wie 'für immer' zum schönsten Wort der Welt wurde",
        "Die Reise einer Madeleine, die Kindheitserinnerungen transportierte",
        "Der Vogel, der sein Nest aus Traumfäden baute",
        "Wie ein Glühwürmchen lernte, dass sein inneres Licht einzigartig war",
        "Das Geheimnis des Morgentaus, der müde Herzen erfrischte",
        "Die Zaubersuppe der Großmutter, die allen Kummer heilte",
        "Wie ein einfacher Tannenzapfen zum schönsten Baum wurde",
        "Der Weg aus weißen Kieselsteinen, der immer nach Hause führte",
        "Das Abenteuer eines lieben Wortes, das von Mund zu Mund reiste",
        "Der Koala, der die Welt erkunden wollte, ohne seinen Baum zu verlassen",
        "Wie ein Gewitter lernte, sanft zu donnern, um niemanden zu erschrecken",
        "Die kleine Meerjungfrau, die lieber an Land ging als zu schwimmen",
        "Das Geheimnis des ersten Schnees, der alles still und schön machte",
        "Wie ein roter Luftballon seinen Weg zurück zum Himmel fand",
        "Die Reise eines Blütendufts durch die Jahreszeiten",
        "Ein leuchtender Pilz, der die Wege im Wald erhellte",
        "Die Legende der Regenbogenbrücke, die zwei Welten verband",
        "Wie eine Welle lernte, nicht zu überschwemmen, sondern zu streicheln",
        "Das kleine Rotkäppchen, das keine Angst vor dem Wolf hatte",
        "Das Geheimnis der Ostereier, die nie gefunden wurden",
        "Eine herzförmige Wolke, die über der Stadt schwebte",
        "Wie eine stehengebliebene Uhr den besten Moment zum Lieben zeigte",
        "Die Reise eines Rosenblatts im Frühlingswind",
        "Die Grille, die Geige spielte, um den Mond in den Schlaf zu wiegen",
        "Wie ein Haufen Laub zu einer Burg voller Erinnerungen wurde",
        "Der kleine Regentropfen, der Angst vor dem Fallen hatte",
        "Das Geheimnis des letzten Herbstblattes, das sich weigerte zu fallen",
        "Das Abenteuer eines Kreidestücks, das magische Türen zeichnete",
        "Wie ein Stock zur schönsten Zauberrute der Welt wurde",
        "Die Reise eines Seesterns, der die Sterne am Himmel sehen wollte",
        "Wie ein Knoten in einem Schal half, das Wichtigste nicht zu vergessen",
        "Der Igel, der jemanden zum Kuscheln suchte",
        "Das Geheimnis des Heubodens, wo die Träume sanft reiften",
        "Das Abenteuer einer Briefmarke, die um die ganze Welt reiste",
        "Wie ein Seufzer der Erleichterung zu einer sanften Brise wurde",
        "Die kleine Geheimnisschachtel, die die schönsten Erinnerungen enthielt",
        "Die Reise eines Löwenzahnsamens, getragen vom Sommerwind",
        "Wie der Regen lernte, in Musik zu fallen",
        "Das Geheimnis der Tür, die nur bei Vollmond erschien",
        "Ein runder Kiesel, der so weit rollte, bis er das Meer sah",
        "Wie ein tiefer Atemzug allen Zorn der Welt besänftigte",
        "Die Reise eines Kusses, der per Post über Kontinente reiste",
        "Die kleine Pfütze, die ein ganzer Ozean werden wollte",
        "Das Geheimnis des warmen Sandes, der die Fußabdrücke bewahrte",
        "Das Abenteuer eines Strohhalms, der die Sterne einsaugen wollte",
        "Wie eine leere Schachtel lernte, dass sie mit Liebe gefüllt werden konnte",
        "Der kleine Bücherwurm, der zwischen den Seiten der Bücher lebte",
        "Das Geheimnis der karierten Decke, die vor Albträumen schützte",
        "Das Abenteuer einer Brotscheibe, die ein goldener Toast werden wollte",
        "Wie eine Strickleiter half, die höchsten Träume zu erreichen",
        "Das Sparschwein, das nicht Geld, sondern Lächeln sammelte",
        "Die Reise eines Zauberworts, das alle Türen öffnete",
        "Ein Vogelnest, gewebt aus Fäden der Zärtlichkeit",
        "Wie eine Pfütze nach dem Regen das ganze Universum spiegelte",
        "Der Wichtel, der nachts kaputtes Spielzeug reparierte",
        "Das Geheimnis des Marmeladenglases, das den Geschmack des Sommers bewahrte",
        "Das Abenteuer eines Buntstifts, der die Unendlichkeit zeichnen wollte",
        "Wie ein Topf Suppe ein ganzes Dorf wärmte",
        "Die Reise eines Apfelkerns, der zum schönsten Baum des Gartens wurde",
        "Ein Gutenachtkuss, der bis ins Land der Träume reiste",
        "Die Legende der Schlittschuhe, die allein unter dem Mond tanzten",
        "Wie eine karierte Decke half, alle Stürme zu überstehen",
        "Das kleine Schaf, das die Kinder zählte, um einzuschlafen",
        "Das Geheimnis des Nistkastens, in den die Vögel ihre Lieder legten",
        "Das Abenteuer einer Schneekugel, die den ganzen Winter enthielt",
        "Wie ein mit Liebe gestrickter Schal das Herz der Welt wärmte",
        "Die Zauberflöte, die sogar Steine zum Tanzen brachte",
        "Die Reise einer Baumrinde, die über sieben Meere segelte",
        "Ein Blütenblatt, das einem müden Marienkäfer als Bett diente",
        "Wie ein Lavendelfeld alle Sorgen vertrieb",
        "Das kleine Schattentheater, in dem die Schatten Geschichten erzählten",
        "Das Geheimnis des ewigen Versteckspiels zwischen Sonne und Mond",
        "Das Abenteuer eines Katzenbarts, der zu einem Zauberpinsel wurde",
        "Wie ein abgenutzter fliegender Teppich seine Schwebekraft wiederfand",
        "Das Rezept der Ruhe für Tage innerer Stürme",
        "Die Reise eines Kinderlachens, das die ganze Galaxie durchquerte",
        "Wie ein Kastanie im Fell eines Hundes um die Welt reiste",
        "Der kleine Astronaut, der in einem Karton die Galaxie erkundete",
        "Das Geheimnis der heißen Maronen, die im Winter Herzen wärmen",
        "Das Abenteuer einer Eichel, die zur Königin des hundertjährigen Waldes wurde",
        "Wie ein Chamäleon lernte, seine Gefühle zu zeigen statt zu verstecken",
        "Die Legende vom Kolibri, der den letzten Regentropfen trank",
        "Wie ein Tautropfen im Sonnenaufgang zum Diamanten wurde",
        "Der verrückte Hutmacher, der maßgeschneiderte Traumhüte fertigte",
        "Die Reise eines Telefonkabels, das die Herzen der Welt verband",
    ]

def save_topics_to_file(topics, filename="topics.txt"):
    """Save topics to file."""
    with open(filename, "w", encoding="utf-8") as f:
        for topic in topics:
            f.write(f"{topic}\n")
    print(f"[topics] {len(topics)} Themen in {filename} gespeichert")

def main():
    """Generate and save beautiful German kids story topics."""
    print("=" * 60)
    print("=== Generator für wunderschöne Kindergeschichten ===")
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
    new_topics = generate_german_kids_topics(num_to_generate)

    all_topics = existing_topics + new_topics
    unique_topics = []
    seen = set()
    for topic in all_topics:
        if topic.lower() not in seen:
            unique_topics.append(topic)
            seen.add(topic.lower())

    save_topics_to_file(unique_topics)

    print("=" * 60)
    print(f"✅ {len(unique_topics)} einzigartige und wunderschöne Themen generiert!")
    print("=" * 60)

if __name__ == "__main__":
    main()
