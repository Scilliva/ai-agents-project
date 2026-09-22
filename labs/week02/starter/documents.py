"""Week 2 corpus: service requests to the Remerbaach help desk.

Nothing to complete in this file. Read it before you write a prompt.

Remerbaach is a fictional Luxembourg commune and it is the running example
for the whole semester. The messages are synthetic, they were written for
this course, and nothing in them is information about Luxembourg.

Two collections live here.

`DOCS` and `GOLD` are the evaluation set: ten short messages with a gold
annotation each. You score both prompt variants against these, and you never
put any of them into a prompt as an example. An example that also appears in
the evaluation set turns your measurement into a memory test.

`EXAMPLE_POOL` is a separate, held out set of six annotated messages. This is
where few-shot examples come from. It is deliberately larger than the three
to five you should end up using, because choosing is the exercise.

The annotation conventions, which the prompt has to state and which no model
will guess on its own:

  due_date  ISO 8601 (YYYY-MM-DD) when the message states a calendar date,
            in any format or language. None when the message states no date
            or only a relative expression such as "as soon as possible" or
            "before the end of the month". Dates written as DD/MM/YYYY are
            European, because the corpus is.
  quote     A span copied verbatim from the message, supporting the urgency
            decision. It is scored by exact substring search against the
            source, so a paraphrase scores zero.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Doc:
    id: str
    lang: str
    text: str


@dataclass(frozen=True)
class Gold:
    category: str
    urgency: str
    due_date: Optional[str]


# ---------------------------------------------------------------------------
# Evaluation set. Ten records. Never use these as few-shot examples.
# ---------------------------------------------------------------------------

DOCS = [
    Doc("REQ-01", "en",
        "Hello, I cannot sign in to the citizen portal any more. My password "
        "reset email never arrives. I have a residence appointment at the "
        "Bierger-Center tomorrow at 09:00 and I need the confirmation letter "
        "from my account before then. Please help today."),

    Doc("REQ-02", "fr",
        "Bonjour, l'imprimante du service technique au deuxieme etage "
        "n'imprime plus depuis lundi. Elle affiche une erreur de bourrage "
        "papier alors qu'il n'y a pas de papier coince. Nous en aurons besoin "
        "pour la seance du conseil, donc au plus tard le 15/09/2026. Merci."),

    Doc("REQ-03", "de",
        "Guten Tag, auf unserer letzten Rechnung fuer die Kantinennutzung "
        "steht ein Betrag von 480 Euro, wir haben aber nur elf Mittagessen "
        "bestellt. Koennen Sie das bitte pruefen und gegebenenfalls "
        "korrigieren? Es eilt nicht."),

    Doc("REQ-04", "en",
        "The main entrance door of the Bierger-Center did not lock last "
        "night. It is standing open right now and anyone can walk into the "
        "building, including the room where the archive boxes are kept. "
        "Someone needs to come immediately."),

    Doc("REQ-05", "fr",
        "Bonjour, ma nouvelle collegue commence lundi au service population. "
        "Pourriez-vous lui creer un compte sur le portail interne et lui "
        "donner acces au dossier partage du service? Ce n'est pas urgent, "
        "mais ce serait bien avant la fin du mois."),

    Doc("REQ-06", "en",
        "Just so you know: from the next billing cycle our supplier reference "
        "on the water invoices changes from LU-COM-4417 to LU-COM-4419. No "
        "action needed from your side, I am only informing the help desk so "
        "nobody is surprised."),

    Doc("REQ-07", "de",
        "Sehr geehrte Damen und Herren, die Heizung im Sitzungssaal des "
        "Gemeindehauses funktioniert nicht. Die Raumtemperatur liegt bei etwa "
        "vierzehn Grad. Die naechste oeffentliche Sitzung ist am 1. Oktober "
        "2026, bis dahin sollte es repariert sein."),

    Doc("REQ-08", "fr",
        "Le serveur de fichiers du service urbanisme ne repond plus du tout. "
        "Personne dans le service ne peut ouvrir un dossier ce matin et nous "
        "avons trois permis de construire a instruire aujourd'hui. C'est "
        "bloquant pour toute l'equipe."),

    Doc("REQ-09", "en",
        "Hi, is there any chance the help desk could publish its opening "
        "hours somewhere on the intranet? I never remember them and I keep "
        "asking colleagues. Not a problem, just a suggestion."),

    Doc("REQ-10", "en",
        "Could someone please add me to the shared mailbox for building "
        "permits? I was moved to that team last week and I still only see my "
        "own inbox. It would be good to have it before the end of the month."),
]

GOLD = {
    "REQ-01": Gold("access", "urgent", None),
    "REQ-02": Gold("hardware", "standard", "2026-09-15"),
    "REQ-03": Gold("billing", "standard", None),
    "REQ-04": Gold("facilities", "urgent", None),
    "REQ-05": Gold("access", "standard", None),
    "REQ-06": Gold("billing", "info", None),
    "REQ-07": Gold("facilities", "standard", "2026-10-01"),
    "REQ-08": Gold("hardware", "urgent", None),
    "REQ-09": Gold("other", "info", None),
    "REQ-10": Gold("access", "standard", None),
}


# ---------------------------------------------------------------------------
# Held out example pool. Six records. Few-shot examples come from here.
# You do not have to use all of them, and you should not.
# ---------------------------------------------------------------------------

EXAMPLE_POOL = [
    (Doc("EX-01", "en",
         "The badge reader at the side entrance rejects my card since the "
         "system update. I can still get in through the main door, so it is "
         "not blocking me."),
     Gold("access", "standard", None)),

    (Doc("EX-02", "fr",
         "L'ascenseur du batiment administratif est bloque entre le rez et le "
         "premier avec une personne a l'interieur. Intervention immediate "
         "necessaire."),
     Gold("facilities", "urgent", None)),

    (Doc("EX-03", "de",
         "Der Laptop aus dem Sitzungssaal laedt nicht mehr, das Netzteil ist "
         "vermutlich defekt. Ersatz waere bis zum 20/09/2026 gut."),
     Gold("hardware", "standard", "2026-09-20")),

    (Doc("EX-04", "en",
         "For information only: the new intranet search will be switched on "
         "next week. Nothing changes for users."),
     Gold("other", "info", None)),

    (Doc("EX-05", "fr",
         "Nous avons recu deux fois la meme facture pour l'entretien des "
         "espaces verts, reference 2026-0417. Merci de verifier avant le "
         "paiement du 30 septembre 2026."),
     Gold("billing", "standard", "2026-09-30")),

    (Doc("EX-06", "en",
         "The window in office 2.14 will not close and rain is coming in onto "
         "the shared printer below it. This is getting worse by the hour."),
     Gold("facilities", "urgent", None)),
]
