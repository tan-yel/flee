from flee.flee import Person, Ecosystem
from flee.InputGeography import InputGeography

class HFleePerson(Person):
    def choose_destination(self):
        if self.location.location_type == "evacuation_zone":
            safe_routes = [link.endpoint for link in self.lcoation.links if link.endpoint.location_type in ["shelter", "safe_zone"]]

            if not safe_routes:
                return None
            
            return min(safe_routes, key=lambda loc:loc.distance)
        
        return None

class HFleeEcosystem(Ecosystem):
    def add_hflee_person(self, location, movechance, awareness, speed):
        person = HFleePerson(location, movechance, awareness, speed)
        self.agents.append(person)
    
    def evolve(self):
        for agent in self.agents:
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
