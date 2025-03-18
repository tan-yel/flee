from flee import Person, Ecosystem

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