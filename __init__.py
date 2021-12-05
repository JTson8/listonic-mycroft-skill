# Copyright 2016 Mycroft AI, Inc.
#
# This file is part of Mycroft Core.
#
# Mycroft Core is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mycroft Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mycroft Core.  If not, see <http://www.gnu.org/licenses/>.
import json

import requests
from mycroft import MycroftSkill, intent_handler
from adapt.intent import IntentBuilder


class ListonicSkill(MycroftSkill):
    def __init__(self):
        """ The __init__ method is called when the Skill is first constructed.
        It is often used to declare variables or perform setup actions, however
        it cannot utilise MycroftSkill methods as the class does not yet exist.
        """
        super().__init__()
        self.learning = True
        self.access_token = ""

    def initialize(self):
        """ Perform any final setup needed for the skill here.
        This function is invoked after the skill is fully constructed and
        registered with the system. Intents will be registered and Skill
        settings will be available."""
        self.login()

    @intent_handler(IntentBuilder("AddToList").require("Add").require("Seperator").optionally("AddItem").optionally("ListName").build())
    def handle_list_intent(self, message):
        list_id = ""
        item_name = message.data.get('AddItem')
        list_name = message.data.get('ListName')
        self.log.info(message.utterance_remainder())

        if item_name is None:
            self.speak_dialog("no item given to add to list")
            return
        if list_name is None:
            self.speak_dialog("no list given to add item")
            return

        if self.settings.get('list_1_name') is not None \
                and list_name == self.settings.get('list_1_name').lower():
            list_id = self.settings.get('list_1_id')
        elif self.settings.get('list_2_name') is not None \
                and list_name == self.settings.get('list_2_name').lower():
            list_id = self.settings.get('list_2_id')
        elif self.settings.get('list_3_name') is not None \
                and list_name == self.settings.get('list_3_name').lower():
            list_id = self.settings.get('list_3_id')

        if list_id is None or list_id == "":
            self.speak_dialog("no list found by that name")
        else:
            self.handle_request(list_id, item_name, list_name)

    def stop(self):
        pass

    def handle_request(self, list_id, item, list_name, second_time=False):
        url = 'https://hl2api.listonic.com/api/lists/' + list_id + '/items'
        headers = {'Authorization': 'Bearer ' + self.access_token}
        self.log.info(self.access_token)
        self.log.info(list_id)
        payload = {'SortOrder': None, 'Name': item, 'ListId': list_id, 'Amount': "", "Unit": ""}
        self.log.info(payload)
        r = requests.post(url, json=payload, headers=headers)
        if r.status_code == 401:
            if second_time:
                self.speak_dialog("Authorization failed")
            else:
                self.login()
                self.handle_request(list_id, item, list_name, True)
        elif r.status_code == 201:
            self.speak_dialog("I have added " + item + " to " + list_name)
        else:
            self.log.info(r.status_code)
            self.speak_dialog("Could not add " + item + " to " + list_name)

    def login(self):
        url = 'https://hl2api.listonic.com/api/loginextended?provider=password&autoMerge=1&autoDestruct=1'
        headers = {'ClientAuthorization': 'Bearer bGlzdG9uaWN2MjpmamRmc29qOTg3NGpkZmhqa2gzNGpraGZmZGZmZg=='}
        user_name = self.settings.get('my_email')
        if user_name is None:
            user_name = ""
        password = self.settings.get('my_password')
        if password is None:
            password = ""
        payload = "username=" + user_name + "&password=" + password + "&client_id=listonicv2&client_secret=fjdfsoj9874jdfhjkh34jkhffdfff"
        r = requests.post(url, data=payload, headers=headers)
        if r.status_code == 200:
            output = r.json()
            if 'access_token' in output.keys():
                self.access_token = output["access_token"]


def create_skill():
    return ListonicSkill()
