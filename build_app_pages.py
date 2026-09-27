#!/usr/bin/env python3
"""Generate the localised Secye app landing pages from app.html.

The page is one file with the copy swapped out, rather than four files edited
by hand. The store badges are identical in every language and their text is
product chrome, so translating it would mean a translator maintaining something
that never changes.
"""
import pathlib
import re

TRANSLATIONS = {
    "es": {
        "legal_page": "es",
        "legal_labels": ["Aviso de privacidad", "T\u00e9rminos", "Aviso m\u00e9dico", "Eliminar mi cuenta", "Legal y privacidad", "Pol\u00edtica de privacidad"],
        "lang": "es",
        "title": "Secye — Escanea una etiqueta y mira qué lleva | Adadeo Ltd",
        "description": (
            "Secye escanea el código de barras de un alimento y muestra una "
            "puntuaci\u00f3n nutricional sobre 100, una evaluaci\u00f3n de alimentos "
            "ultraprocesados y los aditivos que aparecen realmente en la "
            "etiqueta. Gratis en iOS y Android."
        ),
        "og_title": "Secye — Escanea una etiqueta y mira qué lleva",
        "og_desc": (
            "Una puntuaci\u00f3n nutricional sobre 100, una evaluaci\u00f3n de alimentos "
            "ultraprocesados y los aditivos que aparecen realmente en la etiqueta."
        ),
        "tagline": "Escanea una etiqueta. Mira qu\u00e9 lleva de verdad.",
        "get_app": "Consigue la app",
        "ios_pending": "iOS — pr\u00f3ximamente",
        "android_pending": "Android — proximamente",
        "notice": (
            "Secye est\u00e1 en las pruebas finales antes del lanzamiento. Los enlaces "
            "de las tiendas se activan aqu\u00ed el d\u00eda en que se publique cada "
            "ficha: guarda esta pagina y te llevara a la tienda correcta."
        ),
        "what_it_does": "Qu\u00e9 hace",
        "w1_t": "Una puntuacion sobre 100",
        "w1_b": ", no solo una letra, para que un resultado compartido se pueda comprobar.",
        "w2_t": "Evaluacion de alimentos ultraprocesados",
        "w2_b": ", basada en lo que dice la lista de ingredientes.",
        "w3_t": "Los aditivos que estan de verdad",
        "w3_b": (
            ", nombrados por codigo E, incluidos los que no restan puntos pero "
            "conviene conocer."
        ),
        "w4_t": "Fotografa una etiqueta",
        "w4_b": (
            " cuando un producto no aparece en ninguna base de datos, y anadelo tu."
        ),
        "w5_t": "Cuatro idiomas",
        "w5_b": ": ingles, turco, polaco y espanol.",
        "how_it_does": "Como se calcula la puntuacion",
        "p1": (
            "Las notas de Nutri-Score por s\u00ed solas dicen poco: una \u201cA\u201d y una "
            "\u201cD\u201d pueden aparecer en etiquetas con az\u00facar y sal casi id\u00e9nticas. Secye "
            " punt\u00faa el panel por 100 g sobre 100 y despu\u00e9s lee la lista de ingredientes "
            "en busca de se\u00f1ales de procesado, de modo que el n\u00famero y las palabras de la "
            "etiqueta se consideran juntos."
        ),
        "p2": (
            "El modelo lleva version y sus pesos son publico, para que una "
            "puntuacion se pueda reproducir y discutir en lugar de aceptarse por "
            "confianza."
        ),
        "privacy": "Privacidad",
        "priv1": (
            "Una puntuacion es un calculo, no un historial medico, y Secye no "
            "necesita tu identidad para calcularla. Las fotos que envias para un "
            "producto que falta se limpian de datos de ubicacion y de "
            "dispositivo, se borran cuando la entrada esta completa y se "
            "conservan como maximo seis meses. Puedes eliminar tu cuenta y tus "
            "datos desde la propia app."
        ),
        "footer_disc": (
            "Las notas y puntuaciones de Secye son informativas y educativas. Se "
            "basan en datos abiertos de productos, no son consejo medico ni "
            "dietetico, y no son una declaracion de salud certificada. Comprueba "
            "siempre la etiqueta fisica."
        ),
    },
    "pl": {
        "legal_page": "pl",
        "legal_labels": ["Polityka prywatno\u015bci", "Regulamin", "Zastrze\u017ca medyczne", "Usu\u0144 konto", "Dokumenty prawne i prywatno\u015b\u0107", "Polityka prywatno\u015bci"],
        "lang": "pl",
        "title": "Secye — Zeskanuj etykietę i zobacz, co jest w środku | Adadeo Ltd",
        "description": (
            "Secye skanuje kod kreskowy żywności i pokazuje ocenę żywieniową na "
            "100, ocenę żywności ultraprzetworzonej oraz dodatki, które naprawdę "
            "są na etykiecie. Darmowo na iOS i Android."
        ),
        "og_title": "Secye — Zeskanuj etykietę i zobacz, co jest w środku",
        "og_desc": (
            "Ocena żywieniowa na 100, ocena żywności ultraprzetworzonej oraz "
            "dodatki, które naprawdę są na etykiecie."
        ),
        "tagline": "Zeskanuj etykietę. Zobacz, co jest naprawdę w środku.",
        "get_app": "Pobierz aplikację",
        "ios_pending": "iOS — wkrótce",
        "android_pending": "Android — wkrótce",
        "notice": (
            "Secye jest w końcowych testach przed wydaniem. Odnośniki do sklepów "
            "włączą się tutaj w dniu publikacji każdej z nich — dodaj tę stronę "
            "do zakładek, a poprowadzi Cię do właściwego sklepu."
        ),
        "what_it_does": "Co potrafi",
        "w1_t": "Ocena na 100 punktów",
        "w1_b": ", a nie tylko litera — dzięki temu wynik można sprawdzić.",
        "w2_t": "Ocena żywności ultraprzetworzonej",
        "w2_b": ", oparta na tym, co napisano w składzie.",
        "w3_t": "Dodatki, które naprawdę są",
        "w3_b": (
            ", wymienione według kodów E, także te, które nie kosztują punktów, "
            "ale warto o nich wiedzieć."
        ),
        "w4_t": "Zrób zdjęcie etykiety",
        "w4_b": ", gdy produktu nie ma w żadnej bazie, i dodaj go samodzielnie.",
        "w5_t": "Cztery języki",
        "w5_b": ": angielski, turecki, polski i hiszpański.",
        "how_it_does": "Jak liczona jest ocena",
        "p1": (
            "Klasy Nutri-Score mówią niewiele: „A” i „D” mogą znaleźć się na "
            "etykietach z niemal identyczną zawartością cukru i soli. Secye punktuje "
            "panel na 100 g w skali 100, a następnie czyta listę składników w "
            "poszukiwaniu sygnałów przetworzenia, więc liczba i słowa na etykiecie "
            "są rozpatrywane razem."
        ),
        "p2": (
            "Model ma wersję, a jego wagi są publikowane, dzięki czemu wynik można "
            "odtworzyć i przedyskutować, zamiast przyjmować go na zaufanie."
        ),
        "privacy": "Prywatność",
        "priv1": (
            "Ocena jest obliczeniem, nie dokumentacją medyczną, a Secye nie potrzebuje "
            "Twojej tożsamości, żeby jej policzyć. Zdjęcia wysyłane dla brakującego "
            "produktu są czyszczone z danych lokalizacji i urządzenia, usuwane po "
            "uzupełnieniu wpisu i przechowywane maksymalnie sześć miesięcy. Konto i "
            "dane możesz usunąć w aplikacji."
        ),
        "footer_disc": (
            "Oceny i wyniki Secye mają charakter informacyjny i edukacyjny. Oparte są "
            "na otwartych danych o produktach, nie są poradą medyczną ani dietetyczną "
            "i nie stanowią certyfikowanego świadczenia zdrowotnego. Zawsze sprawdzaj "
            "fizyczną etykietę."
        ),
    },
    "tr": {
        "legal_page": "tr",
        "legal_labels": ["Gizlilik politikas\u0131", "Ko\u015fullar", "Sa\u011fl\u0131k uyar\u0131s\u0131", "Hesab\u0131n\u0131 sil", "Hukuki ve gizlilik", "Gizlilik politikas\u0131"],
        "lang": "tr",
        "title": "Secye — Etiketi okut, içinde ne var gör | Adadeo Ltd",
        "description": (
            "Secye bir gıda ürününün barkodunu okur ve 100 üzerinden beslenme "
            "puanını, ultra işlenmiş gıda değerlendirmesini ve etikette gerçekten "
            "yazan katkı maddelerini gösterir. iOS ve Android'de ücretsiz."
        ),
        "og_title": "Secye — Etiketi okut, içinde ne var gör",
        "og_desc": (
            "100 üzerinden beslenme puanı, ultra işlenmiş gıda değerlendirmesi ve "
            "etikette gerçekten yazan katkı maddeleri."
        ),
        "tagline": "Etiketi okut. İçinde ne var, gör.",
        "get_app": "Uygulamayı edin",
        "ios_pending": "iOS — yakında",
        "android_pending": "Android — yakında",
        "notice": (
            "Secye, yayın öncesi son testlerinde. Mağaza bağlantıları her bir "
            "kayıt yayınlandığı gün burada etkinleşecek — bu sayfayı yer imlerine "
            "ekleyin, sizi doğru mağazaya götürsün."
        ),
        "what_it_does": "Neler yapıyor",
        "w1_t": "100 üzerinden puan",
        "w1_b": ", sadece bir harf değil — paylaşılan sonuç böylece kontrol edilebilir.",
        "w2_t": "Ultra işlenmiş gıda değerlendirmesi",
        "w2_b": ", içindekiler listesinde ne yazıyorsa ona dayanır.",
        "w3_t": "Gerçekten etikette olan katkı maddeleri",
        "w3_b": (
            ", E koduyla adlandırılmış olarak; puan düşürmeyenler de bilinmeye değer."
        ),
        "w4_t": "Etiketin fotoğrafını çekin",
        "w4_b": ", ürün hiçbir veritabanında yoksa, ve kendiniz ekleyin.",
        "w5_t": "Dört dil",
        "w5_b": ": İngilizce, Türkçe, Lehçe ve İspanyolca.",
        "how_it_does": "Puan nasıl hesaplanıyor",
        "p1": (
            "Nutri-Score tek başına pek bir şey söylemez: şeker ve tuz bakımından "
            "neredeyse aynı iki etikette bir “A” ile bir “D” yan yana durabilir. "
            "Secye paneli 100 g üzerinden 100 puan üzerinden değerlendirir, "
            "ardından işlenme sinyalleri için içindekiler listesini okur; böylece "
            "sayı ve etiket üzerindeki kelimeler birlikte değerlendirilir."
        ),
        "p2": (
            "Model sürümlüdür ve ağırlıkları yayımlanır; böylece bir puan güvenilerek "
            "kabul edilmek yerine yeniden üretilebilir ve tartışılabilir."
        ),
        "privacy": "Gizlilik",
        "priv1": (
            "Puan bir hesaplamadır, sağlık kaydı değildir; Secye bunu yapmak için "
            "kimliğinizi istemez. Eksik bir ürün için gönderdiğiniz fotoğraflar "
            "konum ve cihaz verilerinden arındırılır, kayıt tamamlandığında silinir "
            "ve en fazla altı ay saklanır. Hesabınızı ve verilerinizi uygulama "
            "içinden silebilirsiniz."
        ),
        "footer_disc": (
            "Secye notları ve puanları bilgilendirme ve eğitim amaçlıdır. Açık ürün "
            "verilerine dayanır, tıbbi veya beslenme tavsiyesi değildir ve sertifikalı "
            "bir sağlık beyanı değildir. Her zaman fiziksel etiketi kontrol edin."
        ),
    },
}


def esc(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(code: str, t: dict) -> str:
    page = pathlib.Path(__file__).with_name("app.html").read_text(encoding="utf-8")

    out = page
    out = out.replace('<html lang="en">', f'<html lang="{t["lang"]}">', 1)
    out = re.sub(r"<title>.*?</title>", f"<title>{esc(t['title'])}</title>", out, count=1, flags=re.S)
    out = re.sub(
        r'<meta name="description" content=".*?">',
        f'<meta name="description" content="{esc(t["description"])}">',
        out, count=1, flags=re.S,
    )
    out = re.sub(
        r'<meta property="og:title" content=".*?">',
        f'<meta property="og:title" content="{esc(t["og_title"])}">',
        out, count=1, flags=re.S,
    )
    out = re.sub(
        r'<meta property="og:description" content=".*?">',
        f'<meta property="og:description" content="{esc(t["og_desc"])}">',
        out, count=1, flags=re.S,
    )
    out = re.sub(
        r"<p class=\"tagline\">.*?</p>",
        f'<p class="tagline">{esc(t["tagline"])}</p>',
        out, count=1, flags=re.S,
    )
    out = out.replace("<h2>Get the app</h2>", f"<h2>{esc(t['get_app'])}</h2>", 1)
    out = out.replace("iOS — coming soon", esc(t["ios_pending"]), 1)
    out = out.replace("Android — coming soon", esc(t["android_pending"]), 1)
    out = re.sub(
        r'<div class="notice">.*?</div>',
        f'<div class="notice">{esc(t["notice"])}</div>',
        out, count=1, flags=re.S,
    )
    out = out.replace("<h2>What it does</h2>", f"<h2>{esc(t['what_it_does'])}</h2>", 1)
    out = out.replace(
        '<li><strong>A score out of 100</strong>, not just a letter grade — so a shared result can actually be checked.</li>',
        f"<li><strong>{esc(t['w1_t'])}</strong>{esc(t['w1_b'])}</li>", 1)
    out = out.replace(
        '<li><strong>Ultra-processed food assessment</strong>, based on what the ingredient list says.</li>',
        f"<li><strong>{esc(t['w2_t'])}</strong>{esc(t['w2_b'])}</li>", 1)
    out = out.replace(
        '<li><strong>The additives that are really there</strong>, named by E-code, including the ones that cost nothing but are worth knowing.</li>',
        f"<li><strong>{esc(t['w3_t'])}</strong>{esc(t['w3_b'])}</li>", 1)
    out = out.replace(
        '<li><strong>Photograph a label</strong> when a product isn\'t in any database, and add it yourself.</li>',
        f"<li><strong>{esc(t['w4_t'])}</strong>{esc(t['w4_b'])}</li>", 1)
    out = out.replace(
        '<li><strong>Four languages</strong>: English, Türkçe, Polski, Español.</li>',
        f"<li><strong>{esc(t['w5_t'])}</strong>{esc(t['w5_b'])}</li>", 1)
    out = out.replace(
        "<h2>How the score works</h2>", f"<h2>{esc(t['how_it_does'])}</h2>", 1)

    # The two body paragraphs of "How the score works", the privacy paragraph and
    # the footer disclaimer, each matched on its stable English opening.
    out = re.sub(
        r"(<h2>[^<]*</h2>\s*)<p>\s*Nutri-Score grades alone.*?</p>",
        lambda m: m.group(1) + f"<p>{esc(t['p1'])}</p>",
        out, count=1, flags=re.S,
    )
    out = re.sub(
        r'<p class="muted">\s*The model is versioned.*?</p>',
        f'<p class="muted">{esc(t["p2"])}</p>',
        out, count=1, flags=re.S,
    )
    out = out.replace("<h2>Privacy</h2>", f"<h2>{esc(t['privacy'])}</h2>", 1)
    out = re.sub(
        r'<p class="privacy-note">\s*A score is a calculation.*?</p>',
        f'<p class="privacy-note">{esc(t["priv1"])}</p>',
        out, count=1, flags=re.S,
    )
    out = re.sub(
        r"<footer>.*?</footer>",
        lambda m: re.sub(
            r"(\s*Secye grades and scores are informational.*?</p>)",
            f"\n        {esc(t['footer_disc'])}",
            m.group(0), count=1, flags=re.S,
        ),
        out, count=1, flags=re.S,
    )

    # Legal links in the reader's own language.
    code_labels = t.get("legal_labels")
    if code_labels:
        privacy_label, terms_label, disc_label, delete_label, legal_label, policy_label = code_labels
        legal = t.get("legal_page", "secye.html")
        out = out.replace(">Privacy policy</a>", f">{policy_label}</a>", 1)
        out = out.replace(">Terms</a>", f">{terms_label}</a>", 1)
        out = out.replace(">Health disclaimer</a>", f">{disc_label}</a>", 1)
        out = out.replace(">Delete your account</a>", f">{delete_label}</a>", 1)
        out = out.replace(">Legal &amp; privacy</a>", f">{legal_label}</a>", 1)
        # Re-point every legal anchor at the localised page.
        out = out.replace('href="secye.html#', f'href="secye-{legal}.html#')

    # Language switch: this one is current, the others are plain links.
    out = out.replace(
        '<a href="app.html" aria-current="page">English</a>',
        f'<a href="app-{code}.html">{ {"es": "Español", "pl": "Polski", "tr": "Türkçe"}[code] }</a>\n'
        f'        <a href="app.html" aria-current="page">English</a>',
        1,
    )
    return out


if __name__ == "__main__":
    here = pathlib.Path(__file__).parent
    for code, t in TRANSLATIONS.items():
        (here / f"app-{code}.html").write_text(build(code, t), encoding="utf-8")
        print(f"  wrote app-{code}.html")
