# Erklärtexte zu Haushaltstiteln

Eine Datei je Titel (oder Einzelplan), benannt nach der Knoten-ID (`11-1102-63681.md`, `14.md`).
Frontmatter: `id`, `quelle` (Liste von URLs, Pflicht), `stand` (Datum). Darunter der Text: höchstens zwei Sätze,
die sagen, was der Posten ist und wer das Geld bekommt oder warum es gezahlt wird. Keine Wertung.
Der Build (`bht build`) bricht ab, wenn eine Datei keine Quelle hat oder mehr als zwei Sätze enthält.
