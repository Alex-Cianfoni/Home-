"""Operation Rustbucket: a small, turn-based Pygame submarine exercise.

Install: python -m pip install pygame
Run:     python operation_rustbucket_fixed.py
"""
import json
import math
import random
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path

import pygame

SCREEN_WIDTH, SCREEN_HEIGHT, FPS = 1200, 800, 60
WHITE, GREEN, RED = (245, 245, 245), (75, 225, 120), (240, 95, 95)
YELLOW, GRAY = (255, 222, 85), (155, 165, 175)
DARK_BLUE, LIGHT_BLUE = (12, 33, 62), (130, 190, 230)
SAVE_PATH = Path(__file__).with_name('rustbucket_world.json')


class GameState(Enum):
    MENU = auto()
    MISSION = auto()
    ENDGAME = auto()


class ShipType(Enum):
    SUBMARINE = auto()
    DESTROYER = auto()
    CRUISER = auto()
    CARRIER = auto()
    BATTLESHIP = auto()
    PATROL_BOAT = auto()


class ContactType(Enum):
    UNKNOWN = auto()
    SUBMARINE = auto()
    SHIP = auto()
    AIRCRAFT = auto()
    DRONE = auto()
    MERCHANT = auto()
    ENVIRONMENTAL = auto()


class DetectionState(Enum):
    UNDETECTED = auto()
    SUSPECTED = auto()
    LOCATED = auto()
    TRACKED = auto()


class SystemStatus(Enum):
    NOMINAL = auto()
    DEGRADED = auto()
    FAILED = auto()


class MissionObjective(Enum):
    HARBOUR_INFILTRATION = auto()
    SUBMARINE_HUNT = auto()
    CARRIER_HUNT = auto()
    CONVOY_ESCORT = auto()
    RECONNAISSANCE = auto()
    FLEET_BATTLE = auto()
    EMERGENCY_RECOVERY = auto()


class GameMode(Enum):
    MOVIE = 'Movie'
    EASY = 'Easy'
    MEDIUM = 'Medium'
    HARD = 'Hard'
    VETERAN = 'Veteran'
    REALISTIC = 'Realistic'


@dataclass
class ModeConfig:
    ai_aggression: float
    ai_speed_penalty: int
    detection_chance: float
    detection_confidence: float
    encounter_chance: float
    hull_damage_multiplier: float
    stealth_loss_per_contact: int


MODE_CONFIGS = {
    GameMode.MOVIE: ModeConfig(.05, 0, .15, .20, .02, .3, 2),
    GameMode.EASY: ModeConfig(.10, 0, .20, .30, .05, .5, 4),
    GameMode.MEDIUM: ModeConfig(.30, 30, .30, .60, .12, 1, 6),
    GameMode.HARD: ModeConfig(.55, 40, .40, .65, .18, 1.5, 8),
    GameMode.VETERAN: ModeConfig(.75, 45, .45, .70, .25, 2, 10),
    GameMode.REALISTIC: ModeConfig(.90, 60, .55, .78, .30, 2.5, 12),
}


@dataclass
class CrewMember:
    name: str
    role: str
    personality: str
    expertise: int
    morale: int = 100
    fatigue: int = 0
    status: str = 'Active'


@dataclass
class Ship:
    name: str
    ship_type: ShipType
    hull_integrity: int = 100
    battery_charge: int = 100
    propulsion_status: SystemStatus = SystemStatus.NOMINAL
    depth: int = 0
    seabed_clearance: int = 50
    sonar_status: SystemStatus = SystemStatus.NOMINAL
    weapons: list[str] = field(default_factory=list)
    navigation_status: SystemStatus = SystemStatus.NOMINAL
    communication_status: SystemStatus = SystemStatus.NOMINAL
    stealth_level: int = 100
    crew: list[CrewMember] = field(default_factory=list)
    mission_clock: int = 0
    position: tuple[float, float] = (0, 0)
    speed: int = 0
    heading: float = 90.0


@dataclass
class Contact:
    name: str
    contact_type: ContactType
    detection_state: DetectionState
    distance: int
    bearing: float
    speed: int
    depth: int
    stealth_level: int = 50
    classified: bool = False


@dataclass
class Mission:
    objective: MissionObjective
    description: str
    duration: int
    success_conditions: list[str]
    failure_conditions: list[str]
    score: int = 0
    completed: bool = False
    failed: bool = False


class NavalWorld:
    THEATERS = [
        {'name': 'Pacific Exercises', 'lat': 30, 'lon': -120,
         'terrain': 'Island Complex', 'base_fuel': 150},
        {'name': 'Atlantic Corridor', 'lat': 40, 'lon': 5,
         'terrain': 'Deep Trench', 'base_fuel': 200},
        {'name': 'Mediterranean Base', 'lat': 35, 'lon': -10,
         'terrain': 'Coastal Shore', 'base_fuel': 120},
    ]

    @staticmethod
    def get_theater_at(lat, lon):
        return min(NavalWorld.THEATERS,
                   key=lambda t: math.hypot(lat - t['lat'], lon - t['lon']))


# Enum values are serialized by NAME, including nested dataclasses.
def encode(value):
    if isinstance(value, Enum):
        return value.name
    if isinstance(value, (Ship, Contact, Mission, CrewMember)):
        return {k: encode(v) for k, v in asdict(value).items()} if isinstance(value, CrewMember) else {
            key: encode(getattr(value, key)) for key in value.__dataclass_fields__
        }
    if isinstance(value, (tuple, list)):
        return [encode(item) for item in value]
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    return value


def restore_ship(data):
    data = dict(data)
    data['ship_type'] = ShipType[data['ship_type']]
    for key in ('propulsion_status', 'sonar_status', 'navigation_status',
                'communication_status'):
        data[key] = SystemStatus[data[key]]
    data['crew'] = [CrewMember(**member) for member in data.get('crew', [])]
    data['position'] = tuple(data['position'])
    return Ship(**data)


def restore_contact(data):
    data = dict(data)
    data['contact_type'] = ContactType[data['contact_type']]
    data['detection_state'] = DetectionState[data['detection_state']]
    return Contact(**data)


def restore_mission(data):
    data = dict(data)
    data['objective'] = MissionObjective[data['objective']]
    return Mission(**data)


class OperationRustbucket:
    def __init__(self, difficulty=GameMode.MEDIUM):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Operation Rustbucket')
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont(None, 48)
        self.font_medium = pygame.font.SysFont(None, 32)
        self.font_small = pygame.font.SysFont(None, 23)
        self.mode = difficulty
        self.config = MODE_CONFIGS[self.mode]
        self.state = GameState.MENU
        self.command_input = ''
        self.message_log = []
        self.initialize_game()
        self.load_persistent_state()

    def initialize_game(self):
        self.turn = 0
        self.score = 0
        self.turn_start = 0
        self.ship_maintenance = 15
        self.ship_maintenance_points = 0
        self.ship_fuel_consumption_per_km = 2.0
        self.player_fuel = 150.0
        self.supplies = [{'name': 'Pacific Exercises', 'amount': 200}]
        self.marker_transmitted = False
        self.was_detected = False
        self.command_input = ''
        self.message_log = ['Exercise ready. Type HELP for commands.']
        self.player_ship = Ship(
            name='USS Razorback', ship_type=ShipType.SUBMARINE,
            battery_charge=94, depth=50, stealth_level=90,
            weapons=['Torpedo MK 14'] * 8, position=(30, -120),
            crew=[
                CrewMember('Captain', 'Commander', 'Determined', 85),
                CrewMember('Executive Officer', 'Navigator', 'Professional', 75, 90),
                CrewMember('Sonar Chief', 'Sonar Technician', 'Observant', 80, 85),
                CrewMember('Chief Engineer', 'Engineer', 'Sarcastic', 90, 75),
                CrewMember('Helmsman', 'Navigator', 'Disciplined', 85, 95),
                CrewMember('Radio Operator', 'Communications', 'Alert', 70, 80),
            ],
        )
        self.mission = Mission(
            objective=MissionObjective.HARBOUR_INFILTRATION,
            description='Transmit exercise marker and withdraw safely',
            duration=15,
            success_conditions=['Mission marker transmitted', 'Safe withdrawal'],
            failure_conditions=['Hull integrity below 30%', 'Fuel or battery depleted'],
        )
        self.contacts = [
            Contact('USS Fletcher', ContactType.SHIP,
                    DetectionState.UNDETECTED, 300, 180.0, 20, 0),
            Contact('German Submarine', ContactType.SUBMARINE,
                    DetectionState.UNDETECTED, 500, 90.0, 15, 50),
            Contact('Patrol Drone', ContactType.DRONE,
                    DetectionState.UNDETECTED, 200, 270.0, 10, 0),
        ]
        self.update_suggested_actions()

    def log(self, message):
        self.message_log.append(str(message))
        self.message_log = self.message_log[-100:]

    def save_world(self):
        data = {
            'version': 2, 'mode': self.mode.name, 'turn': self.turn,
            'score': self.score, 'state': self.state.name,
            'ship_maintenance_points': self.ship_maintenance_points,
            'fuel': self.player_fuel, 'supplies': self.supplies,
            'marker_transmitted': self.marker_transmitted,
            'was_detected': self.was_detected,
            'contacts': encode(self.contacts), 'mission': encode(self.mission),
            'player_ship': encode(self.player_ship),
            'message_log': self.message_log[-25:],
        }
        try:
            SAVE_PATH.write_text(json.dumps(data, indent=2), encoding='utf-8')
            self.log(f'Saved to {SAVE_PATH.name}')
        except OSError as exc:
            self.log(f'Save failed: {exc}')

    def load_persistent_state(self):
        if not SAVE_PATH.exists():
            return
        try:
            data = json.loads(SAVE_PATH.read_text(encoding='utf-8'))
            if data.get('version') != 2:
                self.log('Older save format found; started a fresh exercise.')
                return
            mode = GameMode[data['mode']]
            ship = restore_ship(data['player_ship'])
            contacts = [restore_contact(c) for c in data['contacts']]
            mission = restore_mission(data['mission'])
            self.mode, self.config = mode, MODE_CONFIGS[mode]
            self.player_ship, self.contacts, self.mission = ship, contacts, mission
            self.turn = int(data['turn'])
            self.score = int(data.get('score', 0))
            self.player_fuel = float(data['fuel'])
            self.ship_maintenance_points = int(data.get('ship_maintenance_points', 0))
            self.supplies = data.get('supplies', [])
            self.marker_transmitted = bool(data.get('marker_transmitted', False))
            self.was_detected = bool(data.get('was_detected', False))
            self.message_log = list(data.get('message_log', []))[-100:]
            self.state = GameState[data.get('state', 'MENU')]
            self.update_suggested_actions()
            self.log('Saved exercise loaded.')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.initialize_game()
            self.log(f'Could not load save: {exc}')

    def update_crew_fatigue(self):
        for member in self.player_ship.crew:
            member.fatigue = min(100, member.fatigue + random.randint(2, 6))
            if member.fatigue > 75:
                member.morale = max(0, member.morale - 1)

    def apply_maintenance(self):
        if self.ship_maintenance_points >= 30 and self.player_ship.hull_integrity < 100:
            self.player_ship.hull_integrity = min(100, self.player_ship.hull_integrity + 10)
            self.ship_maintenance_points -= 30
            self.log('Damage-control team repaired 10 hull points.')

    def consume_fuel(self, km):
        self.player_fuel = max(0.0, self.player_fuel - km * self.ship_fuel_consumption_per_km)

    def refill_from_depot(self, depot_name):
        for depot in self.supplies:
            if depot['name'].lower() == depot_name.lower() and depot['amount'] > 0:
                amount = min(50.0, 200 - self.player_fuel, depot['amount'])
                if amount <= 0:
                    self.log('Fuel tanks already full.')
                    return
                self.player_fuel += amount
                depot['amount'] -= amount
                self.log(f'Refueled {amount:g} units at {depot["name"]}.')
                return
        self.log('Depot not found or out of fuel.')

    def _apply_difficulty_scaling(self):
        for contact in self.contacts:
            if contact.detection_state == DetectionState.UNDETECTED:
                if random.random() < self.config.detection_chance:
                    contact.detection_state = DetectionState.SUSPECTED
                    self.log(f'Sonar: possible contact, {contact.name}.')
            elif contact.detection_state == DetectionState.SUSPECTED:
                if random.random() < self.config.detection_confidence:
                    contact.detection_state = DetectionState.LOCATED
                    self.log(f'Sonar: {contact.name} located.')
            elif contact.detection_state == DetectionState.LOCATED and random.random() < .2:
                contact.detection_state = DetectionState.TRACKED

        threat_count = sum(c.contact_type in (ContactType.SUBMARINE, ContactType.SHIP,
                                             ContactType.DRONE) and
                           c.detection_state in (DetectionState.LOCATED, DetectionState.TRACKED)
                           for c in self.contacts)
        # Contact discovery is not the same as the player's submarine being detected.
        if threat_count and random.random() < self.config.ai_aggression * threat_count / 3:
            self.was_detected = True
            self.player_ship.stealth_level = max(
                0, self.player_ship.stealth_level - self.config.stealth_loss_per_contact)
            self.log('Warning: opposing force may have detected our submarine!')
            if random.random() < self.config.encounter_chance:
                damage = max(1, round(8 * self.config.hull_damage_multiplier))
                self.player_ship.hull_integrity = max(0, self.player_ship.hull_integrity - damage)
                self.log(f'Exercise damage event: hull -{damage}%.')

    def update_suggested_actions(self):
        self.suggested_actions = ['depth 60', 'speed 3', 'sonar', 'transmit marker']
        if self.marker_transmitted:
            self.suggested_actions[3] = 'extract'
        if self.player_ship.hull_integrity < 80:
            self.suggested_actions[2] = 'repair'
        if self.player_fuel < 20:
            self.suggested_actions[2] = 'refuel'

    def get_theater_info(self):
        theater = NavalWorld.get_theater_at(*self.player_ship.position)
        return {'terrain': theater['terrain'], 'base_fuel': theater['base_fuel']}

    def check_mission_conditions(self):
        if self.player_ship.hull_integrity < 30 or self.player_fuel <= 0 or self.player_ship.battery_charge <= 0:
            self.mission.failed = True
            self.log('Mission failed: critical ship resources depleted.')
        elif self.turn >= self.mission.duration:
            self.mission.failed = True
            self.log('Mission failed: exercise deadline reached.')
        if self.mission.failed:
            self.finish_mission(False)

    def finish_mission(self, successful):
        self.mission.completed = bool(successful)
        self.mission.failed = not successful
        self.score = max(0, min(100, (65 if successful else 10)
                                + self.player_ship.hull_integrity // 5
                                + int(self.player_fuel // 10)
                                - (15 if self.was_detected else 0)))
        self.mission.score = self.score
        self.state = GameState.ENDGAME

    def process_command(self, command):
        cmd = command.lower().strip()
        if not cmd:
            return
        if cmd == 'help':
            self.log('Commands: depth N, speed N, heading N, sonar, stealth, repair,')
            self.log('transmit marker, extract, radio, refuel, wait, save, load, help')
            return
        if cmd == 'save':
            self.save_world()
            return
        if cmd == 'load':
            self.load_persistent_state()
            return
        if self.state != GameState.MISSION:
            return

        self.log(f'> {cmd}')
        parts = cmd.split()
        action, value = parts[0], parts[1:]
        ship = self.player_ship
        if action in ('depth', 'speed', 'heading'):
            if len(value) != 1:
                self.log(f'Usage: {action} <number>')
                return
            try:
                number = int(value[0])
            except ValueError:
                self.log('Please enter a whole number.')
                return
            ranges = {'depth': (0, 250), 'speed': (0, 20), 'heading': (0, 359)}
            lo, hi = ranges[action]
            if not lo <= number <= hi:
                self.log(f'{action.title()} must be between {lo} and {hi}.')
                return
            setattr(ship, action, number)
            self.log(f'{action.title()} set to {number}.')
        elif action in ('sonar', 'contacts'):
            self.log('Sonar watch maintained; passive contacts updated.')
        elif action == 'stealth':
            ship.speed = min(ship.speed, 3)
            ship.stealth_level = min(100, ship.stealth_level + 5)
            self.log('Quiet running established.')
        elif action == 'repair':
            self.ship_maintenance_points += self.ship_maintenance
            self.apply_maintenance()
            self.log('Damage control check completed.')
        elif cmd in ('transmit marker', 'transmit', 'marker'):
            self.marker_transmitted = True
            self.log('Exercise marker transmitted to command.')
        elif action == 'extract':
            if not self.marker_transmitted:
                self.log('Transmit the exercise marker before extraction.')
                return
            self.finish_mission(True)
            self.log('USS Razorback safely withdrew from exercise area.')
            return
        elif action in ('radio', 'communicate'):
            self.log('Exercise command acknowledges check-in.')
        elif action == 'refuel':
            theater = NavalWorld.get_theater_at(*ship.position)
            self.refill_from_depot(theater['name'])
        elif action == 'wait':
            self.log('Holding course and depth.')
        else:
            self.log('Unknown command. Type HELP.')
            return

        # Exactly one simulation turn for each valid operational command.
        self._apply_difficulty_scaling()
        self.consume_fuel(ship.speed * 1.852 / 60)  # one simulated minute, km
        ship.battery_charge = max(0, ship.battery_charge - (1 if ship.speed >= 8 else 0))
        ship.mission_clock += 1
        self.update_crew_fatigue()
        self.turn += 1
        self.check_mission_conditions()
        self.update_suggested_actions()

    def draw_text(self, text, x, y, color=WHITE, font=None, max_width=None):
        font = font or self.font_small
        if max_width:
            while text and font.size(text)[0] > max_width:
                text = text[:-2] + '…'
        self.screen.blit(font.render(text, True, color), (x, y))

    def draw_panel(self, rect, title):
        pygame.draw.rect(self.screen, LIGHT_BLUE, rect, 2, border_radius=5)
        self.draw_text(title, rect[0] + 12, rect[1] + 10, YELLOW)
        pygame.draw.line(self.screen, LIGHT_BLUE,
                         (rect[0], rect[1] + 38), (rect[0] + rect[2], rect[1] + 38))

    def draw_menu(self):
        self.screen.fill(DARK_BLUE)
        self.draw_text('OPERATION RUSTBUCKET', 350, 100, YELLOW, self.font_large)
        self.draw_text(f'Difficulty: {self.mode.value}', 440, 190, WHITE, self.font_medium)
        self.draw_text('LEFT / RIGHT: choose difficulty', 420, 245)
        self.draw_text('SPACE: begin or continue mission', 410, 280, GREEN)
        self.draw_text('N: start a new exercise (discard loaded progress)', 370, 325)
        self.draw_text('Type HELP during the mission for commands.', 385, 385)
        pygame.display.flip()

    def draw_mission_screen(self):
        self.screen.fill(DARK_BLUE)
        self.draw_text(f'TURN {self.turn} / {self.mission.duration}  |  {self.mission.description}',
                       20, 16, YELLOW, self.font_medium, 1140)
        self.draw_panel((20, 60, 360, 230), 'USS Razorback - Ship Status')
        ship = self.player_ship
        ship_lines = [f'Hull: {ship.hull_integrity}%    Battery: {ship.battery_charge}%',
                      f'Fuel: {self.player_fuel:.1f} units',
                      f'Depth: {ship.depth} m    Speed: {ship.speed} knots',
                      f'Heading: {ship.heading:03.0f}°    Stealth: {ship.stealth_level}%',
                      f'Torpedoes: {len(ship.weapons)}',
                      f'Maintenance points: {self.ship_maintenance_points}']
        for i, s in enumerate(ship_lines):
            self.draw_text(s, 32, 108 + i * 28)

        self.draw_panel((400, 60, 780, 230), 'Sonar Contacts')
        for i, c in enumerate(self.contacts[:5]):
            display = c.name if c.detection_state != DetectionState.UNDETECTED else 'Unidentified signal'
            self.draw_text(f'{display} | {c.detection_state.name} | {c.bearing:.0f}°',
                           412, 110 + i * 30, GREEN if c.detection_state != DetectionState.UNDETECTED else GRAY)

        self.draw_panel((20, 310, 560, 140), 'Mission Progress')
        self.draw_text(f'Marker transmitted: {"YES" if self.marker_transmitted else "NO"}', 32, 360)
        self.draw_text(f'Possible enemy detection: {"YES" if self.was_detected else "NO"}', 32, 392)
        self.draw_panel((600, 310, 580, 140), 'Suggested Actions')
        for i, action in enumerate(self.suggested_actions[:3]):
            self.draw_text(f'{i+1}. {action}', 612, 354 + i * 26)
        self.draw_text(f'4. {self.suggested_actions[3]}', 850, 354)

        self.draw_panel((20, 470, 1160, 235), 'Message Log')
        for i, line in enumerate(self.message_log[-8:]):
            self.draw_text(line, 32, 518 + i * 22, WHITE, max_width=1120)
        pygame.draw.rect(self.screen, (25, 56, 83), (20, 720, 1160, 55), border_radius=4)
        self.draw_text('> ' + self.command_input + ('_' if pygame.time.get_ticks() // 500 % 2 else ''),
                       32, 737, GREEN, max_width=1125)
        pygame.display.flip()

    def draw_endgame(self):
        self.screen.fill(DARK_BLUE)
        status = 'MISSION SUCCESSFUL' if self.mission.completed else 'MISSION FAILED'
        self.draw_text(status, 360, 115,
                       GREEN if self.mission.completed else RED, self.font_large)
        self.draw_text(f'Final score: {self.score}/100', 450, 210, YELLOW, self.font_medium)
        self.draw_text(f'Hull remaining: {self.player_ship.hull_integrity}%', 430, 290)
        self.draw_text(f'Fuel remaining: {self.player_fuel:.1f}', 430, 325)
        self.draw_text(f'Torpedoes left: {len(self.player_ship.weapons)}', 430, 360)
        self.draw_text('R: restart | M: menu | S: save', 415, 490, GREEN, self.font_medium)
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if self.state == GameState.MENU:
                        modes = list(GameMode)
                        idx = modes.index(self.mode)
                        if event.key == pygame.K_LEFT:
                            self.mode = modes[(idx - 1) % len(modes)]
                        elif event.key == pygame.K_RIGHT:
                            self.mode = modes[(idx + 1) % len(modes)]
                        elif event.key == pygame.K_n:
                            self.initialize_game()
                            self.state = GameState.MISSION
                        elif event.key == pygame.K_SPACE:
                            self.state = GameState.MISSION
                        self.config = MODE_CONFIGS[self.mode]
                    elif self.state == GameState.MISSION:
                        if event.key == pygame.K_RETURN:
                            submitted = self.command_input
                            self.command_input = ''
                            self.process_command(submitted)
                        elif event.key == pygame.K_BACKSPACE:
                            self.command_input = self.command_input[:-1]
                        elif event.key == pygame.K_ESCAPE:
                            self.state = GameState.MENU
                        elif event.unicode and event.unicode.isprintable() and len(self.command_input) < 100:
                            self.command_input += event.unicode
                    elif self.state == GameState.ENDGAME:
                        if event.key == pygame.K_r:
                            self.initialize_game()
                            self.state = GameState.MISSION
                        elif event.key == pygame.K_m:
                            self.state = GameState.MENU
                        elif event.key == pygame.K_s:
                            self.save_world()
            if self.state == GameState.MENU:
                self.draw_menu()
            elif self.state == GameState.MISSION:
                self.draw_mission_screen()
            else:
                self.draw_endgame()
            self.clock.tick(FPS)
        pygame.quit()


if __name__ == '__main__':
    OperationRustbucket().run()
