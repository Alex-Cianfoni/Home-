"""Playable alternate-history submarine roster. Specifications are GAME BALANCE,
not historical engineering limits. Named museum boats and broad historic classes.
"""
from __future__ import annotations
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Submarine:
    id: str
    name: str
    country: str
    era: str
    year: int
    speed: float             # game submerged maximum in knots
    depth: int               # game-approved maximum feet
    battery: int             # initial battery percent
    signature: int           # relative fictional acoustic signature (higher = louder)
    sonar: int               # sensor gameplay rating (1-10)
    torpedoes: int
    description: str


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


# country | name | era | year | game speed | game dive limit | battery start |
# fictional sound index | fictional sensor rating | exercise torpedoes | description
# A broad playable selection of classes/variants, not literally every submarine
# design ever built. Fictional modernization is assumed for historic boats.
_DATA = r"""
United States|USS Razorback (SS-394) — GUPPY IIA|Museum fleet|1944|8|245|94|5|7|10|Default hero vessel; Balao hull with postwar GUPPY IIA modernization
United States|USS Becuna (SS-319) — GUPPY IA|Museum fleet|1944|8|240|92|5|7|10|Restored Balao-class sister submarine
United States|USS Blueback (SS-581) — Barbel|Museum fleet|1959|10|310|96|3|8|12|Streamlined postwar diesel-electric submarine
United States|USS Nautilus (SSN-571) — Nuclear|Museum fleet|1954|12|400|100|4|9|14|Historic first nuclear-powered submarine; fictional compact endurance rating
Australia|HMAS Onslow (SS 60) — Oberon|Museum fleet|1968|11|330|97|3|9|12|Quiet Royal Australian Navy Oberon-class submarine
Germany|U-2540 — Type XXI|Museum fleet|1945|11|280|91|4|8|12|Late-war German electroboat; subsequently Wilhelm Bauer
France|Le Redoutable (S611) — SSBN|Museum fleet|1967|12|420|100|5|8|14|French Cold War submarine; no nuclear weapons in the game
United States|USS Pampanito (SS-383) — Balao|Museum fleet|1943|8|245|94|5|7|10|San Francisco museum submarine
United States|USS Bowfin (SS-287) — Balao|Museum fleet|1942|8|245|94|5|7|10|Pearl Harbor museum submarine
United States|USS Silversides (SS-236) — Gato|Museum fleet|1941|8|220|92|6|6|10|Muskegon museum submarine
United States|USS Drum (SS-228) — Gato|Museum fleet|1941|8|220|92|6|6|10|Mobile museum submarine
United States|USS Cobia (SS-245) — Gato|Museum fleet|1943|8|220|92|6|6|10|Wisconsin museum submarine
United States|USS Batfish (SS-310) — Balao|Museum fleet|1943|8|245|94|5|7|10|Restored fleet submarine
United States|USS Croaker (SS-246) — Gato|Museum fleet|1944|8|220|92|6|6|10|Buffalo museum submarine
United States|USS Cod (SS-224) — Gato|Museum fleet|1943|8|220|92|6|6|10|Cleveland museum submarine
United States|USS Torsk (SS-423) — Tench|Museum fleet|1944|9|270|95|5|7|10|Baltimore museum submarine
United States|USS Requin (SS-481) — Tench|Museum fleet|1945|9|270|95|5|7|10|Pittsburgh museum submarine
United States|USS Cavalla (SS-244) — Gato|Museum fleet|1944|8|220|92|6|6|10|Galveston museum submarine
United States|USS Growler (SSG-577) — Grayback|Museum fleet|1958|10|290|94|5|8|8|Regulus guided-missile submarine; conventional training weapons only
United States|USS Albacore (AGSS-569) — Experimental|Museum fleet|1953|13|350|94|3|9|0|Experimental streamlined hull; no torpedoes
Germany|U-505 — Type IXC|Museum fleet|1941|7|235|90|6|6|10|Chicago museum U-boat
Germany|U-995 — Type VIIC/41|Museum fleet|1943|7|230|89|6|6|10|Laboe museum U-boat
Germany|U-534 — Type IXC/40|Museum fleet|1942|7|240|90|6|6|10|Preserved German U-boat
Finland|Vesikko — Type IIA derivative|Museum fleet|1933|7|200|87|6|5|5|Preserved Finnish coastal submarine
Netherlands|HNLMS Dolfijn (S808) — Dolfijn|Museum fleet|1960|10|320|96|4|8|10|Postwar Dutch three-cylinder submarine
Sweden|HMS Neptun — Näcken|Museum fleet|1980|12|390|97|2|9|12|Swedish Cold War submarine; fictional modernization
United Kingdom|HMS Alliance (P417) — Amphion|Museum fleet|1945|10|300|96|4|8|12|Royal Navy A-class museum submarine
United Kingdom|HMS Ocelot (S17) — Oberon|Museum fleet|1962|11|330|97|3|9|12|Chatham museum submarine
United Kingdom|HMS Otus (S18) — Oberon|Museum fleet|1963|11|330|97|3|9|12|Royal Navy Oberon boat
United Kingdom|HMS Courageous (S50) — Valiant|Museum fleet|1970|12|430|100|4|9|14|British nuclear attack submarine; fictional endurance
United States|AA-1 / T-class|US classes|1916|6|170|83|8|4|4|Early American fleet submarine concept
United States|V-1 / Barracuda class|US classes|1924|7|190|85|8|4|6|Interwar V-boat design
United States|V-4 / Argonaut|US classes|1927|7|190|86|8|5|8|Interwar minelaying submarine
United States|V-5 / Narwhal class|US classes|1929|7|210|87|8|5|8|Large American cruiser submarine
United States|Dolphin class|US classes|1932|7|200|88|7|5|8|Interwar fleet submarine
United States|Cachalot class|US classes|1933|7|210|89|7|5|8|American interwar submarine
United States|Porpoise class|US classes|1935|7|220|90|7|6|10|Early American diesel-electric fleet submarine
United States|Salmon class|US classes|1937|7|225|90|7|6|10|Large long-range American fleet submarine
United States|Sargo class|US classes|1938|8|230|91|7|6|10|Prewar American fleet submarine
United States|Tambor class|US classes|1939|8|240|92|6|6|10|US submarine with improved torpedo arrangement
United States|Gar class|US classes|1940|8|245|92|6|6|10|American fleet submarine related to Tambor
United States|Gato class|US classes|1940|8|245|93|6|7|10|Large American WWII fleet submarine
United States|Balao class|US classes|1942|8|265|94|5|7|10|Deep-diving American fleet submarine
United States|Tench class|US classes|1944|9|290|95|5|7|10|Late-war American fleet submarine
United States|GUPPY I|GUPPY conversions|1947|9|270|96|4|7|10|Early postwar GUPPY conversion
United States|GUPPY II|GUPPY conversions|1948|10|280|96|4|8|10|GUPPY with improved underwater performance
United States|GUPPY IA|GUPPY conversions|1951|9|270|96|4|7|10|Cost-reduced GUPPY conversion
United States|GUPPY IIA|GUPPY conversions|1952|9|280|97|4|8|10|Revised machinery arrangement
United States|GUPPY IB|GUPPY conversions|1953|9|275|96|4|8|10|Export conversion variant
United States|GUPPY III|GUPPY conversions|1959|10|310|97|3|8|12|Lengthened GUPPY conversion
United States|Fleet Snorkel conversion|GUPPY conversions|1945|8|250|94|5|7|10|Postwar snorkel modernization
United States|Tang class (1951)|US Cold War|1951|11|310|97|3|8|12|Postwar purpose-built diesel-electric boat
United States|Barbel class (1958)|US Cold War|1958|12|350|98|3|9|12|Last US conventional attack submarine design
United States|Skate class SSN|US Cold War|1957|12|380|100|4|9|12|Early nuclear-powered attack submarine
United States|Skipjack class SSN|US Cold War|1958|13|430|100|4|9|14|Streamlined nuclear attack submarine
United States|Sturgeon class SSN|US Cold War|1966|13|500|100|3|10|14|Quiet Cold War nuclear attack boat
Germany|Type II A/B/C/D|German WWII|1935|7|180|86|7|5|5|Small coastal WWII U-boat
Germany|Type VII A|German WWII|1936|7|220|89|6|6|10|Early ocean-going U-boat
Germany|Type VII B|German WWII|1938|7|225|90|6|6|10|Improved ocean-going U-boat
Germany|Type VII C|German WWII|1940|8|240|91|6|7|10|Common German WWII U-boat
Germany|Type VII C/41|German WWII|1943|8|250|91|6|7|10|Strengthened Type VII variant
Germany|Type VII D|German WWII|1941|7|240|90|7|6|8|Minelaying Type VII variant
Germany|Type VII F|German WWII|1943|7|245|91|7|6|8|Torpedo transport Type VII variant
Germany|Type IX A/B|German WWII|1938|8|240|91|7|6|12|Long-range ocean submarine
Germany|Type IX C|German WWII|1939|8|250|92|7|6|12|Long-range U-boat
Germany|Type IX C/40|German WWII|1942|8|260|92|6|7|12|Extended-range Type IX variant
Germany|Type IX D2|German WWII|1942|8|265|92|7|6|12|Very long-range ocean-going U-boat
Germany|Type X B|German WWII|1941|7|265|90|8|6|4|Large minelaying U-boat
Germany|Type XIV|German WWII|1941|7|225|90|8|5|0|Supply U-boat; no torpedoes
Germany|Type XXI|German WWII|1944|12|300|97|3|9|12|High submerged performance electroboat
Germany|Type XXIII|German WWII|1944|9|255|95|4|8|2|Small coastal electroboat
Germany|Type 201 / 205|German Cold War|1961|11|350|97|3|9|8|Postwar coastal submarine class
Germany|Type 206A|German Cold War|1973|12|400|98|2|9|8|Quiet small conventionally powered boat
Germany|Type 209|German Cold War|1967|12|410|98|3|9|12|Export diesel-electric submarine family
Germany|Type 212A|Modern competitors|2002|13|500|100|2|10|12|Advanced air-independent propulsion submarine
Germany|Type 214|Modern competitors|2004|13|510|100|2|10|12|Modern export air-independent propulsion boat
United Kingdom|T class (Triton)|British WWII|1937|8|245|92|6|7|10|Royal Navy ocean-going WWII boat
United Kingdom|S class (1931)|British WWII|1931|8|235|91|6|7|10|Medium Royal Navy submarine
United Kingdom|U class (Undine)|British WWII|1938|7|220|91|6|6|8|Small Royal Navy submarine
United Kingdom|V class (1942)|British WWII|1942|8|230|92|6|6|8|Coastal Royal Navy submarine
United Kingdom|O/P/R class|British WWII|1926|7|235|88|7|6|10|Interwar British overseas submarine families
United Kingdom|River class (Thames)|British WWII|1932|8|240|89|7|6|10|Long-range British ocean-going submarine
United Kingdom|Amphion / A class|British WWII|1944|10|300|96|4|8|12|Late-war British submarine
United Kingdom|Oberon class|British Cold War|1960|12|350|98|3|9|12|Quiet British diesel-electric class
United Kingdom|Porpoise class (1956)|British Cold War|1956|11|330|97|4|8|12|Postwar Royal Navy submarine
United Kingdom|Valiant class SSN|British Cold War|1963|13|450|100|4|9|14|Nuclear attack submarine class
Japan|Kaichu I-VI|Japanese WWII|1919|7|230|87|7|5|8|Japanese ocean submarine family
Japan|Kaidai I-VII|Japanese WWII|1924|8|260|90|7|6|12|Japanese large fleet submarines
Japan|Type A1 / A2 cruiser|Japanese WWII|1939|8|270|92|7|7|12|Large cruiser submarine
Japan|Type B1|Japanese WWII|1938|8|275|92|7|7|12|Japanese scouting submarine with aviation capability
Japan|Type B2/B3|Japanese WWII|1942|8|275|92|7|7|12|Improved large scout submarine
Japan|Type C1 / C2|Japanese WWII|1938|8|275|92|7|7|14|Long-range Japanese submarines
Japan|I-201 class (Sen-Taka)|Japanese WWII|1945|12|310|97|3|8|8|High-speed Japanese late-war submarine
Japan|I-400 class (Sen-Toku)|Japanese WWII|1944|9|320|95|8|8|10|Giant submarine aircraft carrier; aircraft gameplay abstracted
Japan|Ko-hyoteki midget|Japanese WWII|1934|5|140|79|8|4|2|Japanese two-man midget submarine
Japan|Kairyu midget|Japanese WWII|1944|5|140|77|8|4|2|Japanese late-war midget submarine
Japan|Ro-100 class|Japanese WWII|1942|7|220|88|7|6|8|Japanese small patrol submarine
Japan|Sen-Ho / I-351|Japanese WWII|1943|8|285|90|8|6|4|Japanese submarine tanker design
Soviet Union|Shchuka class (Shch)|Soviet WWII|1932|7|230|90|7|6|8|Soviet medium submarine family
Soviet Union|Malyutka class (M)|Soviet WWII|1932|6|185|85|8|5|4|Small coastal Soviet submarine
Soviet Union|S class (Stalinets)|Soviet WWII|1936|8|245|91|6|7|10|Soviet ocean-going submarine
Soviet Union|K class (Katyusha)|Soviet WWII|1938|8|275|92|7|7|12|Large Soviet cruiser submarine
Soviet Union|L class (Leninets)|Soviet WWII|1931|7|250|89|7|6|10|Soviet minelaying submarine
Soviet Union|D class (Dekabrist)|Soviet WWII|1928|7|230|88|8|6|8|Early Soviet ocean submarine
Soviet Union|Project 613 (Whiskey)|Soviet Cold War|1950|10|310|96|4|8|12|Postwar Soviet diesel-electric boat
Soviet Union|Project 641 (Foxtrot)|Soviet Cold War|1957|11|350|97|4|8|12|Long-range Soviet diesel-electric boat
Soviet Union|Project 641B (Tango)|Soviet Cold War|1973|12|390|98|3|9|12|Modernized Soviet diesel-electric boat
Soviet Union|Project 877 (Kilo)|Modern competitors|1980|12|460|100|2|10|12|Quiet Soviet conventional submarine
Italy|Marcello class|Italian WWII|1938|8|265|91|7|6|10|Italian ocean-going submarine
Italy|Marconi class|Italian WWII|1939|8|275|92|7|7|10|Large Italian ocean submarine
Italy|Calvi class|Italian WWII|1935|8|270|90|8|6|10|Large Italian cruiser submarine
Italy|Brin class|Italian WWII|1938|8|265|91|7|6|10|Italian long-range submarine
Italy|Perla class|Italian WWII|1936|7|220|89|7|6|8|Italian coastal submarine
Italy|Sirena class|Italian WWII|1933|7|225|89|7|6|8|Italian coastal submarine
Italy|Adua class|Italian WWII|1936|7|225|89|7|6|8|Italian coastal submarine
Italy|Acciaio class|Italian WWII|1941|8|240|91|6|7|8|Italian late-war coastal submarine
Italy|Flutto class|Italian WWII|1942|8|250|92|6|7|8|Italian later-war submarine
France|Redoutable class (1928)|French WWII|1928|8|245|90|7|6|10|Large French ocean submarine
France|Aurore class|French WWII|1939|8|245|91|6|7|10|French medium submarine
France|Minerve class (1934)|French WWII|1934|8|235|89|7|6|8|French coastal submarine
France|Saphir class|French WWII|1928|7|230|87|7|6|8|French minelaying submarine
France|Surcouf (NN3)|French WWII|1929|8|290|91|9|7|10|Unique French cruiser submarine with heavy guns
France|Narval class (1954)|French Cold War|1954|10|320|96|4|8|12|French postwar diesel-electric submarine
France|Daphné class|French Cold War|1958|11|350|97|3|9|12|French export submarine class
Netherlands|O-19 class|Dutch WWII|1938|8|250|91|7|7|10|Dutch ocean minelaying submarine
Netherlands|O-21 class|Dutch WWII|1940|8|255|92|6|7|10|Dutch ocean-going submarine
Netherlands|Dolfijn class|Dutch Cold War|1959|11|330|97|4|8|10|Dutch three-hull submarine
Netherlands|Walrus class|Modern competitors|1985|12|420|99|3|9|12|Dutch modern attack submarine
Australia|Collins class|Modern competitors|1990|12|440|100|3|9|12|Australian modern diesel-electric submarine
Sweden|Näcken class|Swedish Cold War|1978|12|420|98|2|9|10|Swedish modern quiet submarine
Sweden|Gotland class|Modern competitors|1995|13|470|100|2|10|12|Swedish air-independent propulsion boat
"""


def _read() -> dict[str, Submarine]:
    out: dict[str, Submarine] = {}
    for raw in _DATA.strip().splitlines():
        parts = [x.strip() for x in raw.split("|")]
        if len(parts) != 11:
            raise ValueError("Invalid roster row: " + raw)
        country, name, era, year, speed, depth, battery, signature, sonar, torpedoes, description = parts
        key = "razorback" if name.startswith("USS Razorback") else slug(f"{country} {name}")
        if key in out:
            raise ValueError(f"Duplicate submarine ID {key}")
        out[key] = Submarine(key, name, country, era, int(year), float(speed), int(depth), int(battery), int(signature), int(sonar), int(torpedoes), description)
    return out


SUBMARINES = _read()
DEFAULT_SUBMARINE = "razorback"


def select_submarine(value: str) -> Submarine:
    if value in SUBMARINES:
        return SUBMARINES[value]
    name = value.casefold().strip()
    exact = [item for item in SUBMARINES.values() if item.name.casefold() == name]
    if exact:
        return exact[0]
    partial = [item for item in SUBMARINES.values() if name in item.name.casefold()]
    if len(partial) == 1:
        return partial[0]
    raise ValueError(f"Unknown/ambiguous submarine: {value}. Choose a class in the fleet menu.")


def groups() -> dict[str, list[Submarine]]:
    result: dict[str, list[Submarine]] = {}
    for sub in SUBMARINES.values():
        result.setdefault(sub.era, []).append(sub)
    return result
