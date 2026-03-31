# mattygmod_vape_vomit.py
# Hooks into Basemental Drugs vape interaction and applies a vomit buff
# to Matthew Grant whenever he uses the vaporizer.
#
# INSTALL: Drop this .py file into your Sims 4 Mods folder (or a subfolder).
# Tested against: Sims 4 (latest EA patch), Basemental Drugs

# ── Core game imports ────────────────────────────────────────────────────────
import sims4.log
import sims4.localization
import sims4.resources
import services
import zone
import interactions.context
import interactions.priority

from event_testing.test_events import TestEvent
from ui.ui_dialog_notification import UiDialogNotification

# ── Logging ──────────────────────────────────────────────────────────────────
logger = sims4.log.Logger('MattyGMod', default_owner='MattyG')

# ── Config ───────────────────────────────────────────────────────────────────
DEBUG_MODE = True

# GUID64 of the Basemental vaporizer smoke interaction.
# Verify in-game with the debug notifications below; update if needed.
VAPE_INTERACTION_ID = 0xFA672665D7CADF8E

# Numeric tuning ID of the buff to apply.
# "e_Buff_Sickness_NeedToPuke" hashed value – replace with the correct int if
# the buff lookup fails (check logger output).
# You can find the correct value by opening the buff's .xml tuning file and
# reading the `s=` attribute on the <I> tag, then converting hex → int.
PUKE_AFFORDANCE_ID = 102305  
NAUSEA_BUFF_ID = 98267

# Sim to target
TARGET_FIRST_NAME = "Matthew"
TARGET_LAST_NAME  = "Grant"

# ── State ────────────────────────────────────────────────────────────────────
_listener_registered = False
_puke_in_progress = False


# ── Notification helper ──────────────────────────────────────────────────────
def _notify(text: str) -> None:
    
    if not DEBUG_MODE:
        return
    try:
        
        client = services.client_manager().get_first_client()
        if client is None:
            logger.warn('MattyGMod: _notify called but no client found.')
            return
        sim = client.active_sim
        if sim is None:
            logger.warn('MattyGMod: _notify called but active_sim is None.')
            return

        localized_text  = lambda **_: sims4.localization.LocalizationHelperTuning.get_raw_text(text)
        localized_title = lambda **_: sims4.localization.LocalizationHelperTuning.get_raw_text('MattyGMod')

        notification = UiDialogNotification.TunableFactory().default(
            sim,
            text=localized_text,
            title=localized_title,
        )
        notification.show_dialog()
    except Exception as exc:
        # Never let a debug helper crash the game
        logger.error(f'MattyGMod: _notify raised {exc}')


# ── Buff application ─────────────────────────────────────────────────────────
def _apply_vomit(sim) -> None:
    global _puke_in_progress
    if _puke_in_progress:
        _notify('[MattyGMod] Vomit already in progress, skipping.')
        return
    _puke_in_progress = True
    try:
        # Step 1: apply the nausea buff so the interaction test passes
        buff_manager = services.get_instance_manager(sims4.resources.Types.BUFF)
        buff_type = buff_manager.get(NAUSEA_BUFF_ID)
        if buff_type is None:
            _notify(f'[MattyGMod] Could not find nausea buff {NAUSEA_BUFF_ID}')
            return
        sim.add_buff(buff_type, None, 250)
        _notify('[MattyGMod] Nausea buff applied!')

        # Step 2: now push the puke interaction
        """ interaction_manager = services.get_instance_manager(sims4.resources.Types.INTERACTION)
        affordance = interaction_manager.get(PUKE_AFFORDANCE_ID)
        if affordance is None:
            _notify(f'[MattyGMod] Could not find puke interaction {PUKE_AFFORDANCE_ID}')
            return
        context = interactions.context.InteractionContext(
            sim,
            interactions.context.InteractionContext.SOURCE_SCRIPT,
            interactions.priority.Priority.High,
            insert_strategy=interactions.context.QueueInsertStrategy.NEXT
        )
        result = sim.push_super_affordance(affordance, sim, context)
        _notify(f'[MattyGMod] Push result: {result}') """

    except Exception as exc:
        _notify(f'[MattyGMod] _apply_vomit error: {exc}')
    finally:
        _puke_in_progress = False


# ── Event callback ───────────────────────────────────────────────────────────
class _VapeEventHandler:
    def handle_event(self, sim_info, event_type, resolver):
        try:
            interaction = resolver.interaction if hasattr(resolver, 'interaction') else None
            if interaction is None:
                return

            guid = getattr(interaction, 'guid64', None)

            if DEBUG_MODE:
                module = type(interaction).__module__ or ''
                if 'basemental' in module.lower():
                    name = type(interaction).__name__
                    guid_str = hex(guid) if guid is not None else 'None'
                    _notify(f'[BM] {name}\n{guid_str}')

            if guid != VAPE_INTERACTION_ID:
                return

            sim = getattr(interaction, 'sim', None)
            if sim is None:
                return

            first = getattr(sim.sim_info, 'first_name', '')
            last  = getattr(sim.sim_info, 'last_name', '')

            _notify(f'[MattyGMod] Vape detected on {first} {last}')

            if first == TARGET_FIRST_NAME and last == TARGET_LAST_NAME:
                _apply_vomit(sim)

        except Exception as exc:
            _notify(f'[MattyGMod] handle_event error: {exc}')

_vape_handler = _VapeEventHandler()

# ── Listener registration ────────────────────────────────────────────────────
def _register_listener() -> None:
    
    global _listener_registered
    if _listener_registered:
        return
    try:
        event_manager = services.get_event_manager()
        event_manager.register_single_event(_vape_handler, TestEvent.InteractionComplete)
        _listener_registered = True
        _notify('[MattyGMod] Listener registered!')
    except Exception as exc:
        _notify(f'[MattyGMod] Register failed: {exc}')

# ── Zone load hook ───────────────────────────────────────────────────────────
# Safely CHAIN into on_loading_screen_animation_finished instead of replacing it.
# Replacing it (what the original code did) destroys critical game setup and
# bricks saves / build mode.

_original_zone_load = zone.Zone.on_loading_screen_animation_finished

def _patched_zone_load(self, *args, **kwargs):
    # Always run the game's original method first
    _original_zone_load(self, *args, **kwargs)
    try:
        logger.info('MattyGMod: Zone finished loading – registering listener.')
        _notify('[MattyGMod] Zone loaded!')
        _register_listener()
    except Exception as exc:
        logger.error(f'MattyGMod: _patched_zone_load raised {exc}')

zone.Zone.on_loading_screen_animation_finished = _patched_zone_load