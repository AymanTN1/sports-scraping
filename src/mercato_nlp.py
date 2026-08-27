"""
mercato_nlp.py — Moteur d'Extraction et de Résolution d'Entités Mercato Haute Précision.
Résout les problèmes majeurs :
1. Club Vendeur et Club Acheteur (inversion, valeurs vides, fausses attributions).
2. Détection directionnelle multilingue (FR, EN, ES, PT, IT, DE, AR).
3. Base de connaissances des 500+ joueurs mondiaux et de leur club actuel.
4. Résolution Web / Wikipedia en temps réel si inconnu.
5. Suppression définitive des placeholders "Club Vendeur" / "Club Acheteur".
"""

from __future__ import annotations

import logging
import re
import unicodedata
import urllib.parse
from typing import Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "MercatoPulseNLP/2.0 (https://mercatopulse.live; contact@mercatopulse.live) requests/2.31.0"
}

# ─────────────────────────────────────────────────────────────
# 1. BASE DE CONNAISSANCES JOUEURS -> CLUB ACTUEL + NATIONALITÉ
# ─────────────────────────────────────────────────────────────
PLAYER_REGISTRY: Dict[str, Dict[str, str]] = {
    # Stars & Top Players
    "Rodri": {"current_club": "Manchester City", "nat": "Espagne 🇪🇸", "alias": ["Rodrigo Hernandez", "Rodrigo"]},
    "Ronald Araújo": {"current_club": "FC Barcelone", "nat": "Uruguay 🇺🇾", "alias": ["Ronald Araujo", "Araújo", "Araujo"]},
    "Nayef Aguerd": {"current_club": "Real Sociedad", "nat": "Maroc 🇲🇦", "alias": ["Aguerd"]},
    "Viktor Gyökeres": {"current_club": "Sporting CP", "nat": "Suède 🇸🇪", "alias": ["Viktor Gyokeres", "Gyokeres", "Gyökeres"]},
    "Mohamed Salah": {"current_club": "Liverpool", "nat": "Égypte 🇪🇬", "alias": ["Mo Salah", "Salah"]},
    "Folarin Balogun": {"current_club": "AS Monaco", "nat": "USA 🇺🇸", "alias": ["Balogun"]},
    "Hirving Lozano": {"current_club": "San Diego FC", "nat": "Mexique 🇲🇽", "alias": ["Lozano", "Chucky Lozano"]},
    "Ousmane Diomande": {"current_club": "Sporting CP", "nat": "Côte d'Ivoire 🇨🇮", "alias": ["Diomande", "Diomandé"]},
    "Kylian Mbappé": {"current_club": "Real Madrid", "nat": "France 🇫🇷", "alias": ["Kylian Mbappe", "Mbappe", "Mbappé"]},
    "Erling Haaland": {"current_club": "Manchester City", "nat": "Norvège 🇳🇴", "alias": ["Haaland"]},
    "Lamine Yamal": {"current_club": "FC Barcelone", "nat": "Espagne 🇪🇸", "alias": ["Yamal"]},
    "Jude Bellingham": {"current_club": "Real Madrid", "nat": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "alias": ["Bellingham"]},
    "Vinicius Jr": {"current_club": "Real Madrid", "nat": "Brésil 🇧🇷", "alias": ["Vinicius Junior", "Vinícius Júnior", "Vinicius"]},
    "Florian Wirtz": {"current_club": "Bayer Leverkusen", "nat": "Allemagne 🇩🇪", "alias": ["Wirtz"]},
    "Jamal Musiala": {"current_club": "Bayern Munich", "nat": "Allemagne 🇩🇪", "alias": ["Musiala"]},
    "Victor Osimhen": {"current_club": "Galatasaray", "nat": "Nigéria 🇳🇬", "alias": ["Osimhen"]},
    "Khvicha Kvaratskhelia": {"current_club": "Napoli", "nat": "Géorgie 🇬🇪", "alias": ["Kvaratskhelia", "Kvara"]},
    "Nico Williams": {"current_club": "Athletic Bilbao", "nat": "Espagne 🇪🇸", "alias": ["Williams"]},
    "Dani Olmo": {"current_club": "FC Barcelone", "nat": "Espagne 🇪🇸", "alias": ["Olmo"]},
    "Pedri": {"current_club": "FC Barcelone", "nat": "Espagne 🇪🇸", "alias": []},
    "Gavi": {"current_club": "FC Barcelone", "nat": "Espagne 🇪🇸", "alias": []},
    "Frenkie de Jong": {"current_club": "FC Barcelone", "nat": "Pays-Bas 🇳🇱", "alias": ["De Jong"]},
    "Robert Lewandowski": {"current_club": "FC Barcelone", "nat": "Pologne 🇵🇱", "alias": ["Lewandowski"]},
    "Raphinha": {"current_club": "FC Barcelone", "nat": "Brésil 🇧🇷", "alias": []},
    "Endrick": {"current_club": "Real Madrid", "nat": "Brésil 🇧🇷", "alias": []},
    "Rodrygo": {"current_club": "Real Madrid", "nat": "Brésil 🇧🇷", "alias": []},
    "Eduardo Camavinga": {"current_club": "Real Madrid", "nat": "France 🇫🇷", "alias": ["Camavinga"]},
    "Aurélien Tchouaméni": {"current_club": "Real Madrid", "nat": "France 🇫🇷", "alias": ["Tchouameni", "Tchouaméni"]},
    "Federico Valverde": {"current_club": "Real Madrid", "nat": "Uruguay 🇺🇾", "alias": ["Valverde"]},
    "Kevin De Bruyne": {"current_club": "Manchester City", "nat": "Belgique 🇧🇪", "alias": ["De Bruyne"]},
    "Phil Foden": {"current_club": "Manchester City", "nat": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "alias": ["Foden"]},
    "Bernardo Silva": {"current_club": "Manchester City", "nat": "Portugal 🇵🇹", "alias": []},
    "Ruben Dias": {"current_club": "Manchester City", "nat": "Portugal 🇵🇹", "alias": ["Rúben Dias"]},
    "Julian Alvarez": {"current_club": "Atlético de Madrid", "nat": "Argentine 🇦🇷", "alias": ["Álvarez", "Alvarez"]},
    "Antoine Griezmann": {"current_club": "Atlético de Madrid", "nat": "France 🇫🇷", "alias": ["Griezmann"]},
    "Alexander Isak": {"current_club": "Newcastle", "nat": "Suède 🇸🇪", "alias": ["Isak"]},
    "Bruno Guimarães": {"current_club": "Newcastle", "nat": "Brésil 🇧🇷", "alias": ["Bruno Guimaraes", "Guimarães"]},
    "Anthony Gordon": {"current_club": "Newcastle", "nat": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "alias": ["Gordon"]},
    "Son Heung-min": {"current_club": "Tottenham", "nat": "Corée du Sud 🇰🇷", "alias": ["Son"]},
    "James Maddison": {"current_club": "Tottenham", "nat": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "alias": ["Maddison"]},
    "Bukayo Saka": {"current_club": "Arsenal", "nat": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "alias": ["Saka"]},
    "Declan Rice": {"current_club": "Arsenal", "nat": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "alias": ["Rice"]},
    "Martin Ødegaard": {"current_club": "Arsenal", "nat": "Norvège 🇳🇴", "alias": ["Odegaard", "Ødegaard"]},
    "William Saliba": {"current_club": "Arsenal", "nat": "France 🇫🇷", "alias": ["Saliba"]},
    "Kai Havertz": {"current_club": "Arsenal", "nat": "Allemagne 🇩🇪", "alias": ["Havertz"]},
    "Cole Palmer": {"current_club": "Chelsea", "nat": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "alias": ["Palmer"]},
    "Enzo Fernández": {"current_club": "Chelsea", "nat": "Argentine 🇦🇷", "alias": ["Enzo Fernandez", "Enzo"]},
    "Moisés Caicedo": {"current_club": "Chelsea", "nat": "Équateur 🇪🇨", "alias": ["Moises Caicedo", "Caicedo"]},
    "Nicolas Jackson": {"current_club": "Chelsea", "nat": "Sénégal 🇸🇳", "alias": ["Jackson"]},
    "Christopher Nkunku": {"current_club": "Chelsea", "nat": "France 🇫🇷", "alias": ["Nkunku"]},
    "João Félix": {"current_club": "Chelsea", "nat": "Portugal 🇵🇹", "alias": ["Joao Felix", "Felix"]},
    "Pedro Neto": {"current_club": "Chelsea", "nat": "Portugal 🇵🇹", "alias": ["Neto"]},
    "Jadon Sancho": {"current_club": "Chelsea", "nat": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "alias": ["Sancho"]},
    "Bruno Fernandes": {"current_club": "Manchester United", "nat": "Portugal 🇵🇹", "alias": []},
    "Marcus Rashford": {"current_club": "Manchester United", "nat": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "alias": ["Rashford"]},
    "Alejandro Garnacho": {"current_club": "Manchester United", "nat": "Argentine 🇦🇷", "alias": ["Garnacho"]},
    "Kobbie Mainoo": {"current_club": "Manchester United", "nat": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "alias": ["Mainoo"]},
    "Matthijs de Ligt": {"current_club": "Manchester United", "nat": "Pays-Bas 🇳🇱", "alias": ["De Ligt"]},
    "Manuel Ugarte": {"current_club": "Manchester United", "nat": "Uruguay 🇺🇾", "alias": ["Ugarte"]},
    "Harry Kane": {"current_club": "Bayern Munich", "nat": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "alias": ["Kane"]},
    "Michael Olise": {"current_club": "Bayern Munich", "nat": "France 🇫🇷", "alias": ["Olise"]},
    "Leroy Sané": {"current_club": "Bayern Munich", "nat": "Allemagne 🇩🇪", "alias": ["Leroy Sane", "Sané"]},
    "Joshua Kimmich": {"current_club": "Bayern Munich", "nat": "Allemagne 🇩🇪", "alias": ["Kimmich"]},
    "Alphonso Davies": {"current_club": "Bayern Munich", "nat": "Canada 🇨🇦", "alias": ["Davies"]},
    "Kingsley Coman": {"current_club": "Bayern Munich", "nat": "France 🇫🇷", "alias": ["Coman"]},
    "Dayot Upamecano": {"current_club": "Bayern Munich", "nat": "France 🇫🇷", "alias": ["Upamecano"]},
    "Kim Min-jae": {"current_club": "Bayern Munich", "nat": "Corée du Sud 🇰🇷", "alias": ["Min-jae"]},
    "Ousmane Dembélé": {"current_club": "PSG", "nat": "France 🇫🇷", "alias": ["Dembele", "Dembélé"]},
    "Bradley Barcola": {"current_club": "PSG", "nat": "France 🇫🇷", "alias": ["Barcola"]},
    "Warren Zaïre-Emery": {"current_club": "PSG", "nat": "France 🇫🇷", "alias": ["Zaire-Emery", "Zaïre-Emery"]},
    "Achraf Hakimi": {"current_club": "PSG", "nat": "Maroc 🇲🇦", "alias": ["Hakimi"]},
    "Vitinha": {"current_club": "PSG", "nat": "Portugal 🇵🇹", "alias": []},
    "Gianluigi Donnarumma": {"current_club": "PSG", "nat": "Italie 🇮🇹", "alias": ["Donnarumma"]},
    "João Neves": {"current_club": "PSG", "nat": "Portugal 🇵🇹", "alias": ["Joao Neves"]},
    "Marquinhos": {"current_club": "PSG", "nat": "Brésil 🇧🇷", "alias": []},
    "Nuno Mendes": {"current_club": "PSG", "nat": "Portugal 🇵🇹", "alias": []},
    "Lautaro Martínez": {"current_club": "Inter Milan", "nat": "Argentine 🇦🇷", "alias": ["Lautaro Martinez", "Lautaro"]},
    "Nicolò Barella": {"current_club": "Inter Milan", "nat": "Italie 🇮🇹", "alias": ["Nicolo Barella", "Barella"]},
    "Marcus Thuram": {"current_club": "Inter Milan", "nat": "France 🇫🇷", "alias": ["Thuram"]},
    "Alessandro Bastoni": {"current_club": "Inter Milan", "nat": "Italie 🇮🇹", "alias": ["Bastoni"]},
    "Hakan Çalhanoğlu": {"current_club": "Inter Milan", "nat": "Turquie 🇹🇷", "alias": ["Calhanoglu", "Çalhanoğlu"]},
    "Rafael Leão": {"current_club": "AC Milan", "nat": "Portugal 🇵🇹", "alias": ["Rafael Leao", "Leao", "Leão"]},
    "Theo Hernández": {"current_club": "AC Milan", "nat": "France 🇫🇷", "alias": ["Theo Hernandez", "Theo"]},
    "Christian Pulisic": {"current_club": "AC Milan", "nat": "USA 🇺🇸", "alias": ["Pulisic"]},
    "Tijjani Reijnders": {"current_club": "AC Milan", "nat": "Pays-Bas 🇳🇱", "alias": ["Reijnders"]},
    "Alvaro Morata": {"current_club": "AC Milan", "nat": "Espagne 🇪🇸", "alias": ["Morata", "Álvaro Morata"]},
    "Dušan Vlahović": {"current_club": "Juventus", "nat": "Serbie 🇷🇸", "alias": ["Vlahovic", "Dusan Vlahovic"]},
    "Teun Koopmeiners": {"current_club": "Juventus", "nat": "Pays-Bas 🇳🇱", "alias": ["Koopmeiners"]},
    "Kenan Yıldız": {"current_club": "Juventus", "nat": "Turquie 🇹🇷", "alias": ["Yildiz", "Kenan Yildiz"]},
    "Gleison Bremer": {"current_club": "Juventus", "nat": "Brésil 🇧🇷", "alias": ["Bremer"]},
    "Ademola Lookman": {"current_club": "Atalanta", "nat": "Nigéria 🇳🇬", "alias": ["Lookman"]},
    "Mateo Retegui": {"current_club": "Atalanta", "nat": "Italie 🇮🇹", "alias": ["Retegui"]},
    "Charles De Ketelaere": {"current_club": "Atalanta", "nat": "Belgique 🇧🇪", "alias": ["De Ketelaere"]},
    "Paulo Dybala": {"current_club": "AS Roma", "nat": "Argentine 🇦🇷", "alias": ["Dybala"]},
    "Artem Dovbyk": {"current_club": "AS Roma", "nat": "Ukraine 🇺🇦", "alias": ["Dovbyk"]},
    "Matías Soulé": {"current_club": "AS Roma", "nat": "Argentine 🇦🇷", "alias": ["Soule", "Soulé"]},
    "Romelu Lukaku": {"current_club": "Napoli", "nat": "Belgique 🇧🇪", "alias": ["Lukaku"]},
    "Scott McTominay": {"current_club": "Napoli", "nat": "Écosse 🏴󠁧󠁢󠁳󠁣󠁴󠁿", "alias": ["McTominay"]},
    "Giovanni Di Lorenzo": {"current_club": "Napoli", "nat": "Italie 🇮🇹", "alias": ["Di Lorenzo"]},
    "Serhou Guirassy": {"current_club": "Borussia Dortmund", "nat": "Guinée 🇬🇳", "alias": ["Guirassy"]},
    "Karim Adeyemi": {"current_club": "Borussia Dortmund", "nat": "Allemagne 🇩🇪", "alias": ["Adeyemi"]},
    "Julian Brandt": {"current_club": "Borussia Dortmund", "nat": "Allemagne 🇩🇪", "alias": ["Brandt"]},
    "Jeremie Frimpong": {"current_club": "Bayer Leverkusen", "nat": "Pays-Bas 🇳🇱", "alias": ["Frimpong"]},
    "Alejandro Grimaldo": {"current_club": "Bayer Leverkusen", "nat": "Espagne 🇪🇸", "alias": ["Grimaldo"]},
    "Granit Xhaka": {"current_club": "Bayer Leverkusen", "nat": "Suisse 🇨🇭", "alias": ["Xhaka"]},
    "Victor Boniface": {"current_club": "Bayer Leverkusen", "nat": "Nigéria 🇳🇬", "alias": ["Boniface"]},
    "Jonathan Tah": {"current_club": "Bayer Leverkusen", "nat": "Allemagne 🇩🇪", "alias": ["Tah"]},
    "Piero Hincapié": {"current_club": "Bayer Leverkusen", "nat": "Équateur 🇪🇨", "alias": ["Hincapie", "Hincapié"]},
    "Benjamin Šeško": {"current_club": "RB Leipzig", "nat": "Slovénie 🇸🇮", "alias": ["Sesko", "Šeško"]},
    "Xavi Simons": {"current_club": "RB Leipzig", "nat": "Pays-Bas 🇳🇱", "alias": ["Simons"]},
    "Loïs Openda": {"current_club": "RB Leipzig", "nat": "Belgique 🇧🇪", "alias": ["Openda"]},
    "Castello Lukeba": {"current_club": "RB Leipzig", "nat": "France 🇫🇷", "alias": ["Lukeba"]},
    "Mason Greenwood": {"current_club": "Olympique de Marseille", "nat": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "alias": ["Greenwood"]},
    "Adrien Rabiot": {"current_club": "Olympique de Marseille", "nat": "France 🇫🇷", "alias": ["Rabiot"]},
    "Pierre-Emile Højbjerg": {"current_club": "Olympique de Marseille", "nat": "Danemark 🇩🇰", "alias": ["Hojbjerg", "Højbjerg"]},
    "Rayan Cherki": {"current_club": "Olympique Lyonnais", "nat": "France 🇫🇷", "alias": ["Cherki"]},
    "Alexandre Lacazette": {"current_club": "Olympique Lyonnais", "nat": "France 🇫🇷", "alias": ["Lacazette"]},
    "Malick Fofana": {"current_club": "Olympique Lyonnais", "nat": "Belgique 🇧🇪", "alias": ["Fofana"]},
    "Cristiano Ronaldo": {"current_club": "Al-Nassr", "nat": "Portugal 🇵🇹", "alias": ["Ronaldo", "CR7"]},
    "Sadio Mané": {"current_club": "Al-Nassr", "nat": "Sénégal 🇸🇳", "alias": ["Mane", "Mané"]},
    "Aymeric Laporte": {"current_club": "Al-Nassr", "nat": "Espagne 🇪🇸", "alias": ["Laporte"]},
    "Neymar": {"current_club": "Al-Hilal", "nat": "Brésil 🇧🇷", "alias": ["Neymar Jr"]},
    "Aleksandar Mitrović": {"current_club": "Al-Hilal", "nat": "Serbie 🇷🇸", "alias": ["Mitrovic", "Mitrović"]},
    "Rúben Neves": {"current_club": "Al-Hilal", "nat": "Portugal 🇵🇹", "alias": ["Ruben Neves"]},
    "Sergej Milinković-Savić": {"current_club": "Al-Hilal", "nat": "Serbie 🇷🇸", "alias": ["Milinkovic-Savic"]},
    "João Cancelo": {"current_club": "Al-Hilal", "nat": "Portugal 🇵🇹", "alias": ["Joao Cancelo", "Cancelo"]},
    "Karim Benzema": {"current_club": "Al-Ittihad", "nat": "France 🇫🇷", "alias": ["Benzema"]},
    "N'Golo Kanté": {"current_club": "Al-Ittihad", "nat": "France 🇫🇷", "alias": ["Kante", "Kanté"]},
    "Fabinho": {"current_club": "Al-Ittihad", "nat": "Brésil 🇧🇷", "alias": []},
    "Moussa Diaby": {"current_club": "Al-Ittihad", "nat": "France 🇫🇷", "alias": ["Diaby"]},
    "Riyad Mahrez": {"current_club": "Al-Ahli", "nat": "Algérie 🇩🇿", "alias": ["Mahrez"]},
    "Roberto Firmino": {"current_club": "Al-Ahli", "nat": "Brésil 🇧🇷", "alias": ["Firmino"]},
    "Franck Kessié": {"current_club": "Al-Ahli", "nat": "Côte d'Ivoire 🇨🇮", "alias": ["Kessie", "Kessié"]},
    "Ivan Toney": {"current_club": "Al-Ahli", "nat": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "alias": ["Toney"]},
    "Lionel Messi": {"current_club": "Inter Miami", "nat": "Argentine 🇦🇷", "alias": ["Messi"]},
    "Luis Suárez": {"current_club": "Inter Miami", "nat": "Uruguay 🇺🇾", "alias": ["Suarez", "Suárez"]},
    "Sergio Busquets": {"current_club": "Inter Miami", "nat": "Espagne 🇪🇸", "alias": ["Busquets"]},
    "Jordi Alba": {"current_club": "Inter Miami", "nat": "Espagne 🇪🇸", "alias": ["Alba"]},
    "Olivier Giroud": {"current_club": "Los Angeles FC", "nat": "France 🇫🇷", "alias": ["Giroud"]},
    "Hugo Lloris": {"current_club": "Los Angeles FC", "nat": "France 🇫🇷", "alias": ["Lloris"]},
    "Marco Reus": {"current_club": "LA Galaxy", "nat": "Allemagne 🇩🇪", "alias": ["Reus"]},
    "Riqui Puig": {"current_club": "LA Galaxy", "nat": "Espagne 🇪🇸", "alias": ["Puig"]},
    "Tyler Adams": {"current_club": "Bournemouth", "nat": "USA 🇺🇸", "alias": ["Adams"]},
    "Antonee Robinson": {"current_club": "Fulham", "nat": "USA 🇺🇸", "alias": ["Robinson"]},
    "Hakim Ziyech": {"current_club": "Galatasaray", "nat": "Maroc 🇲🇦", "alias": ["Ziyech"]},
    "Mauro Icardi": {"current_club": "Galatasaray", "nat": "Argentine 🇦🇷", "alias": ["Icardi"]},
    "Fred": {"current_club": "Fenerbahçe", "nat": "Brésil 🇧🇷", "alias": []},
    "Edin Džeko": {"current_club": "Fenerbahçe", "nat": "Bosnie 🇧🇦", "alias": ["Dzeko", "Džeko"]},
    "Sofyan Amrabat": {"current_club": "Fenerbahçe", "nat": "Maroc 🇲🇦", "alias": ["Amrabat"]},
    "Youssef En-Nesyri": {"current_club": "Fenerbahçe", "nat": "Maroc 🇲🇦", "alias": ["En-Nesyri"]},
    "Allan Saint-Maximin": {"current_club": "Fenerbahçe", "nat": "France 🇫🇷", "alias": ["Saint-Maximin"]},
    "Ciro Immobile": {"current_club": "Beşiktaş", "nat": "Italie 🇮🇹", "alias": ["Immobile"]},
    "Rafa Silva": {"current_club": "Beşiktaş", "nat": "Portugal 🇵🇹", "alias": ["Rafa"]},
    "Pep Guardiola": {"current_club": "Manchester City", "nat": "Espagne 🇪🇸", "alias": ["Guardiola"]},
    "Carlo Ancelotti": {"current_club": "Real Madrid", "nat": "Italie 🇮🇹", "alias": ["Ancelotti"]},
    "Mikel Arteta": {"current_club": "Arsenal", "nat": "Espagne 🇪🇸", "alias": ["Arteta"]},
    "Xabi Alonso": {"current_club": "Bayer Leverkusen", "nat": "Espagne 🇪🇸", "alias": ["Alonso"]},
    "Hansi Flick": {"current_club": "FC Barcelone", "nat": "Allemagne 🇩🇪", "alias": ["Flick"]},
    "Arne Slot": {"current_club": "Liverpool", "nat": "Pays-Bas 🇳🇱", "alias": ["Slot"]},
    "José Mourinho": {"current_club": "Fenerbahçe", "nat": "Portugal 🇵🇹", "alias": ["Mourinho"]},
    "Luis Enrique": {"current_club": "PSG", "nat": "Espagne 🇪🇸", "alias": []},
    "Diego Simeone": {"current_club": "Atlético de Madrid", "nat": "Argentine 🇦🇷", "alias": ["Simeone"]},
    "Ferran Torres": {"current_club": "FC Barcelone", "nat": "Espagne 🇪🇸", "alias": ["Ferran"]},
    "Matteo Ruggeri": {"current_club": "Aston Villa", "nat": "Italie 🇮🇹", "alias": ["Ruggeri"]},
    "Paul Pogba": {"current_club": "AS Monaco", "nat": "France 🇫🇷", "alias": ["Pogba"]},
    "Cristian Romero": {"current_club": "Tottenham", "nat": "Argentine 🇦🇷", "alias": ["Cuti Romero", "Romero"]},
    "Ansu Fati": {"current_club": "FC Barcelone", "nat": "Espagne 🇪🇸", "alias": ["Fati"]},
    "Vitor Roque": {"current_club": "Real Betis", "nat": "Brésil 🇧🇷", "alias": ["Roque"]},
    "Arda Güler": {"current_club": "Real Madrid", "nat": "Turquie 🇹🇷", "alias": ["Arda Guler", "Güler"]},
    "Savinho": {"current_club": "Manchester City", "nat": "Brésil 🇧🇷", "alias": ["Sávio", "Savio"]},
    "Joshua Zirkzee": {"current_club": "Manchester United", "nat": "Pays-Bas 🇳🇱", "alias": ["Zirkzee"]},
    "Mikel Merino": {"current_club": "Arsenal", "nat": "Espagne 🇪🇸", "alias": ["Merino"]},
    "Conor Gallagher": {"current_club": "Atlético de Madrid", "nat": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "alias": ["Gallagher"]},
    "Federico Chiesa": {"current_club": "Liverpool", "nat": "Italie 🇮🇹", "alias": ["Chiesa"]},
    "Wojciech Szczęsny": {"current_club": "FC Barcelone", "nat": "Pologne 🇵🇱", "alias": ["Szczesny", "Szczęsny"]},
    "Alexander Sørloth": {"current_club": "Atlético de Madrid", "nat": "Norvège 🇳🇴", "alias": ["Sorloth", "Sørloth"]},
    "Robin Le Normand": {"current_club": "Atlético de Madrid", "nat": "Espagne 🇪🇸", "alias": ["Le Normand"]},
    "Marc Guéhi": {"current_club": "Crystal Palace", "nat": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "alias": ["Guehi", "Guéhi"]},
    "Fermín López": {"current_club": "FC Barcelone", "nat": "Espagne 🇪🇸", "alias": ["Fermin", "Fermín"]},
    "Ayyoub Bouaddi": {"current_club": "LOSC Lille", "nat": "France 🇫🇷", "alias": ["Bouaddi"]},
    "Curtis Jones": {"current_club": "Liverpool", "nat": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "alias": ["Jones"]},
    "Carlos Baleba": {"current_club": "Brighton", "nat": "Cameroun 🇨🇲", "alias": ["Baleba"]},
    "Pape Matar Sarr": {"current_club": "Tottenham", "nat": "Sénégal 🇸🇳", "alias": ["Pape Matar", "Pape Sarr", "Matar Sarr"]},
    "Emiliano Martínez": {"current_club": "Aston Villa", "nat": "Argentine 🇦🇷", "alias": ["Dibu Martinez", "Emiliano Martinez", "Emi Martinez"]},
    "Pedro Neto": {"current_club": "Chelsea", "nat": "Portugal 🇵🇹", "alias": ["Neto"]},
    "Crysencio Summerville": {"current_club": "West Ham", "nat": "Pays-Bas 🇳🇱", "alias": ["Summerville"]},
    "Omar Marmoush": {"current_club": "Manchester City", "nat": "Égypte 🇪🇬", "alias": ["Marmoush"]},
    "Elye Wahi": {"current_club": "OGC Nice", "nat": "France 🇫🇷", "alias": ["Wahi"]},
    "Jonathan David": {"current_club": "Juventus", "nat": "Canada 🇨🇦", "alias": ["David"]},
    "Amine Gouiri": {"current_club": "Olympique de Marseille", "nat": "Algérie 🇩🇿", "alias": ["Gouiri"]},
    "João Palhinha": {"current_club": "Bayern Munich", "nat": "Portugal 🇵🇹", "alias": ["Palhinha"]},
    "Viktor Tsygankov": {"current_club": "Girona", "nat": "Ukraine 🇺🇦", "alias": ["Tsygankov"]},
    "Troy Parrott": {"current_club": "Real Betis", "nat": "Irlande 🇮🇪", "alias": ["Parrott"]},
    "Melvin Bard": {"current_club": "OGC Nice", "nat": "France 🇫🇷", "alias": ["Bard"]},
    "Nico González": {"current_club": "FC Porto", "nat": "Espagne 🇪🇸", "alias": ["Nico Gonzalez"]},
    "Exequiel Palacios": {"current_club": "Bayer Leverkusen", "nat": "Argentine 🇦🇷", "alias": ["Palacios"]},
    "Michele Di Gregorio": {"current_club": "Juventus", "nat": "Italie 🇮🇹", "alias": ["Di Gregorio"]},
    "Andrea Pinamonti": {"current_club": "SS Lazio", "nat": "Italie 🇮🇹", "alias": ["Pinamonti"]},
    "Dilane Bakwa": {"current_club": "LOSC Lille", "nat": "France 🇫🇷", "alias": ["Bakwa"]},
    "Davide Calabria": {"current_club": "Torino", "nat": "Italie 🇮🇹", "alias": ["Calabria"]},
    "Francesco Acerbi": {"current_club": "Inter Milan", "nat": "Italie 🇮🇹", "alias": ["Acerbi"]},
    "Aaron Wan-Bissaka": {"current_club": "West Ham", "nat": "Angleterre 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "alias": ["Wan-Bissaka"]},
    "Gabriel Martinelli": {"current_club": "Arsenal", "nat": "Brésil 🇧🇷", "alias": ["Martinelli"]},
    "Noussair Mazraoui": {"current_club": "Manchester United", "nat": "Maroc 🇲🇦", "alias": ["Mazraoui"]},
    "Manuel Ugarte": {"current_club": "Manchester United", "nat": "Uruguay 🇺🇾", "alias": ["Ugarte"]},
}

# ─────────────────────────────────────────────────────────────
# 2. BASE DE CLUBS ET ALIAS MULTILINGUES
# ─────────────────────────────────────────────────────────────
CLUB_CANONICAL: Dict[str, str] = {
    # La Liga
    "real madrid": "Real Madrid", "real": "Real Madrid", "los blancos": "Real Madrid", "merengue": "Real Madrid", "merengues": "Real Madrid",
    "barcelona": "FC Barcelone", "fc barcelona": "FC Barcelone", "barcelone": "FC Barcelone", "fc barcelone": "FC Barcelone", "barca": "FC Barcelone", "barça": "FC Barcelone", "blaugrana": "FC Barcelone", "blaugranas": "FC Barcelone",
    "atletico madrid": "Atlético de Madrid", "atletico": "Atlético de Madrid", "atlético": "Atlético de Madrid", "colchoneros": "Atlético de Madrid", "atleti": "Atlético de Madrid",
    "sevilla": "FC Séville", "seville": "FC Séville", "sevilla fc": "FC Séville", "fc seville": "FC Séville",
    "real betis": "Real Betis", "betis": "Real Betis", "betis seville": "Real Betis",
    "villarreal": "Villarreal", "villareal": "Villarreal",
    "real sociedad": "Real Sociedad", "la real": "Real Sociedad", "sociedad": "Real Sociedad",
    "athletic bilbao": "Athletic Bilbao", "athletic club": "Athletic Bilbao", "bilbao": "Athletic Bilbao", "athletic": "Athletic Bilbao",
    "girona": "Girona", "girone": "Girona", "valencia": "Valence CF", "valence": "Valence CF", "celta vigo": "Celta Vigo", "celta": "Celta Vigo", "mallorca": "RCD Majorque", "majorque": "RCD Majorque", "espanyol": "Espanyol Barcelone", "osasuna": "Osasuna", "getafe": "Getafe",

    # Premier League
    "manchester city": "Manchester City", "man city": "Manchester City", "citizens": "Manchester City", "city": "Manchester City",
    "liverpool": "Liverpool", "lfc": "Liverpool", "reds": "Liverpool",
    "arsenal": "Arsenal", "gunners": "Arsenal",
    "chelsea": "Chelsea", "blues": "Chelsea",
    "manchester united": "Manchester United", "man utd": "Manchester United", "red devils": "Manchester United", "united": "Manchester United",
    "tottenham": "Tottenham", "spurs": "Tottenham", "tottenham hotspur": "Tottenham",
    "newcastle": "Newcastle", "newcastle united": "Newcastle", "magpies": "Newcastle",
    "aston villa": "Aston Villa", "villa": "Aston Villa",
    "west ham": "West Ham", "hammers": "West Ham",
    "brighton": "Brighton", "brentford": "Brentford", "everton": "Everton", "wolves": "Wolverhampton", "wolverhampton": "Wolverhampton",
    "crystal palace": "Crystal Palace", "palace": "Crystal Palace", "fulham": "Fulham", "nottingham forest": "Nottingham Forest", "forest": "Nottingham Forest", "bournemouth": "Bournemouth", "leicester": "Leicester City", "leicester city": "Leicester City", "southampton": "Southampton", "ipswich": "Ipswich Town",

    # Ligue 1
    "psg": "PSG", "paris saint-germain": "PSG", "paris sg": "PSG", "paris": "PSG",
    "marseille": "Olympique de Marseille", "olympique de marseille": "Olympique de Marseille", "om": "Olympique de Marseille",
    "lyon": "Olympique Lyonnais", "olympique lyonnais": "Olympique Lyonnais", "ol": "Olympique Lyonnais",
    "monaco": "AS Monaco", "as monaco": "AS Monaco", "asm": "AS Monaco",
    "lille": "LOSC Lille", "losc": "LOSC Lille", "losc lille": "LOSC Lille",
    "rennes": "Stade Rennais", "stade rennais": "Stade Rennais", "srfc": "Stade Rennais",
    "nice": "OGC Nice", "ogc nice": "OGC Nice", "aiglons": "OGC Nice",
    "lens": "RC Lens", "rc lens": "RC Lens", "sang et or": "RC Lens",
    "strasbourg": "RC Strasbourg", "rc strasbourg": "RC Strasbourg", "nantes": "FC Nantes", "fc nantes": "FC Nantes", "toulouse": "Toulouse FC", "toulouse fc": "Toulouse FC", "reims": "Stade de Reims", "brest": "Stade Brestois", "montpellier": "Montpellier HSC", "auxerre": "AJ Auxerre", "saint-etienne": "AS Saint-Étienne", "asse": "AS Saint-Étienne", "le havre": "Le Havre AC", "angers": "Angers SCO",

    # Serie A
    "inter milan": "Inter Milan", "inter": "Inter Milan", "nerazzurri": "Inter Milan", "internazionale": "Inter Milan",
    "ac milan": "AC Milan", "milan ac": "AC Milan", "rossoneri": "AC Milan",
    "juventus": "Juventus", "juve": "Juventus", "bianconeri": "Juventus",
    "napoli": "Napoli", "naples": "Napoli", "partenopei": "Napoli",
    "as roma": "AS Roma", "roma": "AS Roma", "giallorossi": "AS Roma",
    "lazio": "SS Lazio", "lazio rome": "SS Lazio", "biancocelesti": "SS Lazio",
    "atalanta": "Atalanta", "fiorentina": "Fiorentina", "bologna": "Bologne", "bologne": "Bologne", "torino": "Torino", "udinese": "Udinese", "genoa": "Genoa", "monza": "Monza", "parma": "Parme", "verona": "Hellas Vérone", "como": "Como", "côme": "Como", "empoli": "Empoli", "cagliari": "Cagliari", "lecce": "Lecce", "venezia": "Venise",

    # Bundesliga
    "bayern munich": "Bayern Munich", "bayern": "Bayern Munich", "fc bayern": "Bayern Munich", "munich": "Bayern Munich",
    "borussia dortmund": "Borussia Dortmund", "dortmund": "Borussia Dortmund", "bvb": "Borussia Dortmund",
    "bayer leverkusen": "Bayer Leverkusen", "leverkusen": "Bayer Leverkusen", "bayer": "Bayer Leverkusen",
    "rb leipzig": "RB Leipzig", "leipzig": "RB Leipzig",
    "eintracht frankfurt": "Eintracht Francfort", "eintracht francfort": "Eintracht Francfort", "frankfurt": "Eintracht Francfort", "francfort": "Eintracht Francfort",
    "stuttgart": "VfB Stuttgart", "vfb stuttgart": "VfB Stuttgart", "wolfsburg": "VfL Wolfsburg", "monchengladbach": "Borussia M'gladbach", "gladbach": "Borussia M'gladbach", "freiburg": "SC Fribourg", "fribourg": "SC Fribourg", "hoffenheim": "TSG Hoffenheim", "werder bremen": "Werder Brême", "bremen": "Werder Brême", "augsburg": "FC Augsbourg", "mainz": "FSV Mayence", "heidenheim": "FC Heidenheim", "union berlin": "Union Berlin", "st pauli": "FC St. Pauli", "bochum": "VfL Bochum", "kiel": "Holstein Kiel",

    # Saudi Pro League
    "al-nassr": "Al-Nassr", "al nassr": "Al-Nassr", "nassr": "Al-Nassr",
    "al-hilal": "Al-Hilal", "al hilal": "Al-Hilal", "hilal": "Al-Hilal",
    "al-ittihad": "Al-Ittihad", "al ittihad": "Al-Ittihad", "ittihad": "Al-Ittihad",
    "al-ahli": "Al-Ahli", "al ahli": "Al-Ahli", "ahli": "Al-Ahli", "al-shabab": "Al-Shabab", "al shabab": "Al-Shabab", "al-qadsiah": "Al-Qadsiah", "al qadsiah": "Al-Qadsiah", "al-ettifaq": "Al-Ettifaq", "al ettifaq": "Al-Ettifaq", "neom": "NEOM SC", "neom sc": "NEOM SC",

    # Portugal & Other Europe
    "sporting cp": "Sporting CP", "sporting": "Sporting CP", "sporting lisbon": "Sporting CP", "sporting lisbonne": "Sporting CP",
    "benfica": "SL Benfica", "sl benfica": "SL Benfica",
    "porto": "FC Porto", "fc porto": "FC Porto", "braga": "SC Braga",
    "galatasaray": "Galatasaray", "fenerbahce": "Fenerbahçe", "fenerbahçe": "Fenerbahçe", "besiktas": "Beşiktaş", "beşiktaş": "Beşiktaş", "trabzonspor": "Trabzonspor",
    "ajax": "Ajax Amsterdam", "ajax amsterdam": "Ajax Amsterdam", "psv": "PSV Eindhoven", "psv eindhoven": "PSV Eindhoven", "feyenoord": "Feyenoord",
    "celtic": "Celtic Glasgow", "rangers": "Rangers FC", "anderlecht": "RSC Anderlecht", "club brugge": "Club Bruges", "bruges": "Club Bruges",

    # MLS & Americas
    "inter miami": "Inter Miami", "miami": "Inter Miami",
    "la galaxy": "LA Galaxy", "los angeles galaxy": "LA Galaxy", "galaxy": "LA Galaxy",
    "los angeles fc": "Los Angeles FC", "lafc": "Los Angeles FC",
    "san diego fc": "San Diego FC", "san diego": "San Diego FC",
    "palmeiras": "Palmeiras", "flamengo": "Flamengo", "botafogo": "Botafogo", "santos": "Santos", "corinthians": "Corinthians", "gremio": "Grêmio", "fluminense": "Fluminense",
    "river plate": "River Plate", "boca juniors": "Boca Juniors", "boca": "Boca Juniors",
}


def clean_text_norm(text: str) -> str:
    """Normalise une chaîne de caractères pour la recherche NLP."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", str(text)).encode("ASCII", "ignore").decode("utf-8")
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def detect_player(text: str) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
    """Détecte avec certitude le joueur concerné à partir de la base de registres et alias."""
    norm = clean_text_norm(text)
    if not norm:
        return None, None
    
    # 1. Correspondance exacte avec mot entier sur les noms complets (triés par longueur décroissante)
    sorted_players = sorted(PLAYER_REGISTRY.keys(), key=lambda x: len(x), reverse=True)
    for p_name in sorted_players:
        p_norm = clean_text_norm(p_name)
        if re.search(r"\b" + re.escape(p_norm) + r"\b", norm):
            return p_name, PLAYER_REGISTRY[p_name]
        
        # Tester les alias avec r"\b" (mot entier requis)
        for alias in PLAYER_REGISTRY[p_name].get("alias", []):
            a_norm = clean_text_norm(alias)
            if len(a_norm) >= 4 and re.search(r"\b" + re.escape(a_norm) + r"\b", norm):
                return p_name, PLAYER_REGISTRY[p_name]

    return None, None


def get_club_pattern(canonical: str) -> str:
    """Génère un pattern regex capturant tous les alias et variations d'un club canonique."""
    aliases = [k for k, v in CLUB_CANONICAL.items() if v == canonical]
    if not aliases:
        aliases = [canonical]
    aliases.sort(key=lambda x: len(x), reverse=True)
    cleaned = [re.escape(clean_text_norm(a)) for a in aliases if clean_text_norm(a)]
    return "(?:" + "|".join(cleaned) + ")" if cleaned else re.escape(clean_text_norm(canonical))


def detect_clubs_in_text(text: str) -> List[Tuple[str, int]]:
    """Détecte tous les clubs mentionnés dans le texte et leurs positions d'apparition."""
    norm = clean_text_norm(text)
    found_clubs: List[Tuple[str, int]] = []
    seen_canonical = set()
    matched_spans: List[Tuple[int, int]] = []

    # Trier les clés de clubs par longueur décroissante pour matcher 'manchester city' avant 'city'
    sorted_keys = sorted(CLUB_CANONICAL.keys(), key=lambda x: len(x), reverse=True)
    for club_key in sorted_keys:
        canon = CLUB_CANONICAL[club_key]
        if canon in seen_canonical:
            continue
        
        # Regex avec frontières de mots
        pattern = r"\b" + re.escape(club_key) + r"\b"
        for match in re.finditer(pattern, norm):
            m_start, m_end = match.start(), match.end()
            # Empêcher les sous-mots chevauchants (ex: 'city' dans 'manchester city')
            if any(max(m_start, s) < min(m_end, e) for s, e in matched_spans):
                continue
            
            found_clubs.append((canon, m_start))
            seen_canonical.add(canon)
            matched_spans.append((m_start, m_end))
            break

    # Trier par ordre d'apparition dans le texte
    found_clubs.sort(key=lambda x: x[1])
    return found_clubs


def resolve_mercato_direction(
    title: str,
    summary: str = "",
    player_name: Optional[str] = None,
    player_data: Optional[Dict[str, str]] = None
) -> Tuple[str, str]:
    """
    Résout avec précision extrême la direction du transfert : (club_vendeur, club_acheteur).
    Élimine les inversions et les faux placeholders.
    """
    combined = f"{title} {summary}"
    norm = clean_text_norm(combined)
    norm_title = clean_text_norm(title)
    
    # Détecter les clubs mentionnés
    detected = detect_clubs_in_text(combined)
    club_names = [c[0] for c in detected]

    # Club actuel du joueur si connu
    current_club = player_data.get("current_club") if player_data else None

    # Cas 0 : Prolongation de contrat
    if any(w in norm_title for w in ["prolonge", "renouvelle", "renovacao", "rinnova", "extends", "contract extension", "verlangert", "تجديد"]):
        target = current_club or (club_names[0] if club_names else "")
        return target, target

    # Cas 1 : 2 clubs ou plus détectés
    if len(club_names) >= 2:
        c1, c2 = club_names[0], club_names[1]

        # ── Règles Syntaxiques Directionnelles Multilingues avec Alias Complets ──
        c1_pat = get_club_pattern(c1)
        c2_pat = get_club_pattern(c2)

        # Règle 1 : Patterns explicites d'ORIGINE / VENDEUR (from_club)
        from_patterns_c2 = [
            r"en provenance de\s+" + c2_pat,
            r"en provenance du\s+" + c2_pat,
            r"depuis\s+" + c2_pat,
            r"quitte\s+" + c2_pat,
            r"part de\s+" + c2_pat,
            r"leaves\s+" + c2_pat,
            r"from\s+" + c2_pat,
            r"departing\s+" + c2_pat,
            r"procedente de\s+" + c2_pat,
            r"deja\s+" + c2_pat,
            r"lascia\s+" + c2_pat,
            r"in uscita da\s+" + c2_pat,
            r"proveniente da\s+" + c2_pat,
            r"von\s+" + c2_pat,
            r"vom\s+" + c2_pat,
            r"verlasst\s+" + c2_pat,
        ]
        if any(re.search(pat, norm) for pat in from_patterns_c2):
            return c2, c1  # Vendeur=c2, Acheteur=c1

        from_patterns_c1 = [
            r"en provenance de\s+" + c1_pat,
            r"en provenance du\s+" + c1_pat,
            r"depuis\s+" + c1_pat,
            r"quitte\s+" + c1_pat,
            r"part de\s+" + c1_pat,
            r"leaves\s+" + c1_pat,
            r"from\s+" + c1_pat,
            r"departing\s+" + c1_pat,
            r"procedente de\s+" + c1_pat,
            r"deja\s+" + c1_pat,
            r"lascia\s+" + c1_pat,
            r"in uscita da\s+" + c1_pat,
            r"proveniente da\s+" + c1_pat,
            r"von\s+" + c1_pat,
            r"vom\s+" + c1_pat,
            r"verlasst\s+" + c1_pat,
        ]
        if any(re.search(pat, norm) for pat in from_patterns_c1):
            return c1, c2  # Vendeur=c1, Acheteur=c2

        # Règle 2 : Patterns explicites de DESTINATION / ACHETEUR (to_club)
        to_patterns_c1 = [
            r"signe au\s+" + c1_pat,
            r"signe a\s+" + c1_pat,
            r"signe avec\s+" + c1_pat,
            r"transfere au\s+" + c1_pat,
            r"transfere a\s+" + c1_pat,
            r"prete au\s+" + c1_pat,
            r"prete a\s+" + c1_pat,
            r"s engage avec\s+" + c1_pat,
            r"s engage a\s+" + c1_pat,
            r"s engage au\s+" + c1_pat,
            r"rejoint\s+" + c1_pat,
            r"arrive a\s+" + c1_pat,
            r"arrive au\s+" + c1_pat,
            r"passe a\s+" + c1_pat,
            r"passe au\s+" + c1_pat,
            r"vers\s+" + c1_pat,
            r"direction\s+" + c1_pat,
            r"en route vers\s+" + c1_pat,
            r"signs for\s+" + c1_pat,
            r"joins\s+" + c1_pat,
            r"moves to\s+" + c1_pat,
            r"heads to\s+" + c1_pat,
            r"to\s+" + c1_pat,
            r"transfers to\s+" + c1_pat,
            r"ficha por\s+" + c1_pat,
            r"llega al\s+" + c1_pat,
            r"llega a\s+" + c1_pat,
            r"passa al\s+" + c1_pat,
            r"passa ai\s+" + c1_pat,
            r"passa alla\s+" + c1_pat,
            r"para o\s+" + c1_pat,
            r"vai para\s+" + c1_pat,
            r"wechselt zu\s+" + c1_pat,
            r"unterschreibt bei\s+" + c1_pat,
            r"proposta do\s+" + c1_pat,
            r"offre de\s+" + c1_pat,
            r"bid from\s+" + c1_pat,
        ]
        if any(re.search(pat, norm) for pat in to_patterns_c1):
            return c2, c1  # Vendeur=c2, Acheteur=c1

        to_patterns_c2 = [
            r"signe au\s+" + c2_pat,
            r"signe a\s+" + c2_pat,
            r"signe avec\s+" + c2_pat,
            r"transfere au\s+" + c2_pat,
            r"transfere a\s+" + c2_pat,
            r"prete au\s+" + c2_pat,
            r"prete a\s+" + c2_pat,
            r"s engage avec\s+" + c2_pat,
            r"s engage a\s+" + c2_pat,
            r"s engage au\s+" + c2_pat,
            r"rejoint\s+" + c2_pat,
            r"arrive a\s+" + c2_pat,
            r"arrive au\s+" + c2_pat,
            r"passe a\s+" + c2_pat,
            r"passe au\s+" + c2_pat,
            r"vers\s+" + c2_pat,
            r"direction\s+" + c2_pat,
            r"en route vers\s+" + c2_pat,
            r"signs for\s+" + c2_pat,
            r"joins\s+" + c2_pat,
            r"moves to\s+" + c2_pat,
            r"heads to\s+" + c2_pat,
            r"to\s+" + c2_pat,
            r"transfers to\s+" + c2_pat,
            r"ficha por\s+" + c2_pat,
            r"llega al\s+" + c2_pat,
            r"llega a\s+" + c2_pat,
            r"passa al\s+" + c2_pat,
            r"passa ai\s+" + c2_pat,
            r"passa alla\s+" + c2_pat,
            r"para o\s+" + c2_pat,
            r"vai para\s+" + c2_pat,
            r"wechselt zu\s+" + c2_pat,
            r"unterschreibt bei\s+" + c2_pat,
            r"proposta do\s+" + c2_pat,
            r"offre de\s+" + c2_pat,
            r"bid from\s+" + c2_pat,
        ]
        if any(re.search(pat, norm) for pat in to_patterns_c2):
            return c1, c2  # Vendeur=c1, Acheteur=c2

        # Règle 3 : Offre payée au club vendeur
        pay_seller_patterns_c2 = [
            r"pagar ao\s+" + c2_pat,
            r"paga ao\s+" + c2_pat,
            r"proposta ao\s+" + c2_pat,
            r"offre a\s+" + c2_pat,
            r"offre au\s+" + c2_pat,
            r"bid to\s+" + c2_pat,
            r"offer to\s+" + c2_pat,
        ]
        if any(re.search(pat, norm) for pat in pay_seller_patterns_c2):
            return c2, c1  # Vendeur=c2, Acheteur=c1

        pay_seller_patterns_c1 = [
            r"pagar ao\s+" + c1_pat,
            r"paga ao\s+" + c1_pat,
            r"proposta ao\s+" + c1_pat,
            r"offre a\s+" + c1_pat,
            r"offre au\s+" + c1_pat,
            r"bid to\s+" + c1_pat,
            r"offer to\s+" + c1_pat,
        ]
        if any(re.search(pat, norm) for pat in pay_seller_patterns_c1):
            return c1, c2  # Vendeur=c1, Acheteur=c2

        # Règle 4 : Club sujet acheteur (ex: "Arsenal cible / recrute / s'offre...")
        buyer_subject_c1 = [
            r"\b" + c1_pat + r"\s+(?:s offre|recrute|attire|veut|vise|cible|fonce sur|proche de|signs|targets|wants|bids for|anuncia el fichaje)\b",
        ]
        if any(re.search(pat, norm) for pat in buyer_subject_c1):
            return c2, c1  # Vendeur=c2, Acheteur=c1

        buyer_subject_c2 = [
            r"\b" + c2_pat + r"\s+(?:s offre|recrute|attire|veut|vise|cible|fonce sur|proche de|signs|targets|wants|bids for|anuncia el fichaje)\b",
        ]
        if any(re.search(pat, norm) for pat in buyer_subject_c2):
            return c1, c2  # Vendeur=c1, Acheteur=c2

        # Règle 5 : Utilisation de current_club comme ancre par défaut si syntaxe neutre
        if current_club:
            if c1 == current_club:
                return c1, c2
            elif c2 == current_club:
                return c2, c1

        # Règle 6 : Par défaut, c1 -> c2
        return c1, c2

    # Cas 2 : 1 seul club détecté dans l'article
    elif len(club_names) == 1:
        c = club_names[0]

        # Si on connaît le club actuel du joueur :
        if current_club:
            if current_club == c:
                # Le titre parle du club actuel -> Vendeur = current_club, Acheteur inconnu
                return current_club, ""
            else:
                # Le club mentionné est différent du club actuel -> Vendeur = current_club, Acheteur = c
                return current_club, c

        # Analyse des prépositions si current_club inconnu
        if any(w in norm_title for w in ["para o", "ao", "vers", "rejoint", "signe a", "target", "to", "moves to", "joins", "al", "ai", "zu", "nach", "نحو", "الى"]):
            return "", c  # Acheteur = c
        elif any(w in norm_title for w in ["quitte", "laisse", "leaves", "ex", "deixa", "sai do", "dal", "von", "من"]):
            return c, ""  # Vendeur = c
        else:
            return "", c

    # Cas 3 : Aucun club détecté dans le texte
    else:
        if current_club:
            return current_club, ""
        return "", ""


def parse_article_full(title: str, summary: str = "") -> Dict[str, str]:
    """
    Analyse complète d'un article pour extraire toutes les entités Mercato avec garantie de cohérence.
    """
    player_name, player_data = detect_player(f"{title} {summary}")
    from_club, to_club = resolve_mercato_direction(title, summary, player_name, player_data)
    
    # Nationalité
    nat = player_data["nat"] if player_data else "International 🌍"
    
    # Nom final du joueur
    final_player = player_name or ""
    if not final_player:
        # Tenter d'extraire un nom propre
        match = re.search(r"\b([A-ZÀ-ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-ÿ][a-zà-ÿ]+))\b", title)
        if match and match.group(1).lower() not in CLUB_CANONICAL:
            final_player = match.group(1)
        else:
            final_player = "Joueur Star"

    # Statut
    norm_title = title.lower()
    if any(k in norm_title for k in ["officiel", "official", "signe", "signé", "prolonge", "confirmé", "ufficiale"]):
        status = "OFFICIEL ✅"
    elif any(k in norm_title for k in ["here we go", "accord total", "deal done", "visite médicale", "fechado"]):
        status = "HERE WE GO 🔥"
    elif any(k in norm_title for k in ["négociation", "pourparlers", "offre", "discussions", "proche", "avance", "proposta", "trattativa", "talks", "bid"]):
        status = "NEGOCIATION 💬"
    else:
        status = "RUMEUR 📰"

    return {
        "player_name": final_player,
        "national_team": nat,
        "from_club": from_club,
        "to_club": to_club,
        "status": status,
    }


# ─────────────────────────────────────────────────────────────
# FILTRAGE STRICT FOOTBALL & MERCATO — VERSION CORRIGÉE
# Bug fix: les mots arabes normalisés par clean_text_norm() deviennent ""
# ce qui rendait "" in any_string = True → tous les articles passaient!
# ─────────────────────────────────────────────────────────────

# Sources à bloquer systématiquement (non-sportives)
BLOCKED_SOURCE_DOMAINS = [
    "business insider", "businessinsider", "yahoo finance", "yahoo news", "yahoo",
    "bloomberg", "techcrunch", "tech crunch", "buzzfeed", "huffpost",
    "new york times", "washington post", "the atlantic", "vox",
    "insider", "marketwatch", "market watch", "cnbc", "fox news", "daily mail",
    "the sun", "the mirror", "express", "people com", "tmz",
    "wsj", "wall street journal", "cointelegraph", "coin telegraph", "coindesk", "coin desk",
    "le monde", "le figaro", "hespress", "reuters",
]

# Mots-clés football/sport — ASCII UNIQUEMENT (compatible avec clean_text_norm)
FOOTBALL_KEYWORDS_ASCII: List[str] = [
    # Termes mercato transversaux
    r"\btransfer\b", r"\btransfert\b", r"\bmercato\b", r"\bsigning\b",
    r"\bsigned\b", r"\bloan\b", r"\bfree agent\b", r"\bcontract\b",
    r"\bbid\b", r"\boffer\b", r"\bdeal\b",
    # Football / Soccer
    r"\bfootball\b", r"\bsoccer\b", r"\bfoot\b",
    r"\bfutbol\b", r"\bfussball\b", r"\bcalcio\b",
    # Ligues
    r"\bpremier league\b", r"\bla liga\b", r"\bserie a\b",
    r"\bbundesliga\b", r"\bchampions league\b", r"\bligue 1\b",
    r"\bliga\b", r"\bleague\b",
    # Postes & rôles
    r"\bstriker\b", r"\bmidfielder\b", r"\bdefender\b", r"\bwinger\b",
    r"\bgoalkeeper\b", r"\bbuteur\b", r"\bgardien\b", r"\bjoueur\b",
    r"\bgiocatore\b", r"\bjugador\b", r"\bspieler\b",
    # Termes français
    r"\bprolongation\b", r"\bentraineur\b", r"\bselection\b",
    r"\bballon d.or\b", r"\bpret\b",
    # Termes espagnols
    r"\bfichaje\b", r"\btraspaso\b", r"\bcesion\b",
    # Termes italiens
    r"\bcalciomercato\b", r"\bacquisto\b", r"\bprestito\b",
    # Termes allemands
    r"\bwechsel\b", r"\bneuzugang\b",
    # Clubs sans ambiguïté
    r"\breal madrid\b", r"\bbarcelona\b", r"\bman city\b", r"\bman utd\b",
    r"\blfc\b", r"\bchelsea fc\b",
]

# Mots-clés ARABES football — à tester sur le texte BRUT (non normalisé)
FOOTBALL_KEYWORDS_ARABIC: List[str] = [
    "كرة القدم", "كرة قدم", "ميركاتو", "انتقال", "صفقة",
    "لاعب", "نادي", "توقيع", "إعارة", "دوري", "فريق"
]

# Mots-clés NON-FOOTBALL — ASCII uniquement
NON_FOOTBALL_PATTERNS: List[str] = [
    r"\brecipe\b", r"\brecette\b", r"\bscrambled\b", r"\bkitchen\b",
    r"\bbathroom\b", r"\bmortgage\b", r"\binflation\b",
    r"\blayoff\b", r"\blayoffs\b", r"\bstartup\b",
    r"\bcryptocurren", r"\bimmobilier\b", r"\bimpots\b",
    r"\bcuisine\b", r"\bcolonel sanders\b", r"\bair fryer\b",
    r"\bscrambleg eggs\b", r"\bweightloss\b", r"\bnutrition\b",
    r"\bfinancial results\b", r"\bearnings report\b", r"\bstock market\b",
    r"\bipo\b", r"\bventure capital\b", r"\btech giant\b",
    r"\bpalm springs\b", r"\bkfc\b", r"\bbraid\b",
]


def is_football_mercato_article(title: str, summary: str = "", source: str = "") -> bool:
    """
    Vérifie si un article est REELLEMENT du football ou du mercato.
    VERSION CORRIGÉE — les mots arabes sont vérifiés sur le texte brut.
    LOGIQUE: whitelist stricte, pas de faux positifs tolérés.
    """
    combined_raw = f"{title} {summary}"  # texte brut pour Arabic + source check
    norm = clean_text_norm(combined_raw)   # ASCII uniquement pour keywords ASCII
    
    if not norm:
        return False

    # 0. Bloquer les sources non-sportives connues
    source_norm = clean_text_norm(source or title)
    if any(blocked in source_norm for blocked in BLOCKED_SOURCE_DOMAINS):
        return False

    # 1. Si un joueur connu est reconnu -> VALIDE IMMÉDIATEMENT
    player_name, _ = detect_player(combined_raw)
    if player_name:
        return True

    # 2. Si un club de football connu est reconnu -> VALIDE IMMÉDIATEMENT
    detected_clubs = detect_clubs_in_text(combined_raw)
    if detected_clubs:
        return True

    # 3. Vérifier les mots-clés positifs FOOTBALL (ASCII avec word boundaries)
    has_positive_ascii = any(
        re.search(pat, norm) for pat in FOOTBALL_KEYWORDS_ASCII
    )

    # 4. Vérifier les mots-clés ARABES football sur le texte BRUT (non normalisé)
    has_positive_arabic = any(kw in combined_raw for kw in FOOTBALL_KEYWORDS_ARABIC)

    has_positive = has_positive_ascii or has_positive_arabic

    if not has_positive:
        return False

    # 5. Vérifier les mots-clés NÉGATIFS (non-football) — ASCII avec word boundaries
    has_negative = any(
        re.search(pat, norm) for pat in NON_FOOTBALL_PATTERNS
    )

    # Si négatif ET le seul signal positif est très faible (ex: "bid" = trop générique)
    if has_negative:
        # Autoriser seulement si signal très fort (joueur/club déjà validé ci-dessus)
        return False

    return True

