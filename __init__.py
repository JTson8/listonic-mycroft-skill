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
        self.cached_list = []
        self.cached_version = ""

    def initialize(self):
        """ Perform any final setup needed for the skill here.
        This function is invoked after the skill is fully constructed and
        registered with the system. Intents will be registered and Skill
        settings will be available."""
        self.login()

    @intent_handler(IntentBuilder("AddToList").require("Add").require("AddSeperator").require("AddItem").require("ListNameAdd").build())
    def handle_add_list_intent(self, message):
        list_id = ""
        item_name = message.data.get('AddItem')
        list_name = message.data.get('ListNameAdd')
        if list_name == "the":
            list_name = message.utterance_remainder().split()[-1]

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
            found_item = self.get_item_from_list(list_id, item_name, list_name)
            if not found_item:
                self.handle_add_request(list_id, item_name, list_name)
            else:
                self.speak_dialog(item_name + " already exists in " + list_name)

    @intent_handler(
        IntentBuilder("FindItemInList").require("Find").require("FindSeperator").require("FindItem").require("ListNameFind").build())
    def handle_find_item_in_list_intent(self, message):
        list_id = ""
        item_name = message.data.get('FindItem')
        list_name = message.data.get('ListNameFind')
        if list_name == "the":
            list_name = message.utterance_remainder().split()[-1]

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
            found_item = self.get_item_from_list(list_id, item_name, list_name)
            if found_item:
                self.speak_dialog(item_name + " was found in " + list_name)
            else:
                self.speak_dialog(item_name + "does not exist in " + list_name)

    def stop(self):
        pass

    def handle_add_request(self, list_id, item, list_name, second_time=False):
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
                self.handle_add_request(list_id, item, list_name, True)
        elif r.status_code == 201:
            self.speak_dialog("I have added " + item + " to " + list_name)
        else:
            self.log.info(r.status_code)
            self.speak_dialog("Could not add " + item + " to " + list_name)

    def get_item_from_list(self, list_id, item, list_name, second_time=False):
        url = 'https://hl2api.listonic.com/api/lists/' + list_id + '/items'
        headers = {'Authorization': 'Bearer ' + self.access_token}
        r = requests.get(url, headers=headers)
        if r.status_code == 401:
            if second_time:
                return None
            else:
                self.login()
                return self.get_item_from_list(list_id, item, list_name, True)
        elif r.status_code == 200:
            last_version = r.headers.get("x-last-version")
            self.log.info(last_version)
            if last_version != self.cached_version:
                data = r.json()
                output_dict = [x for x in data if x['Deleted'] == 0]
                self.cached_list = output_dict
                self.cached_version = last_version
            self.log.info(self.cached_list)
            for json_item in self.cached_list:
                if json_item.get("name") == item:
                    return True
            return False
        else:
            self.log.info(r.status_code)
            return None

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
