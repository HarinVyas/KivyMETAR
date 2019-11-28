"""
VERSION 1.0.0 ChiChi
"""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.properties import ObjectProperty
from kivy.network.urlrequest import UrlRequest
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty
from kivy.properties import NumericProperty
import json
import hashlib
import os
from kivy.clock import *
from kivy.core.window import Window
from kivy.uix.textinput import TextInput
import ast
from kivy.uix.label import Label
from mapview import MapView
from mapview import *

class WeatherRoot(ScreenManager, BoxLayout):
    pass


class RegisterPage(BoxLayout, Screen):
    username_input = ObjectProperty()
    password_input = ObjectProperty()
    email_input = ObjectProperty()
    validation = ObjectProperty()

    def register_validation(self):
        f = open("Data/data.json", "r")
        data = json.load(f)
        err = False
        idLst = []
        f.close()
        for users in data['users']:
            idLst.append(users)
        print(idLst)
        if (not self.username_input.text) or (not self.password_input.text) or (not self.email_input.text):
            self.validation.text = "Form not completed"
            err = True
        for id in idLst:
            if (self.username_input.text == data['users'][id]['username']) or (self.email_input.text == data['users'][id]['email']):
                self.validation.text = "Username or Email is taken"
                err = True
        if err == False:
            self.register(idLst, data)

    def register(self, idLst, data):
        id = str(int(idLst[-1]) + 1)
        salt = "yousaltybro"
        passHash = hashlib.md5((salt + self.password_input.text).encode("utf-8")).hexdigest()
        data['users'][id] = {"username": self.username_input.text, "password_hash": passHash,
                             "email": self.email_input.text, "recent_searches_METAR": [], "recent_searches_ICAO": []}
        with open("Data/temp.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        f.close()
        os.remove("Data/data.json")
        os.rename("Data/temp.json", "Data/data.json")
        self.validation.text = "Registration Complete"
        self.password_input.text = ""
        self.email_input.text = ""
        self.username_input.text = ""


class LoginPage(BoxLayout, Screen):
    usr_info = StringProperty('')
    username_input = ObjectProperty()
    password_input = ObjectProperty()
    validation = ObjectProperty()

    def validate(self):
        f = open("Data/data.json", "r", encoding="utf-8")
        data = json.load(f)
        idLst, usrlst = [], []
        for id in data['users']:
            idLst.append(id)
            usrlst.append(data['users'][id]['username'])
        if (self.username_input.text == "") or (self.password_input.text == ""):
            self.validation.text = "Form not completed"
        elif (self.username_input.text not in usrlst):
            self.validation.text = "User doesn't exist"
        else:
            self.login(usrlst, idLst, data)

    def login(self, usrLst, idLst, data):
        users = dict(zip(usrLst, idLst))
        usrinfo = data['users'][users[self.username_input.text]]
        self.usr_info = str(usrinfo)
        salt = "yousaltybro"
        passHash = hashlib.md5((salt + self.password_input.text).encode("utf-8")).hexdigest()
        if usrinfo['password_hash'] == passHash:
            self.manager.current = 'AddLocation'
        else:
            self.validation.text = "Password is wrong"


class AddLocationForm(BoxLayout, Screen):
    search_input = ObjectProperty()
    search_results = ObjectProperty()
    recent_search_one = ObjectProperty()
    recent_search_two = ObjectProperty()
    recent_search_three = ObjectProperty()
    usr_details = ObjectProperty()

    airport_info = ObjectProperty()
    raw = ObjectProperty()
    time = ObjectProperty()
    temp = ObjectProperty()
    dew = ObjectProperty()
    wind = ObjectProperty()
    alt = ObjectProperty()
    cloud = ObjectProperty()
    other = ObjectProperty()
    runway_data = ObjectProperty()

    map = ObjectProperty()

    token = "3ddws52jkyV_1PWKhIRFKFL0RUI4IMfFIDoO_L-wOgg"

    def search_location(self):
        search_template = "https://avwx.rest/api/metar/{}?options=summary&format=json&onfail=cache&token={}"
        search_url = search_template.format(self.search_input.text, self.token)
        request = UrlRequest(url=search_url, on_success=self.found_location, on_error=print, on_failure=print)
    
    def get_info(self, ICAO):
        search_template = "https://avwx.rest/api/station/{}?options=format=json&onfail=cache&token={}"
        search_url = search_template.format(self.search_input.text, self.token)
        request = UrlRequest(url=search_url, on_success=self.update_info, on_error=print, on_failure=print)
        
        
    def found_location(self, request, data):
        print("jsdfhk")
        data = json.loads(data.decode()) if not isinstance(data, dict) else data
        toAdd = []

        self.raw.text = data['raw']
        summary = data['summary'].split(',')
        print(summary)
        for i in summary:
            toAdd.append(i)
        self.search_results.item_strings = toAdd
        self.wind.text = summary[0]
        self.other.text = summary[1].replace('Vis', 'Visibility -')
        self.temp.text, self.dew.text = summary[2].replace('Temp', 'Temperature -'), summary[3].replace('Dew', 'Dew Point - ')
        self.alt.text, self.cloud.text = summary[4].replace('Alt', 'Altimeter'), summary[5]


        self.recent_search_three.text = self.recent_search_two.text
        self.recent_search_two.text = self.recent_search_one.text
        self.recent_search_one.text = self.search_input.text
        usrdata = ast.literal_eval(self.usr_details)
        usrdata["recent_searches_METAR"] = [self.recent_search_one.text, self.recent_search_two.text,
                                            self.recent_search_three.text]
        self.usr_details = str(usrdata)
        print(self.usr_details)
        if self.get_info(self.search_input.text) == True:
            update_JSON(usrdata['recent_searches_METAR'], 'recent_searches_METAR', usrdata['username'])
        
    def update_info(self, request, data):
        data = json.loads(data.decode()) if not isinstance(data, dict) else data
        
        name = '{}, {} ({})'.format(data['name'], data['country'], data['icao'])
        
        self.map.center_on(float(data['latitude']), float(data['longitude']))
        #marker = MapMarker(float(data['longitude']), float(data['latitude']))
        #self.map.add_marker(marker)
        toAdd = []
        counter = 1
        for runway in data['runways']:
            d = "{}) {}/{}, Length = {}ft, Width = {}ft".format(counter, runway['ident1'], runway['ident2']
                                                            , runway['length_ft'], runway['width_ft'])
            toAdd.append(d)
        self.runway_data.item_strings = toAdd
        return True
        
    def fill(self):
        rs = (ast.literal_eval(self.usr_details))["recent_searches_METAR"]
        self.recent_search_one.text, self.recent_search_two.text, self.recent_search_three.text = rs[0], rs[1], rs[2]


class ICAOFinder(BoxLayout, Screen):
    search_input = ObjectProperty()
    search_results = ObjectProperty()

    def findICAO(self):
        f = open("Data/airports.csv", encoding="utf-8")
        data = []
        for line in f:
            data_line = line.rstrip().split('\n')
            data_list = data_line[0].split(',')
            data.append(data_list)
        ICAOList = ["Search results are: "]
        counter = 0
        for lst in data:
            if self.search_input.text in lst[1]:
                counter += 1
                ICAOList.append("{} ICAO is {}".format(lst[1], lst[0]))
        ICAOList.insert(0, "Total number of results: {}".format(counter))
        self.search_results.item_strings = ICAOList


class WeatherApp(App):
    pass


def update_JSON(update_data, location, user):
    f = open("Data/data.json", "r", encoding="utf-8")
    data = json.load(f)
    idLst = []
    f.close()
    for users in data['users']:
        idLst.append(users)

    for id in idLst:
        if data['users'][id]["username"] == user:
            data['users'][id][location] = update_data
            pass

    with open("Data/temp.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    f.close()
    os.remove("Data/data.json")
    os.rename("Data/temp.json", "Data/data.json")



def iii(time):
    print("h")
    x = 1
    """
    if x == 1:
        Window.clearcolor = (1, 1, 1, 1)
        root = App.get_running_app().root  # WeatherRoot instance
        for i in range(0, 4):
            screen = root.screens[i]  # RegisterPage instance
            box_layout = screen.children[0]  # BoxLayout instance
            for child in box_layout.children:  # children of box_layout
                if isinstance(child, TextInput):  # verify that the child is a TextInput
                    child.background_color = (0, 0, 0, 1)
                    child.foreground_color = (1, 1, 1, 1)
                elif isinstance(child, Label):
                    child.color = (0,0,0,1)
            try:
                box_layout = screen.children[1]  # BoxLayout instance
                for child in box_layout.children:  # children of box_layout
                    if isinstance(child, TextInput):  # verify that the child is a TextInput
                        child.background_color = (0, 0, 0, 1)
                        child.foreground_color = (1, 1, 1, 1)
                    elif isinstance(child, Label):
                        child.color = (0, 0, 0, 1)
            except:
                pass
    """
    pass

class Map(MapView):
    def build(self):
        mapview = MapView(zoom=AddLocationForm.zoom, lat=AddLocationForm.lat, lon=AddLocationForm.long)
        return mapview

if __name__ == "__main__":
    Clock.schedule_once(iii)
    WeatherApp().run()
