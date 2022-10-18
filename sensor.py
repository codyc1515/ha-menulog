"""Menulog sensors"""
from datetime import datetime, timedelta

import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.entity import Entity

from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .api import MenulogApi

from .const import (
    DOMAIN,
    SENSOR_NAME
)

NAME = DOMAIN
ISSUEURL = "https://github.com/codyc1515/hacs_menulog/issues"

STARTUP = f"""
-------------------------------------------------------------------
{NAME}
This is a custom component
If you have any issues with this you need to open an issue here:
{ISSUEURL}
-------------------------------------------------------------------
"""

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string
})

SCAN_INTERVAL = timedelta(seconds=60)

async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    email = config.get(CONF_EMAIL)
    password = config.get(CONF_PASSWORD)
    
    api = MenulogApi(email, password)

    _LOGGER.debug('Setting up sensor(s)...')

    sensors = []
    sensors.append(MenulogDeliveriesSensor(SENSOR_NAME, api))
    async_add_entities(sensors, True)

class MenulogDeliveriesSensor(Entity):
    def __init__(self, name, api):
        self._name = name
        self._icon = "mdi:truck-delivery"
        self._state = ""
        self._state_attributes = {}
        self._unit_of_measurement = None
        self._device_class = "running"
        self._unique_id = DOMAIN
        self._api = api

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._state_attributes

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id
    
    def update(self):
        _LOGGER.debug('Checking login validity')
        if self._api.check_auth():
            _LOGGER.debug('Fetching deliveries')
            response = self._api.get_deliveries()
            if response['orders'] and response['orders'][0]:
                _LOGGER.debug(response['orders'][0])
                
                order = response['orders'][0]
                
                if order['status']['value'] == "Accepted":
                    self._state = "Order accepted"
                elif order['status']['value'] == "AssigningDriver":
                    self._state = "Assigning driver"
                elif order['status']['value'] == "DriverAssigned":
                    self._state = "Driver assigned"
                elif order['status']['value'] == "DriverArrivedAtRestaurant":
                    self._state = "Driver arrived at restaurant"
                elif order['status']['value'] == "OnItsWay":
                    self._state = "On its way"
                elif order['status']['value'] == "DriverArrivingAtCustomer":
                    self._state = "Driver arriving at customer"
                elif order['status']['value'] == "Completed":
                    self._state = "Completed"
                else:
                    self._state = "Unknown statusValue (" + str(order['status']['value']) + ")"
                
                #self._state_attributes['Order Id'] = order['uuid']
                self._state_attributes['ETA'] = order['status']['currentDueDate']
                self._state_attributes['Restaurant Name'] = order['restaurant']['displayName']
                #self._state_attributes['Courier Name'] = order['contacts'][0]['title']
                
                #if order['feedCards'][1]['mapEntity']:
                #    if order['feedCards'][1]['mapEntity'][0]:
                #        self._state_attributes['Courier Location'] = str(order['feedCards'][1]['mapEntity'][0]['latitude']) + ',' + str(order['feedCards'][1]['mapEntity'][0]['longitude'])
            else:
                self._state = "None"
        else:
            _LOGGER.error('Unable to log in')
