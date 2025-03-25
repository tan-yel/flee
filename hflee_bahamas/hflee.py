from flee.SimulationSettings import SimulationSettings
from flee.flee import Person, Ecosystem
from flee.InputGeography import InputGeography

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
            
            # Use flood_movechances from simulation settings as a template
            move_chances = SimulationSettings.move_rules.get('flood_movechances', [0.5, 0.9, 1.0, 1.0, 1.0])
            
            # Default to the last move chance if hurricane level exceeds defined levels
            movechance = move_chances[hurricane_level] if hurricane_level < len(move_chances) else move_chances[-1]
        
        # Use default awareness and speed if not provided
        awareness = awareness or SimulationSettings.move_rules.get('awareness_level', 1)
        speed = speed or (1.0 if SimulationSettings.move_rules.get('start_on_foot', True) else 0.5)
        
        person = HFleePerson(location, movechance, awareness, speed)
        self.agents.append(person)
    
    def evolve(self):
        """
        Evolve the ecosystem with hurricane-specific movement rules
        """
        for agent in self.agents:
            # Check hurricane level at current location
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
        print("HFleeInputGeography is being used!")

    def UpdateLocationAttributes(self, e, attribute_name: str, time: int) -> None:

        super().UpdateLocationAttributes(e, attribute_name, time)
        if attribute_name == "hurricane_level":
            attrlist = self.attributes.get(attribute_name, {})

            for loc in e.locations:
                loc_name = loc.name
                if loc_name in attrlist:
                    loc.attributes[attribute_name] = int(attrlist[loc_name])
                else:    
                    loc.attributes[attribute_name] = 0
