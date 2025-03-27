from hflee import HFleeEcosystem as Ecosystem
from hflee import HFleePerson
from hflee import HFleeInputGeography
from flee import spawning
from flee.datamanager import handle_refugee_data, read_period
from flee.datamanager import DataTable
import numpy as np
import flee.postprocessing.analysis as a
import sys
from flee.SimulationSettings import SimulationSettings
from datetime import datetime, timedelta

def calculate_hurricane_spawning(hurricane_level):
    """
    Calculate spawning based on hurricane level from simulation settings
    """
    displaced_rates = SimulationSettings.spawn_rules['hurricane_driven_spawning']['displaced_per_flood_day']
    
    if hurricane_level < len(displaced_rates):
        return displaced_rates[hurricane_level]
    
    return displaced_rates[-1]  # Use the last rate if level exceeds defined rates

if __name__ == "__main__":

  start_date, end_time = read_period.read_sim_period("{}/sim_period.csv".format(sys.argv[1]))

  if len(sys.argv) < 4:
    print("Please run using: python3 run.py <your_csv_directory> <your_refugee_data_directory> <duration in days> <optional: simsettings.yml> > <output_directory>/<output_csv_filename>")

  input_csv_directory = sys.argv[1]
  validation_data_directory = sys.argv[2]
  if int(sys.argv[3]) > 0:
    end_time = int(sys.argv[3])

  if len(sys.argv) == 5:
    SimulationSettings.ReadFromYML(sys.argv[4])
  else:
    SimulationSettings.ReadFromYML("simsetting.yml")

  e = Ecosystem()
  
  ig = HFleeInputGeography()
  ig.ReadLocationsFromCSV("%s/locations.csv" % input_csv_directory)
  ig.ReadLinksFromCSV("%s/routes.csv" % input_csv_directory)
  ig.ReadClosuresFromCSV("%s/closures.csv" % input_csv_directory)

  e, lm = ig.StoreInputGeographyInEcosystem(e)

  if SimulationSettings.spawn_rules["read_from_agents_csv_file"]:
      ig.ReadAgentsFromCSV(e, "%s/agents.csv" % input_csv_directory)

  d = handle_refugee_data.RefugeeTable(csvformat="generic", data_directory=validation_data_directory, start_date=start_date, data_layout="data_layout.csv", population_scaledown_factor=SimulationSettings.optimisations["PopulationScaleDownFactor"], start_empty=SimulationSettings.spawn_rules["EmptyCampsOnDay0"])
  d.ReadL1Corrections("%s/registration_corrections.csv" % input_csv_directory)

  output_header_string = "Day,Date," #debug
  camp_locations = e.get_camp_names()

  for l in camp_locations:
      spawning.add_initial_refugees(e, d, lm[l])
      output_header_string += "%s sim,%s data,%s error," % (lm[l].name, lm[l].name, lm[l].name)#debug

  output_header_string += "Total error,refugees in camps (UNHCR),total refugees (simulation),raw UNHCR refugee count,refugees in camps (simulation),refugee_debt"#debug

  if e.getRankN(0):#debug
      print(output_header_string)#debug

  refugee_debt = 0
  refugees_raw = 0

  for t in range(0, end_time):
    ig.AddNewConflictZones(e, t)
    ig.UpdateLocationAttributes(e, "hurricane_level", t)

    # 🌪️ Hurricane-driven spawning
    hurricane_data = getattr(ig, "hurricane_data", {})
    h_spawn = SimulationSettings.spawn_rules.get("hurricane_driven_spawning", {})
    displaced_per_day = h_spawn.get("displaced_per_flood_day", [0.0] * 5)

    if t in hurricane_data:
        for loc_name, level in hurricane_data[t].items():
            if loc_name in e.locations:
                loc = e.locations[loc_name]
                loc.attributes["hurricane_level"] = level

                # Calculate number of people to spawn
                spawn_ratio = displaced_per_day[min(level, len(displaced_per_day) - 1)]
                if spawn_ratio > 0:
                    num_to_spawn = int(loc.population * spawn_ratio)
                    for _ in range(num_to_spawn):
                        e.add_hflee_person(loc)

    spawn_locs = [loc for loc in e.locations if loc.spawn_weight > 0]

    if spawn_locs:
        new_refs, refugees_raw, refugee_debt = spawning.spawn_daily_displaced(e, t, d)
    else:
        new_refs, refugees_raw, refugee_debt = 0, 0, 0  # No valid spawn locations this step
    spawning.refresh_spawn_weights(e)
    e.enact_border_closures(t)
    e.evolve()

    errors = []
    abs_errors = []
    loc_data = []

    camps = []
    for i in camp_locations:
      camps += [lm[i]]
      loc_data += [d.get_field(i, t)]

    refugees_in_camps_sim = sum(c.numAgents for c in camps)

    j=0
    for i in camp_locations:
      errors += [a.rel_error(lm[i].numAgents, loc_data[j])]
      abs_errors += [a.abs_error(lm[i].numAgents, loc_data[j])]

      j += 1


    date = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=t)
    output = "%s,%s" % (t, date.strftime("%Y-%m-%d"))

    for i in range(0,len(errors)):
      output += ",%s,%s,%s" % (lm[camp_locations[i]].numAgents, loc_data[i], errors[i])

    if refugees_raw>0:
      output += ",%s,%s,%s,%s,%s,%s" % (float(np.sum(abs_errors))/float(refugees_raw), int(sum(loc_data)), e.numAgents(), refugees_raw, refugees_in_camps_sim, refugee_debt)
    else:
      output += ",0.0,0,{},0,{},0".format(e.numAgents(), refugees_in_camps_sim)

    if SimulationSettings.log_levels["idp_totals"] > 0:
      output += ",{}".format(e.numIDPs())

    if e.getRankN(t):
        print(output)