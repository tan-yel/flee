from flee.SimulationSettings import SimulationSettings, fetchss
from flee.flee import Person, Ecosystem
from flee.InputGeography import InputGeography
import csv
import sys

print("HFlee loaded successfully!")

class HFleePerson(Person):
    def choose_destination(self):
        if self.location.attributes.get("custom_type") == "evacuation_zone":
            # Ask the ecosystem if we should evacuate
            if self.ecosystem.should_evacuate(self.location):
                safe_routes = [link.endpoint for link in self.location.links
                               if link.endpoint.attributes.get("custom_type") == "safe_zone"]

                if not safe_routes:
                    return None

                return min(safe_routes, key=lambda loc: loc.distance)
        return None

class HFleeEcosystem(Ecosystem):
    def __init__(self):
        super().__init__()
        self.evacuation_threshold = SimulationSettings.spawn_rules.get("evacuation_threshold", 3)
        self.impact_map = SimulationSettings.spawn_rules.get("hurricane_impact_map", {
            1: 0.3, 2: 0.5, 3: 0.7, 4: 0.9, 5: 1.0
        })
        self.print_hurricane_impact_map()

    def print_hurricane_impact_map(self):
        print("[HFlee] Hurricane Impact Levels:", file=sys.stderr)
        for level in sorted(self.impact_map):
            print(f"[HFlee]   {level}: {self.impact_map[level]} movechance", file=sys.stderr)

    def assess_hurricane_impact(self, location, hurricane_level):
        return self.impact_map.get(hurricane_level, 0.0)

    def should_evacuate(self, location):
        hurricane_level = location.attributes.get('hurricane_level', 0)
        return hurricane_level >= self.evacuation_threshold

    def add_hflee_person(self, location, movechance=None, awareness=None, speed=None):
        if movechance is None:
            hurricane_level = location.attributes.get('hurricane_level', 0)
            movechance = self.assess_hurricane_impact(location, hurricane_level)

        p = HFleePerson(location, self, movechance, awareness=awareness, speed=speed)
        self.people.append(p)
        location.add_person(p)

class HFleeInputGeography(InputGeography):
    def __init__(self):
        super().__init__()
        self.hurricane_data = {}
        print("[HFlee] HFleeInputGeography initialized", file=sys.stderr)

    def ReadLocationsFromCSV(self, csv_name):
        super().ReadLocationsFromCSV(csv_name)

    def UpdateLocationAttributes(self, e, attribute_name, time):
        if attribute_name == "flood_level":
            if not hasattr(self, "_flood_warned"):
                print("[HFlee][INFO] Skipping 'flood_level' — not used in HFlee.", file=sys.stderr)
                self._flood_warned = True
            return

        if attribute_name == "hurricane_level":
            level_data = self.hurricane_data.get(time, {})
            for loc in e.locations:
                if loc.name in level_data:
                    loc.attributes["hurricane_level"] = level_data[loc.name]
        else:
            super().UpdateLocationAttributes(e, attribute_name, time)
    
    def ReadHurricaneData(self, filename):
        print(f"[HFlee] Reading hurricane impact matrix from {filename}", file=sys.stderr)

        try:
            with open(filename, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    time = int(row["#Day"])
                    for location_name, level_str in row.items():
                        if location_name == "#Day":
                            continue
                        hurricane_level = int(level_str)
                        self.hurricane_data.setdefault(time, {})[location_name.strip()] = hurricane_level

            print(f"[HFlee] Loaded hurricane data for {len(self.hurricane_data)} time steps", file=sys.stderr)

        except FileNotFoundError:
            print(f"[HFlee][ERROR] File '{filename}' not found. Skipping hurricane data.", file=sys.stderr)


