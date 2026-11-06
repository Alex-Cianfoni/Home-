OPERATION RUSTBUCKET v3.0 — FLEET COMMAND & WORKING SONAR
=========================================================

A playable, fictional, turn-based naval game inspired by the USS Razorback
Port Meridian story. Python 3.9+; NO PYGAME, NO PIP INSTALLS needed.

WHAT'S NEW
----------
* FLEET SELECTION MENU at launch; searchable and filterable roster of 131
  playable historic submarine classes, variants and named preserved boats.
* Choose USS Razorback, Gato/Balao/Tench, GUPPY I/II/IA/IIA/IB/III, Type
  II/VII/IX/XXI/XXIII, British T/S/U/Oberon, Soviet, Japanese, Italian,
  French, Dutch, Australian and other entries.
* Each boat affects playable limits: max submerged speed, game dive limit,
  battery, torpedo supply, fictional noise signature and sensor strength.
* WORKING SONAR: ships have persistent positions, course and speed.
  Contacts move each turn. Passive sensors report estimated bearing/range,
  confidence and last known contact information (including stale tracks).
* PASSIVE LISTEN analyses tracks while time passes. ACTIVE PING boosts track
  confidence at the cost of stealth and possible detection.
* Click plotted sonar contacts for information. Open full SONAR CONSOLE for
  the large screen and a detailed track listing.
* Simulated torpedo use now requires an identifiable nearby Blue Force track.
* SAVE/LOAD keeps sonar contact positions and tracking confidence. Loads
  older v1/v2 saves as Razorback campaigns when possible.
* Open GAME menu to change submarines, begin a new mission, load/save or quit.

INSTALL / START
---------------
1. Extract this ZIP to a folder, do not run files from inside the archive.
2. Install Python 3.9 or newer if you do not already have it.
   On Windows, download Python from https://www.python.org/downloads/
3. Double-click PLAY_RUSTBUCKET.bat.
4. Select a submarine in the fleet selection window. Click COMMAND THIS SUBMARINE.
5. Choose A/B/C or enter your own orders in the command field.

COMMAND PROMPT / POWERSHELL
---------------------------
  py -3 operation_rustbucket.py
  py -3 operation_rustbucket.py --console
  py -3 operation_rustbucket.py --list-subs
  py -3 operation_rustbucket.py --submarine "Type XXI" --console
  py -3 operation_rustbucket.py --seed 1944 --difficulty easy

In console mode, type MENU to choose a different submarine.

SONAR COMMANDS
--------------
  sonar                  Shows latest known tracks without advancing time
  listen                 Spend time refining passive sonar tracks
  analyze sonar contacts Same as listen
  ping                   Send an active sonar pulse; higher risk of detection
  active sonar           Same as ping
  fire torpedo           Simulated launch if a classified enemy contact is valid

Sonar CONTACT IDs (e.g., BRV, B17 and S01) correspond to persistent simulated
vessels. The dots and ranges are now tied to those objects, not fixed artwork.
They update when a simulated turn takes place, not continuously in real time.
Contacts may disappear, reappear or be misclassified as information improves.
Underwater sound propagation and all ranges are simplified game rules.

OTHER ORDERS
------------
  silent                 Continue quietly at two knots
  speed 4                Set four knots if your submarine permits
  depth 130              Request a dive to 130 ft if authorized
  thermal                Enter the fictional temperature gradient
  bottom                 Rest on the approved sandy seabed when cleared
  depart                 Leave bottom after safety checks
  report 30              Report seabed clearance every 30 simulated minutes
  depth report           Current depth / thermal layer readout
  continue present course  Maintain ordered speed/heading without resetting
  transmit 1944          Send the vintage identification marker at objective
  save / load            Console save commands
  help                   Complete command list

Your own multi-part orders also work, e.g.:
  'Enter the thermal layer, maintain two knots, and report depth every 30 minutes.'

OPTIONAL AI FOR FREEFORM COMMANDS
----------------------------------
Offline mode uses a built-in natural-language pattern interpreter. It does not
understand every arbitrary sentence as well as this ChatGPT conversation.
For more flexible narration and command interpretation, click AI MODE and
enter an OPENAI_API_KEY. An OpenAI API account with separate pay-as-you-go
billing is required, even if you have ChatGPT Plus. This sends your orders and
recent game context to the API. The API key is held in memory only and is not
stored in save files. No AI service is required for ordinary offline play.

TESTS
-----
  python -m unittest -v test_rustbucket.py test_v3_features.py
  python operation_rustbucket.py --demo

NOTE / SCOPE
------------
This includes a broad playable selection of 131 entries, not literally every
submarine design ever built. The default mission remains the familiar Port
Meridian infiltration, available to every selected submarine. Historic boats
are fictionally modernized; all game speed/depth/sonar values are BALANCING
VALUES, not verified historical specifications or operational guidance.

Enjoy the mission. The Chief Engineer still wants coffee.
