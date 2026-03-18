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
VOMIT_BUFF_TUNING_ID = 0x4E84D1A5  # placeholder – verify against your game files

# Sim to target
TARGET_FIRST_NAME = "Matthew"
TARGET_LAST_NAME  = "Grant"

# ── State ────────────────────────────────────────────────────────────────────
_listener_registered = False


# ── Notification helper ──────────────────────────────────────────────────────
def _notify(text: str) -> None:
    """Show an in-game notification. Only fires when DEBUG_MODE is True."""
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
def _apply_vomit_buff(sim) -> None:
    """
    Look up VOMIT_BUFF_TUNING_ID in the buff instance manager and apply it
    directly to the sim's buff component.
    """
    try:
        buff_manager = services.get_instance_manager(sims4.resources.Types.BUFF)
        buff_type = buff_manager.get(VOMIT_BUFF_TUNING_ID)

        if buff_type is None:
            msg = (
                f'MattyGMod: Could not find buff with ID {hex(VOMIT_BUFF_TUNING_ID)}. '
                f'Update VOMIT_BUFF_TUNING_ID in the mod source.'
            )
            logger.error(msg)
            _notify(msg)
            return

        # _buffs is the BuffComponent; add_buff_from_op is the standard
        # runtime path for programmatically adding a buff.
        sim.sim_info._buffs.add_buff_from_op(buff_type)
        logger.info(f'MattyGMod: Applied vomit buff to {sim}.')
        _notify(f'[MattyGMod] Vomit buff applied to {sim.sim_info.first_name}!')

    except Exception as exc:
        logger.error(f'MattyGMod: _apply_vomit_buff raised {exc}')


# ── Event callback ───────────────────────────────────────────────────────────
def _on_interaction_start(event_type, resolver) -> None:
    """
    Fired by the event manager for every InteractionStart event.

    resolver.interaction  – the interaction that just started
    resolver.sim          – NOT reliable here; pull sim from the interaction
    """
    try:
        interaction = resolver.interaction
        if interaction is None:
            return

        guid = getattr(interaction, 'guid64', None)

        # Debug: log every interaction GUID so you can verify the vape ID
        if DEBUG_MODE:
            logger.info(f'MattyGMod: InteractionStart guid={hex(guid) if guid else None}')

        if guid != VAPE_INTERACTION_ID:
            return

        sim = getattr(interaction, 'sim', None)
        if sim is None:
            return

        sim_info = sim.sim_info
        first = getattr(sim_info, 'first_name', '')
        last  = getattr(sim_info, 'last_name', '')

        _notify(f'[MattyGMod] Vape interaction detected on {first} {last}')

        if first == TARGET_FIRST_NAME and last == TARGET_LAST_NAME:
            logger.info('MattyGMod: Target sim used vape – applying buff.')
            _apply_vomit_buff(sim)

    except Exception as exc:
        logger.error(f'MattyGMod: _on_interaction_start raised {exc}')


# ── Listener registration ────────────────────────────────────────────────────
def _register_listener() -> None:
    """
    Register the InteractionStart listener with the global event manager.
    Safe to call multiple times – the guard prevents double-registration.
    """
    global _listener_registered
    if _listener_registered:
        return

    try:
        event_manager = services.get_event_manager()
        # register() signature: (event_type, handler, [sim_info_id])
        # Omitting sim_info_id registers globally (all sims).
        event_manager.register(TestEvent.InteractionStart, _on_interaction_start)
        _listener_registered = True
        logger.info('MattyGMod: InteractionStart listener registered.')
        _notify('[MattyGMod] Listener registered successfully!')
    except Exception as exc:
        logger.error(f'MattyGMod: _register_listener raised {exc}')


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