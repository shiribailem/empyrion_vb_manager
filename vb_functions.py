import json
from json.decoder import JSONDecodeError
import os
import fnmatch
import traceback
from time import sleep


class Index_Handler:
    def __init__(self, filename):
        with open(filename, 'r') as file:
            raw_keys = json.loads(file.read())

        self.ids = {}
        self.keys = {}

        for key in raw_keys:
            self.ids[raw_keys[key]] = key
            self.keys[key] = {"id": raw_keys[key], "key": key}

    def import_localization(self, filename):
        with open(filename, 'r') as file:
            data = file.readlines()

        for line in data:
            line = line.split(',')
            if line[0] in self.keys.keys():
                self.keys[line[0]]['name'] = line[1].strip()

    def map_old(self, handler):
        for key in handler.keys.keys():
            if key in self.keys.keys():
                self.keys[key]['alt_id'] = handler.keys[key]["id"]

    def get_by_id(self, idcode):
        return self.keys[self.ids[idcode]]


class Item:
    def __init__(self, data, index):
        if isinstance(data, dict):
            self.data = data
            details = index.get_by_id(data['id'])
        elif isinstance(data, str):
            details = index.keys[data]
            self.data = {
                "id": details['id'],
                "name": None,
                "count": 1,
                "slotIdx": 0,
                "ammo": 0,
                "decay": 0
            }
        elif isinstance(data, int):
            details = index.get_by_id(data)
            self.data = {
                "id": data,
                "name": None,
                "count": 1,
                "slotIdx": 0,
                "ammo": 0,
                "decay": 0
            }
        else:
            raise

        self.key = details['key']

        if 'name' in details.keys():
            self.name = details['name']
        else:
            self.name = self.key

    def __repr__(self):
        return f"<Item({self.name}/{self.data['count']})>"


class Backpack:
    def __init__(self, data, index):
        self.slots = []
        for x in range(49):
            self.slots.append(None)
        if 'Items' in data.keys() and data['Items']:
            for raw_item in data['Items']:
                item = Item(raw_item, index)
                self.slots[item.data['slotIdx']] = item
        else:
            data['Items'] = []

    def place(self, item, slot):
        item.data['slotIdx'] = slot
        self.slots[slot] = item

    def remove(self, slot):
        self.slots[slot] = None

    def move(self, slot1, slot2):
        item = self.slots[slot1]
        self.place(item, slot2)

    def get_raw(self):
        data = []
        for item in self.slots:
            if item:
                data.append(item.data)

        return {"Items": data}

    def __repr__(self):
        output = []
        for item in self.slots:
            output.append(f"{item.__repr__()}")

        return f"<Backpack {','.join(output)}>"


class Master_Backpack:
    def __init__(self, filename, index, max_vbs=10):
        self.data = None
        self.player = None
        self.faction = None
        self.locked = False
        self.filename = filename
        self.index = index
        self.backpacks = []
        self.max_vbs = max_vbs
        self.refresh()

    def refresh(self, locks_only=False):
        with open(self.filename, 'r') as file:
            self.data = json.loads(file.read())

        if "Backpacks" not in self.data:
            print(f"Error loading: {self.filename}")
            raise

        self.player = self.data['LastAccessPlayerName']
        self.faction = self.data['LastAccessFactionName']

        if self.data["OpendByName"] or self.data["OpendBySteamId"]:
            self.locked = True
        else:
            self.locked = False

        if not locks_only:
            for backpack in self.data['Backpacks']:
                self.backpacks.append(Backpack(backpack, self.index))

            while len(self.backpacks) < self.max_vbs:
                self.backpacks.append(Backpack({}, self.index))

    def get_raw(self):
        self.data['Backpacks'] = []
        for backpack in self.backpacks:
            self.data['Backpacks'].append(backpack.get_raw())

    def write(self):
        with open(self.filename, 'w') as file:
            file.write(json.dumps(self.get_raw()))

    def safe_write(self, timeout=10):
        self.refresh(locks_only=True)
        while self.locked and timeout != 0:
            timeout -= 1
            sleep(1)
            self.refresh(locks_only=True)

        if self.locked:
            return False

        self.write()
        return True

    def acquire_lock(self, blocking=False, timeout=10):
        self.refresh(locks_only=True)

        while blocking and timeout != 0 and (self.locked and not self.data["OpendByName"] == "ADMIN"):
            self.refresh(locks_only=True)
            timeout -= 1
            if self.locked:
                sleep(1)

        if not self.locked or self.data["OpendByName"] == "ADMIN":
            self.lock()
            return True
        return False

    def lock(self):
        self.data["OpendByName"] = "ADMIN"
        self.data["OpendBySteamId"] = 1
        self.locked = True
        self.write()

    def unlock(self, release_only=True):
        if self.data["OpendByName"] == "ADMIN" or release_only:
            self.data["OpendByName"] = None
            self.data["OpendBySteamId"] = None
            self.locked = False
            self.write()


def find_json_files(directory, index, max_vbs):
    players = {}
    factions = {}
    origins = {}
    global_bp = None
    for root, dirs, files in os.walk(directory):
        for filename in fnmatch.filter(files, '*.json'):
            filename = os.path.join(root, filename)

            try:
                vb = Master_Backpack(filename, index, max_vbs)

                if "global.json" in filename.lower():
                    global_bp = vb
                elif "faction" in filename.lower():
                    if vb.faction:
                        factions[vb.faction] = vb
                    else:
                        factions[f"PRIVATE-{vb.player}"] = vb
                elif "origin" in filename.lower():
                    players["origin"] = vb
                else:
                    if vb.player:
                        players[vb.player] = vb
            except JSONDecodeError:
                pass
            except Exception:
                traceback.print_exc()

    return players, origins, factions, global_bp
