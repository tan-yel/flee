from flee.SimulationSettings import SimulationSettings
from flee.flee import Person, Ecosystem
from flee.InputGeography import InputGeography
import csv


class HFleePerson(Person):
    def choose_destination(self):
        if self.location.location_type == "evacuation_zone":
            safe_routes = [link.endpoint for link in self.location.links if link.endpoint.location_type in ["camp", "safe_zone"]]

            if not safe_routes:
                return None
            
            return min(safe_routes, key=lambda loc:loc.distance)
        
        return None

class HFleeEcosystem(Ecosystem):
    def add_hflee_person(self, location, movechance=None, awareness=None, speed=None):
        """
        Create a person with hurricane-aware move chance
        """
        # If no movechance provided, use default or calculate based on hurricane level
        if movechance is None:
            hurricane_level = location.attributes.get('hurricane_level', 0)
            hurricane_movechances = SimulationSettings.move_rules.get("HurricaneMovechances", [0.6]*5)
            movechance = hurricane_movechances[min(hurricane_level, len(hurricane_movechances)-1)]

        # Use default awareness and speed if not provided
        awareness = awareness or SimulationSettings.move_rules.get('awareness_level', 1)
        speed = speed or (1.0 if SimulationSettings.move_rules.get('start_on_foot', True) else 0.5)
        
        person = HFleePerson(location, movechance, awareness, speed)
        self.agents.append(person)
    
    def evolve(self):
        for agent in self.agents:
            print(f"Agent type: {type(agent)}")  # Debug: check agent class
            if hasattr(agent, "movechance") and agent.movechance > 0:
                agent.update_location()

            hurricane_level = agent.location.attributes.get('hurricane_level', 0)
            
            # Determine if agent should move based on hurricane level and move chance
            if hurricane_level >= 3:  # Mandatory evacuation for Category 1 and above
                destination = agent.choose_destination()
                if destination:
                    agent.move_to(destination)
            elif agent.movechance > 0:
                # Optional movement for lower hurricane levels
                destination = agent.choose_destination()
                if destination:
                    agent.move_to(destination)

class HFleeInputGeography(InputGeography):
    
    def __init__(self):
        super().__init__()
        self.hurricane_data = {}
        print("HFleeInputGeography is being used!")

    def UpdateLocationAttributes(self, e, attribute_name, time):
        """
        Update location attributes while handling missing keys.
        """
        attrlist = self.attributes.get(attribute_name, {})  # Prevents KeyError

        if not attrlist:
            print(f"Warning: '{attribute_name}' attribute is missing or empty.", file = sys.stderr)
            return
        
        if attribute_name == "hurricane_level":
            level_data = self.hurricane_data.get(time, {})
            for loc in e.locations:
                if loc.name in level_data:
                    loc.attributes["hurricane_level"] = level_data[loc.name]

        super().UpdateLocationAttributes(e, attribute_name, time)
    
    def ReadHurricaneData(self, filename):
        with open(filename) as f:
            reader = csv.DictReader(f)
            for row in reader:
                loc = row["name"].strip()
                time = int(row["time"])
                level = int(row["hurricane_level"])
                if time not in self.hurricane_data:
                    self.hurricane_data[time] = {}
                self.hurricane_data[time][loc] = level

