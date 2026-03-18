# Base interactions and objects
from interactions.base.super_interaction import SuperInteraction
from objects.script_object import ScriptObject

# Core Sims classes
from sims.sim import Sim
from sims.sim_info import SimInfo
from sims4.tuning.instances import lock_instance_tunables
from sims4.tuning.tunable import Tunable
import sims4.resources
import services

from event_testing.test_events import TestEvent
from interactions.utils.loot import LootActions

# Events, buffs, and stats
from buffs.buff import Buff
from sims4.resources import Types



# The original interaction


# Utility functions
import sims4.log
import random

# Set up logging
logger = sims4.log.Logger('MattyGMod', default_owner='MattyG')



VOMIT_BUFF_ID = "Loot_Buff_Sickness_NeedToPuke"  # This is the “Sick” buff in the base game
VAPE_INTERACTION_NAME = 'Basemental:Tobacco_Vaporizer_Smoke_Interaction'
VAPE_INTERACTION_ID = 0xFA672665D7CADF8E


    


    
def on_interaction_start(sim, interaction):
    sims4.log.debug(f"Interaction GUID: {getattr(interaction, 'guid64', None)}")
    if getattr(interaction, 'guid64', None) == VAPE_INTERACTION_ID:
        sims4.log.debug(f"[VapeListener] {sim} used the vape!")
        
        if (sim.sim_info.first_name == "Matthew" and sim.sim_info.last_name == "Grant"):
            sim.run_loot_action_on_sim(VOMIT_BUFF_ID, sim)
        
def register_global_listener():
    sim_manager = services.sim_info_manager()
    for sim_info in sim_manager.get_all():
        sim = sim_info.get_sim_instance()
        if sim is not None:
            sim.register_for_event(TestEvent.InteractionStart, on_interaction_start)

# Call this once at mod load

def on_zone_load(*_, **__):
    register_global_listener()

# Register the zone load callback
import zone
zone.Zone.on_loading_screen_animation_finished = on_zone_load
