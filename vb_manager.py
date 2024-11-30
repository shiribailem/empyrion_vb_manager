import os
import json

from vb_functions import *


def menu(message, raw_options, lower=True):
    # clean options for easier matching
    options = []
    for option in raw_options:
        if option is not None:
            option = str(option)
            if lower:
                option = option.lower()
            options.append(option)

    buffer = ''
    while buffer not in options:
        buffer = input(message)

        buffer = buffer.strip()

        if lower:
            buffer = buffer.lower()

        if buffer in ['q', 'quit', 'exit']:
            return None

    if lower:
        for option in raw_options:
            if str(option).lower() == buffer:
                return option

    return buffer


item_index = Index_Handler("Data/NameIdMapping.json")

try:
    item_index.import_localization("Data/Localization.csv")
except FileNotFoundError:
    pass

try:
    with open("Data/Configuration.json", 'r') as file:
        data = json.loads(file.read())
        max_vbs = data['PersonalBackpack']["MaxBackpacks"]
except FileNotFoundError:
    max_vbs = 10

try:
    with open("Data/vbm_config.json", 'r') as file:
        config = json.loads(file.read())
except FileNotFoundError:
    config = {}

try:
    directory = config['vb_path']
except KeyError:
    directory = None

used_existing = False
if directory:
    print(f"Saved Virtual Backpack Directory: {directory}")

    if menu("Would you like to use existing path? (Y/N)", "yn") == 'n':
        directory = None
    else:
        used_existing = True

if not directory:
    directory = input("Please enter VB directory:")

if not used_existing and menu("Would you like to save this path? (Y/N)", "yn") == 'y':
    with open("Data/vbm_config.json", 'w') as file:
        config['vb_path'] = directory
        file.write(json.dumps(config))

players, origins, factions, global_bp = find_json_files(directory, item_index, max_vbs)

while True:
    option = menu(f"Select an action:\n"
                  f"\t1. Open an individual VB\n"
                  f"\t2. Open a faction VB\n"
                  f"\t3. Open origin VB\n"
                  f"\t4. Open global VB\n"
                  f"\t5. Search for an item by key\n"
                  f"\t6. List all players\n"
                  f"\t7. List all factions\n"
                  f"\t8. List all origins\n"
                  f"\tq. Quit Program\n\n"
                  f"> ", list(range(1, 9)))

    if not option:
        break
    elif option in (1, 2, 3, 4):
        backpacks = None
        locked = False
        if option == 1:
            handle = menu("Enter the player id you wish to open (case insensitive): ", players.keys())
            if handle:
                handle = players[handle]
                backpacks = handle.backpacks
        elif option == 2:
            handle = menu("Enter the faction id you wish to open (case insensitive): ", factions.keys())
            if handle:
                handle = factions[handle]
                backpacks = handle.backpacks
        elif option == 3:
            handle = menu("Enter the origin id you wish to open (case insensitive): ", origins.keys())
            if handle:
                handle = origins[handle]
                backpacks = handle.backpacks
        else:
            handle = global_bp
            backpacks = global_bp.backpacks

        if handle.locked:
            print("\nWARNING BACKPACK IS LOCKED! MAKE SURE PLAYER ISN'T USING IT!\n")

        if backpacks:
            print(f"{handle.player}'s backpacks:")

            count = 0
            for backpack in backpacks:
                print(f"\t{count}: {len(list(filter(lambda x: x, backpack.slots)))} items")
                count += 1

            print("\tr: Refresh Backpacks")

            option = menu("> ", [*range(max_vbs), 'r'])

            if option == 'r':
                handle.refresh()
                print(f"Refreshed Backpack. Backpack is Locked:{handle.locked}.")
                option = None

            while option is not None:
                backpack = backpacks[int(option)]

                while option is not None:
                    count = 0
                    for item in backpack.slots:
                        if item:
                            print(f"{count}: {item.data['count']} x {item.name}")
                        else:
                            print(f"{count}: Empty")
                        count += 1

                    option = menu("\nSelect an action:\n"
                                  "\t1: Add/replace Item\n"
                                  "\t2: Remove Item\n"
                                  "\t3: Change Quantity\n"
                                  "\t4: Reset Decay\n"
                                  "\tr: Refresh Backpack\n"
                                  "\tq: Go back to previous menu\n\n"
                                  "> ", [1, 2, 3, 4, 'r'])

                    if option == 'r':
                        handle.refresh()
                        print(f"Refreshed Backpack. Backpack is Locked:{handle.locked}.")
                    elif option:
                        slot = menu("Enter the slot number to update: ", list(range(0, 49)))

                        if slot is not None:
                            slot = int(slot)
                            if option == 1:
                                item_key = menu("Enter the item key you wish to add/replace: ",
                                                item_index.keys.keys())
                                if item_key:
                                    quantity = menu("Enter the quantity: ", range(1, 50000))
                                    if quantity:
                                        item = Item(item_key, item_index)
                                        item.data['count'] = quantity
                                        backpack.place(item, slot)
                                        print(f"Added {quantity} of {item_key}")

                            elif option == 2:
                                item = backpack.slots[slot]
                                if item:
                                    print(f"Removed {item.name}")
                                    backpack.remove(slot)
                                else:
                                    print("Slot already empty")

                            elif option == 3:
                                quantity = menu("Enter the new quantity: ", range(1, 50000))
                                if quantity:
                                    backpack.slots[slot].data['count'] = int(quantity)

                            elif option == 4:
                                item = backpack.slots[slot]
                                if item:
                                    item.data['decay'] = 0
                                    print(f"Reset decay on {item.name}")
                                else:
                                    print("No item in slot.")
    elif option in [6, 7, 8]:
        handle = [players, factions, origins][option-6]

        if option == 6:
            print("All players:")
        elif option == 7:
            print("All Factions:")
        elif option == 8:
            print("All Origins:")
            print("--- ORIGIN SEARCH NOT IMPLEMENTED ---")

        for item in sorted(handle.keys()):
            if option == 6:
                print(item)
            elif option == 7:
                print(item)
