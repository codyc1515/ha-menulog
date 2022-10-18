"""Menulog API"""
import logging
from datetime import datetime, timedelta
import requests
from requests.auth import HTTPBasicAuth
import json

_LOGGER = logging.getLogger(__name__)

class MenulogApi:
    def __init__(self, email, password):
        self._token = ''
        self._email = email
        self._password = password
        self._locale_code = 'NZ'
        self._server_code = 'aus'
        self._url_base = 'https://' + self._server_code + '.api.just-eat.io'
        self._url_base_login = 'https://auth.menulog.co.' + self._locale_code.lower()
        
    def get_deliveries(self):
        headers = {
            "Accept-Tenant": self._locale_code,
            "x-je-applicationvariant": "live",
            "Authorization": "Bearer " + self._token,
            "User-Agent": "Menulog/34.60.0 (2106) iPadOS 16.1/iPad"
        }
        response = requests.get(self._url_base + '/consumer/me/orders/' + self._locale_code + '?pagination=', headers=headers)
        data = {}
        if response.status_code == requests.codes.ok:
            data = response.json()
            if not data:
                _LOGGER.warning('Fetched deliveries successfully, but did not find any')
            return data
        else:
            _LOGGER.error('Failed to fetch deliveries')
            return data

    def check_auth(self):
        """Check to see if our API Token is valid."""
        if self._token:
            _LOGGER.debug('Checking token validity')
            headers = {
                "Accept-Tenant": self._locale_code,
                "x-je-applicationvariant": "live",
                "Authorization": "Bearer " + self._token,
                "User-Agent": "Menulog/34.60.0 (2106) iPadOS 16.1/iPad"
            }
            response = requests.get(self._url_base + "/applications/international/consumer/me", headers=headers)
            if response.status_code == requests.codes.ok:
                _LOGGER.debug('Token is valid')
                return True
            else:
                _LOGGER.info('Token has expired, logging in again...')
                if self.login() == False:
                    _LOGGER.error(response.message)
                    return False
                return True
        else:
            _LOGGER.info('First load, logging in...')
            if self.login() == False:
                _LOGGER.error(response.message)
                return False
            return True

    def login(self):
        """Login to the Menulog API."""
        result = False
        headers = {
            "Authorization": "Basic Y29uc3VtZXJfaW9zX2plOjExMGM5ZjZmLTRmNGItNDc0ZS04NjJmLTk5OWU0NGIwYjc1Nw==",
            "User-Agent": "Menulog/34.60.0 (2106) iPadOS 16.1/iPad"
        }
        data = {
            "client_id": "consumer_ios_je",
            "grant_type": "password",
            "scope": "openid mobile_scope offline_access",
            "tenant": self._locale_code.lower(),
            "username": self._email,
            "password": self._password
        }
        loginResult = requests.post(self._url_base_login + "/connect/token", data=data, headers=headers)
        if loginResult.status_code == requests.codes.ok:
            jsonResult = loginResult.json()
            self._token = jsonResult['access_token']
            _LOGGER.debug('Logged in')
            self.get_deliveries()
            result = True
        else:
            _LOGGER.debug('Failed to login')
            _LOGGER.error(loginResult.error_description)
        return result
