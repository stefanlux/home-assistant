import logging

import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.knx import (KNXConfig, KNXMultiAddressDevice)
from homeassistant.components.light import ATTR_BRIGHTNESS, Light, PLATFORM_SCHEMA, SUPPORT_BRIGHTNESS
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv

CONF_ADDRESS = 'onoff_address'
CONF_ONOFF_STATE_ADDRESS = 'onoff_state_address'
CONF_BRIGHTNESS_ADDRESS = 'brightness_address'
CONF_BRIGHTNESS_STATE_ADDRESS = 'brightness_state_address'

DEFAULT_NAME = 'KNX Switch'
DEPENDENCIES = ['knx']
SUPPORT_KNX = SUPPORT_BRIGHTNESS

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ADDRESS): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_ONOFF_STATE_ADDRESS): cv.string,
    vol.Optional(CONF_BRIGHTNESS_ADDRESS): cv.string,
    vol.Optional(CONF_BRIGHTNESS_STATE_ADDRESS): cv.string
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Awesome Light platform."""
    add_devices([KNXLight(hass, KNXConfig(config), ['onoff', 'brightness', 'onoff_state', 'brightness_state'], [])])


class KNXLight(KNXMultiAddressDevice, Light):
    """Representation of an Awesome Light."""

    def __init__(self, hass, config, required, optional):
        _LOGGER.info("Init KNXLight")
        self._brightness = 0
        KNXMultiAddressDevice.__init__(self, hass, config, required, optional)

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_KNX

    def turn_on(self, **kwargs):
        """Turn the switch on.

        This sends a value 0 to the group address of the device
        """
        _LOGGER.info("Turn on")
        self._state = 1
        self.set_value('onoff', [1])
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness:
            _LOGGER.info("Set Brightness %d", brightness)
            self._brightness = brightness
            self.set_value('brightness', [brightness])
        if not self.should_poll:
            self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the switch off.

        This sends a value 1 to the group address of the device
        """
        _LOGGER.info("Turn off")
        self._state = 0
        self.set_value('onoff', [0])
        self._state = [0]
        if not self.should_poll:
            self.schedule_update_ha_state()

    @property
    def brightness(self):
        """Brightness of the light (an integer in the range 1-255).

        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        if self._brightness is not None:
            return self._brightness
        else:
            return None

    @property
    def is_on(self):
        """Return True if the value is not 0 is on, else False."""
        return self._state != 0

    def update(self):
        _LOGGER.info("Update")
        """Get the state from KNX bus or cache."""
        from knxip.core import KNXException

        try:
            state = self.value('onoff_state')[0]
            _LOGGER.info("Updated state %d", state)
            self._state = state
            brightness = self.value('brightness_state')[0]
            _LOGGER.info("Updated brightness %d", brightness)
            self._brightness = brightness

        except KNXException:
            _LOGGER.exception(
                "Unable to read from KNX address: %s", self.address)
            return False