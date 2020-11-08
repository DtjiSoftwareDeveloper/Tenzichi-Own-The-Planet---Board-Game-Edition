"""
This file contains source code of the game "Tenzichi Own The Planet - Board Game Edition".
Author: DtjiSoftwareDeveloper
"""


# Game version: 1


# Importing necessary libraries

import sys
import uuid
import pickle
import copy
import random
from mpmath import *

mp.pretty = True


# Creating static functions to be used throughout the game.


def is_number(string: str) -> bool:
    try:
        mpf(string)
        return True
    except ValueError:
        return False


def mpf_sum_of_list(a_list: list) -> mpf:
    return mpf(str(sum(mpf(str(elem)) for elem in a_list if is_number(str(elem)))))


def mpf_product_of_list(a_list: list) -> mpf:
    product: mpf = mpf("1")  # initial value
    for item in a_list:
        if is_number(item):
            product *= mpf(item)

    return product


def load_game_data(file_name):
    # type: (str) -> Game
    return pickle.load(open(file_name, "rb"))


def save_game_data(game_data, file_name):
    # type: (Game, str) -> None
    pickle.dump(game_data, open(file_name, "wb"))


# Creating necessary classes


class Upgrade:
    """
    This class contains attributes of upgrades in this game.
    """

    def __init__(self, name, coin_cost, coin_gain_multiplier, exp_gain_multiplier):
        # type: (str, mpf, int, int) -> None
        self.name: str = name
        self.coin_cost: mpf = coin_cost
        self.coin_gain_multiplier: int = coin_gain_multiplier
        self.exp_gain_multiplier: int = exp_gain_multiplier

    def __str__(self):
        # type: () -> str
        res: str = ""  # initial value
        res += "Name: " + str(self.name) + "\n"
        res += "Coin cost: " + str(self.coin_cost) + "\n"
        res += "Coin gain multiplier: " + str(self.coin_gain_multiplier) + "\n"
        res += "EXP gain multiplier: " + str(self.exp_gain_multiplier) + "\n"
        return res

    def clone(self):
        # type: () -> Upgrade
        return copy.deepcopy(self)


class Player:
    """
    This class contains attributes of the player in this game.
    """

    def __init__(self, name):
        # type: (str) -> None
        self.player_id: str = str(uuid.uuid1())  # randomly generate player ID
        self.name: str = name
        self.level: int = 1
        self.exp: mpf = mpf("0")
        self.required_exp: mpf = mpf("1e6")
        self.coins: mpf = mpf("0")
        self.position: int = 0
        self.__owned_list: list = []  # initial value
        self.__upgrade_list: list = []  # initial value

    def __str__(self):
        # type: () -> str
        res: str = ""  # initial value
        res += "Player ID: " + str(self.player_id) + "\n"
        res += "Name: " + str(self.name) + "\n"
        res += "Level: " + str(self.level) + "\n"
        res += "EXP: " + str(self.exp) + "\n"
        res += "Required EXP: " + str(self.required_exp) + "\n"
        res += "Coins: " + str(self.coins) + "\n"
        res += "Position: " + str(self.position) + "\n"
        res += "Below is a list of places owned by this player:\n"
        for place in self.__owned_list:
            res += str(place) + "\n"

        res += "Below is a list of upgrades owned by this player:\n"
        for upgrade in self.__upgrade_list:
            res += str(upgrade) + "\n"

        return res

    def get_coins_per_turn(self):
        # type: () -> mpf
        return mpf_sum_of_list([place.coins_per_turn for place in self.__owned_list]) * \
               mpf_product_of_list([upgrade.coin_gain_multiplier for upgrade in self.__upgrade_list])

    def get_exp_per_turn(self):
        # type: () -> mpf
        return mpf_sum_of_list([place.exp_per_turn for place in self.__owned_list]) * \
               mpf_product_of_list([upgrade.exp_gain_multiplier for upgrade in self.__upgrade_list])

    def level_up(self):
        # type: () -> None
        while self.exp >= self.required_exp:
            self.level += 1
            self.required_exp *= mpf("10") ** self.level

    def roll_dice(self, dice, game):
        # type: (Dice, Game) -> None
        self.position += dice.value
        if self.position >= len(game.board.get_tiles()):
            self.position -= len(game.board.get_tiles())
            self.coins += game.start_coin_bonus

    def buy_upgrade(self, upgrade):
        # type: (Upgrade) -> bool
        if self.coins >= upgrade.coin_cost:
            self.coins -= upgrade.coin_cost
            self.__upgrade_list.append(upgrade)
            return True
        return False

    def purchase_place(self, place):
        # type: (Place) -> bool
        if self.coins >= place.coin_cost and place not in self.__owned_list:
            self.coins -= place.coin_cost
            place.coin_cost *= mpf("10") ** self.level
            self.__owned_list.append(place)
            return True
        return False

    def upgrade_place(self, place):
        # type: (Place) -> bool
        if self.coins >= place.coin_cost and place in self.__owned_list:
            self.coins -= place.coin_cost
            self.level += 1
            place.coin_cost *= mpf("10") ** self.level
            place.coins_per_turn *= mpf("10") ** self.level
            place.exp_per_turn *= mpf("10") ** self.level
            return True
        return False

    def acquire_place(self, place, other):
        # type: (Place, Player) -> bool
        if self.coins >= place.coin_cost and place in other.get_owned_list() and place not in self.__owned_list:
            self.coins -= place.coin_cost
            self.level += 1
            place.coin_cost *= mpf("10") ** self.level
            place.coins_per_turn *= mpf("10") ** self.level
            place.exp_per_turn *= mpf("10") ** self.level
            self.__owned_list.append(place)
            other.get_owned_list().remove(place)
            return True
        return False

    def get_owned_list(self):
        # type: () -> list
        return self.__owned_list

    def get_upgrade_list(self):
        # type: () -> list
        return self.__upgrade_list

    def clone(self):
        # type: () -> Player
        return copy.deepcopy(self)


class CPU(Player):
    """
    This class contains attributes of player's CPU controlled
    """

    def __init__(self):
        # type: () -> None
        Player.__init__(self, "CPU PLAYER")


class Board:
    """
    This class contains attributes of the board.
    """

    def __init__(self, tiles):
        # type: (list) -> None
        self.__tiles: list = tiles

    def __str__(self):
        # type: () -> str
        res: str = "Below is a list of tiles on the board:\n"
        for tile in self.__tiles:
            res += str(tile) + "\n"

        return res

    def get_tiles(self):
        # type: () -> list
        return self.__tiles

    def clone(self):
        # type: () -> Board
        return copy.deepcopy(self)


class Tile:
    """
    This class contains attributes of a tile on the board.
    """

    def __init__(self):
        # type: () -> None
        self.name: str = ""  # initial value
        self.description: str = ""  # initial value

    def __str__(self):
        # type: () -> str
        res: str = ""  # initial value
        res += "Name: " + str(self.name) + "\n"
        res += "Description: " + str(self.description) + "\n"
        return res

    def clone(self):
        # type: () -> Tile
        return copy.deepcopy(self)


class Place(Tile):
    """
    This class contains attributes of a place which the player and CPU can purchase.
    """

    def __init__(self, name, description, coin_cost, coins_per_turn, exp_per_turn):
        # type: (str, str, mpf, mpf, mpf) -> None
        Tile.__init__(self)
        self.name = name.upper()
        self.level: int = 1  # initial value
        self.description = description
        self.coin_cost: mpf = coin_cost
        self.coins_per_turn: mpf = coins_per_turn
        self.exp_per_turn: mpf = exp_per_turn

    def __str__(self):
        # type: () -> str
        res: str = Tile.__str__(self)
        res += "Level: " + str(self.level) + "\n"
        res += "Coin cost: " + str(self.coin_cost) + "\n"
        res += "Coins per turn: " + str(self.coins_per_turn) + "\n"
        res += "EXP per turn: " + str(self.exp_per_turn) + "\n"
        return res


class StartTile(Tile):
    """
    This class contains attributes of the start tile where the player and CPU gains bonus for landing at or passing it.
    """

    def __init__(self):
        # type: () -> None
        Tile.__init__(self)
        self.name = "START"
        self.description: str = "A tile where the player and CPU gains bonus for passing it."


class EmptySpace(Tile):
    """
    This class contains attributes of empty spaces on the board.
    """

    def __init__(self):
        # type: () -> None
        Tile.__init__(self)
        self.name = "EMPTY SPACE"
        self.description = "An empty space."


class ShinyZone(Tile):
    """
    This class contains attributes of shiny zones on the board where the player and CPU can gain random rewards.
    """

    def __init__(self):
        # type: () -> None
        Tile.__init__(self)
        self.name = "SHINY ZONE"
        self.description = "A tile where the player and CPU can gain random rewards."

    def generate_shiny(self):
        # type: () -> Shiny
        return Shiny()


class UpgradeShop(Tile):
    """
    This class contains attributes of an upgrade shop for the player and CPU to buy upgrades.
    """

    def __init__(self, upgrades_sold):
        # type: (list) -> None
        Tile.__init__(self)
        self.name = "UPGRADE SHOP"
        self.description = "A shop selling upgrades."
        self.__upgrades_sold: list = upgrades_sold

    def __str__(self):
        # type: () -> str
        res: str = Tile.__str__(self)
        res += "Below is a list of upgrades sold on this tile:\n"
        for upgrade_sold in self.__upgrades_sold:
            res += str(upgrade_sold) + "\n"

        return res

    def get_upgrades_sold(self):
        # type: () -> list
        return self.__upgrades_sold


class Shiny:
    """
    This class contains attributes of shinies which the player and CPU can gain when landing on shiny zones.
    """

    def __init__(self):
        # type: () -> None
        self.coin_reward: mpf = mpf("10") ** random.randint(10, 100000)
        self.exp_reward: mpf = mpf("10") ** random.randint(10, 100000)

    def __str__(self):
        # type: () -> str
        res: str = ""  # initial value
        res += "Coin reward: " + str(self.coin_reward) + "\n"
        res += "EXP reward: " + str(self.exp_reward) + "\n"
        return res

    def clone(self):
        # type: () -> Shiny
        return copy.deepcopy(self)


class Dice:
    """
    This class contains attributes of the dice to be rolled.
    """

    def __init__(self):
        # type: () -> None
        self.value: int = random.randint(1, 20)

    def __str__(self):
        # type: () -> str
        return str(self.value)

    def clone(self):
        # type: () -> Dice
        return copy.deepcopy(self)


class Game:
    """
    This class contains attributes of saved game data in this game.
    """

    def __init__(self, player, cpu, board):
        # type: (Player, CPU, Board) -> None
        self.game_level: int = 1
        self.turn: int = 0  # initial value
        self.player: Player = player
        self.cpu: CPU = cpu
        self.board: Board = board
        self.start_coin_bonus: mpf = mpf("1e4")

    def __str__(self):
        # type: () -> str
        res: str = ""  # initial value
        res += "Game level: " + str(self.game_level) + "\n"
        res += "Turn: " + str(self.turn) + "\n"
        res += "Player in this game:\n" + str(self.player) + "\n"
        res += "CPU controlled opponent in this game:\n" + str(self.cpu) + "\n"
        res += "Board representation:\n" + str(self.board) + "\n"
        res += "Start coin bonus: " + str(self.start_coin_bonus) + "\n"
        return res

    def update_game_level(self):
        # type: () -> None
        self.game_level = min(1 + self.player.level // 10, 1 + self.cpu.level // 10)
        self.start_coin_bonus = mpf("1e4") ** self.game_level

    def clone(self):
        # type: () -> Game
        return copy.deepcopy(self)


# Creating main method of the game.


def main():
    # type: () -> None
    """
    This main method is used to run the game.
    :return: None
    """

    print("Welcome to 'Tenzichi Own The Planet - Board Game Edition' by 'DtjiSoftwareDeveloper'.")
    print("This game is a board game where the player needs to own the planet by purchasing and upgrading places.")

    upgrades_sold: list = [
        Upgrade("COIN UPGRADE #1", mpf("1e10"), 10, 1),
        Upgrade("COIN UPGRADE #2", mpf("1e40"), 20, 1),
        Upgrade("COIN UPGRADE #3", mpf("1e160"), 30, 1),
        Upgrade("COIN UPGRADE #4", mpf("1e640"), 40, 1),
        Upgrade("COIN UPGRADE #5", mpf("1e2560"), 50, 1),
        Upgrade("COIN UPGRADE #6", mpf("1e10240"), 60, 1),
        Upgrade("COIN UPGRADE #7", mpf("1e40960"), 70, 1),
        Upgrade("COIN UPGRADE #8", mpf("1e163840"), 80, 1),
        Upgrade("EXP UPGRADE #1", mpf("1e10"), 1, 10),
        Upgrade("EXP UPGRADE #2", mpf("1e40"), 1, 20),
        Upgrade("EXP UPGRADE #3", mpf("1e160"), 1, 30),
        Upgrade("EXP UPGRADE #4", mpf("1e640"), 1, 40),
        Upgrade("EXP UPGRADE #5", mpf("1e2560"), 1, 50),
        Upgrade("EXP UPGRADE #6", mpf("1e10240"), 1, 60),
        Upgrade("EXP UPGRADE #7", mpf("1e40960"), 1, 70),
        Upgrade("EXP UPGRADE #8", mpf("1e163840"), 1, 80)
    ]

    board: Board = Board([
        StartTile(),
        Place("Naivagadi Wild", "A jungle.", mpf("1e5"), mpf("1e4"), mpf("1e3")),
        EmptySpace(),
        EmptySpace(),
        EmptySpace(),
        UpgradeShop(upgrades_sold),
        EmptySpace(),
        EmptySpace(),
        ShinyZone(),
        EmptySpace(),
        EmptySpace(),
        ShinyZone(),
        EmptySpace(),
        EmptySpace(),
        Place("Cardley Strand", "A beach.", mpf("1e10"), mpf("1e8"), mpf("1e6")),
        Place("Sanctuary Of Serenity", "A temple.", mpf("1e16"), mpf("1e13"), mpf("1e10")),
        EmptySpace(),
        Place("Berthierpon Park", "A park.", mpf("1e23"), mpf("1e19"), mpf("1e15")),
        EmptySpace(),
        EmptySpace(),
        ShinyZone(),
        EmptySpace(),
        EmptySpace(),
        ShinyZone(),
        EmptySpace(),
        UpgradeShop(upgrades_sold),
        EmptySpace(),
        Place("Danpawa Shallows", "A lake.", mpf("1e31"), mpf("1e26"), mpf("1e21")),
        Place("Venroy Tops", "A mountain.", mpf("1e40"), mpf("1e34"), mpf("1e28")),
        EmptySpace(),
        EmptySpace(),
        EmptySpace(),
        Place("The Sunken Tunnels", "A dungeon.", mpf("1e50"), mpf("1e43"), mpf("1e36")),
        EmptySpace(),
        ShinyZone(),
        EmptySpace(),
        EmptySpace(),
        Place("The Dragon Shore", "A beach.", mpf("1e61"), mpf("1e53"), mpf("1e45")),
        EmptySpace(),
        EmptySpace(),
        ShinyZone(),
        UpgradeShop(upgrades_sold),
        EmptySpace(),
        EmptySpace(),
        Place("Monastery Of Muvdall", "A temple.", mpf("1e73"), mpf("1e64"), mpf("1e55")),
        EmptySpace(),
        EmptySpace(),
        Place("Venneau Hideout", "A cave.", mpf("1e86"), mpf("1e76"), mpf("1e66")),
        Place("Salbridge River", "A river.", mpf("1e100"), mpf("1e89"), mpf("1e78")),
        EmptySpace(),
        Place("Stancier Meadows", "A park.", mpf("1e115"), mpf("1e103"), mpf("1e91")),
        EmptySpace(),
        EmptySpace(),
        ShinyZone(),
        EmptySpace(),
        Place("The Ellisgonie Tundra", "A snowland.", mpf("1e131"), mpf("1e118"), mpf("1e105")),
        ShinyZone(),
        EmptySpace(),
        EmptySpace(),
        EmptySpace(),
        UpgradeShop(upgrades_sold),
        EmptySpace(),
        ShinyZone(),
        Place("The Grounds Of Hermibriand", "A park.", mpf("1e148"), mpf("1e134"), mpf("1e120")),
        EmptySpace(),
        EmptySpace(),
        Place("Riverfront Plaza", "A park.", mpf("1e166"), mpf("1e151"), mpf("1e136")),
        EmptySpace(),
        ShinyZone(),
        EmptySpace(),
        Place("The Tranquil Tombs", "A dungeon.", mpf("1e185"), mpf("1e169"), mpf("1e153")),
        EmptySpace(),
        UpgradeShop(upgrades_sold),
        EmptySpace(),
        Place("The Grave Deep", "A sea.", mpf("1e205"), mpf("1e188"), mpf("1e171")),
        EmptySpace(),
        EmptySpace(),
        ShinyZone(),
        EmptySpace(),
        EmptySpace(),
        Place("Yorkdiac Point", "A beach.", mpf("1e226"), mpf("1e208"), mpf("1e190")),
        EmptySpace(),
        EmptySpace(),
        Place("The Dark Desert", "A desert.", mpf("1e248"), mpf("1e229"), mpf("1e210")),
        EmptySpace(),
        EmptySpace(),
        ShinyZone(),
        EmptySpace(),
        EmptySpace(),
        Place("Celestial Library", "A library.", mpf("1e271"), mpf("1e251"), mpf("1e231")),
        UpgradeShop(upgrades_sold),
        EmptySpace(),
        EmptySpace(),
        EmptySpace(),
        Place("Aptitude Bibliotheca", "A library.", mpf("1e295"), mpf("1e274"), mpf("1e253")),
        EmptySpace(),
        ShinyZone(),
        EmptySpace(),
        Place("The Windless Wilderness", "A jungle.", mpf("1e320"), mpf("1e298"), mpf("1e276")),
        EmptySpace(),
        EmptySpace(),
        EmptySpace(),
        EmptySpace(),
        EmptySpace(),
        Place("The Wild of Megeisa", "A jungle.", mpf("1e346"), mpf("1e323"), mpf("1e300")),
        ShinyZone(),
        EmptySpace(),
        EmptySpace(),
        UpgradeShop(upgrades_sold),
        Place("The Windy Burrows", "A dungeon.", mpf("1e373"), mpf("1e349"), mpf("1e325")),
        EmptySpace(),
        UpgradeShop(upgrades_sold),
        EmptySpace(),
        Place("Royal Isle Plaza", "A park.", mpf("1e401"), mpf("1e376"), mpf("1e351")),
        EmptySpace(),
        EmptySpace(),
        ShinyZone(),
        EmptySpace(),
        EmptySpace(),
        Place("Pleasant View Grounds", "A park.", mpf("1e430"), mpf("1e404"), mpf("1e378")),
        Place("The Shimmering Coast", "A beach.", mpf("1e460"), mpf("1e433"), mpf("1e406")),
        EmptySpace(),
        EmptySpace(),
        UpgradeShop(upgrades_sold),
        EmptySpace(),
        Place("Durnola Shore", "A beach.", mpf("1e491"), mpf("1e463"), mpf("1e435")),
        EmptySpace(),
        ShinyZone(),
        EmptySpace(),
        Place("Merimer Strand", "A beach.", mpf("1e523"), mpf("1e494"), mpf("1e465")),
        EmptySpace(),
        EmptySpace(),
        EmptySpace(),
        ShinyZone(),
        Place("Richronto Key", "An island.", mpf("1e556"), mpf("1e526"), mpf("1e496")),
        EmptySpace(),
        EmptySpace(),
        EmptySpace(),
        EmptySpace(),
        EmptySpace(),
        Place("Meribrook Ait", "An island.", mpf("1e590"), mpf("1e559"), mpf("1e528")),
        Place("Grettrie Rise", "A mountain.", mpf("1e625"), mpf("1e593"), mpf("1e561")),
        ShinyZone(),
        Place("Scarscour Volcano", "A volcano.", mpf("1e661"), mpf("1e628"), mpf("1e595")),
        EmptySpace(),
        EmptySpace(),
        Place("Plasack Hill", "A hill.", mpf("1e698"), mpf("1e664"), mpf("1e630")),
        UpgradeShop(upgrades_sold),
        Place("Kerrokasing Deep", "A sea.", mpf("1e736"), mpf("1e701"), mpf("1e666")),
        EmptySpace(),
        EmptySpace(),
        EmptySpace(),
        Place("Troutriver Mansion", "A mansion.", mpf("1e775"), mpf("1e739"), mpf("1e703")),
        Place("Fullernelly Residence", "A mansion.", mpf("1e815"), mpf("1e778"), mpf("1e741"))
    ])

    # Automatically load saved game data
    file_name: str = "SAVED TENZICHI OWN THE PLANET - BOARD GAME EDITION GAME PROGRESS"
    new_game: Game
    try:
        new_game = load_game_data(file_name)
        print("Current game progress:\n", str(new_game))
    except FileNotFoundError:
        name: str = input("Please enter your name: ")
        player: Player = Player(name)
        new_game = Game(player, CPU(), board)

    print("Enter 'Y' for yes.")
    print("Enter anything else for no.")
    continue_playing: str = input("Do you want to continue playing 'Tenzichi Own The Planet - Board Game Edition'? ")
    while continue_playing == "Y":
        # Printing your stats and your opponent's stats
        print("Your current stats:\n" + str(new_game.player))
        print("\n")
        print("Your opponent's stats:\n" + str(new_game.cpu))
        new_game.turn += 1
        # Checking whether it is player's turn or CPU's turn
        if new_game.turn % 2 == 1:
            # It is player's turn
            print("It is your turn.")
            print("Enter 'Y' for yes.")
            print("Enter anything else for no.")
            roll_dice: str = input("Do you want to roll the dice? ")
            if roll_dice == "Y":
                new_game.player.roll_dice(Dice(), new_game)
                print("You are now at:\n" + str(new_game.board.get_tiles()[new_game.player.position]))

                # Checking what type of tile the player lands on
                if isinstance(new_game.board.get_tiles()[new_game.player.position], EmptySpace):
                    pass  # do nothing
                elif isinstance(new_game.board.get_tiles()[new_game.player.position], StartTile):
                    pass  # do nothing
                elif isinstance(new_game.board.get_tiles()[new_game.player.position], ShinyZone):
                    # Randomly generate a shiny
                    shiny_zone: ShinyZone = new_game.board.get_tiles()[new_game.player.position]
                    shiny: Shiny = shiny_zone.generate_shiny()
                    print("You earn " + str(shiny.coin_reward) + " coins and " + str(shiny.exp_reward) + " EXP.")
                    new_game.player.coins += shiny.coin_reward
                    new_game.player.exp += shiny.exp_reward
                    new_game.player.level_up()
                elif isinstance(new_game.board.get_tiles()[new_game.player.position], UpgradeShop):
                    # Ask the player whether he/she wants to buy an upgrade or not
                    print("Enter 'Y' for yes.")
                    print("Enter anything else for no.")
                    buy_upgrade: str = input("Do you want to buy an upgrade? ")
                    if buy_upgrade == "Y":
                        upgrade_shop: UpgradeShop = new_game.board.get_tiles()[new_game.player.position]
                        print("Below is a list of upgrades sold:\n")
                        for upgrade in upgrade_shop.get_upgrades_sold():
                            print(str(upgrade) + "\n")

                        upgrade_index: int = int(input("Please enter index of upgrade you want to buy: "))
                        while upgrade_index < 0 or upgrade_index >= len(upgrade_shop.get_upgrades_sold()):
                            upgrade_index = int(input("Sorry, invalid input! "
                                                      "Please enter index of upgrade you want to buy: "))

                        to_buy: Upgrade = upgrade_shop.get_upgrades_sold()[upgrade_index]
                        if new_game.player.buy_upgrade(to_buy):
                            print("Congratulations! You have successfully bought " + str(to_buy.name))
                        else:
                            print("Sorry, insufficient coins!")
                    else:
                        pass  # Do nothing
                elif isinstance(new_game.board.get_tiles()[new_game.player.position], Place):
                    place: Place = new_game.board.get_tiles()[new_game.player.position]

                    # Checking whether the place has an owner or not
                    # 1. If the place does not have an owner
                    if place not in new_game.player.get_owned_list() and place not in new_game.cpu.get_owned_list():
                        # Ask whether the player wants to buy the place or not
                        print("Enter 'Y' for yes.")
                        print("Enter anything else for no.")
                        buy_place: str = input("Do you want to buy this place? ")
                        if buy_place == "Y":
                            if new_game.player.purchase_place(place):
                                print("Congratulations! You have successfully bought " + str(place.name))
                            else:
                                print("Sorry, insufficient coins!")
                        else:
                            pass  # do nothing
                    # 2. If the place is owned by the player
                    elif place in new_game.player.get_owned_list():
                        # Ask whether the player wants to upgrade the place or not
                        print("Enter 'Y' for yes.")
                        print("Enter anything else for no.")
                        upgrade_place: str = input("Do you want to upgrade this place? ")
                        if upgrade_place == "Y":
                            if new_game.player.upgrade_place(place):
                                print("Congratulations! You have successfully upgraded " + str(place.name))
                            else:
                                print("Sorry, insufficient coins!")
                        else:
                            pass  # do nothing
                    # 3. If the place is owned by the CPU
                    elif place in new_game.cpu.get_owned_list():
                        # Ask whether the player wants to acquire the place or not
                        print("Enter 'Y' for yes.")
                        print("Enter anything else for no.")
                        acquire_place: str = input("Do you want to acquire this place? ")
                        if acquire_place == "Y":
                            if new_game.player.acquire_place(place, new_game.cpu):
                                print("Congratulations! You have successfully acquired " + str(place.name))
                            else:
                                print("Sorry, insufficient coins!")
                        else:
                            pass  # Do nothing

                new_game.player.coins += new_game.player.get_coins_per_turn()
                new_game.player.exp += new_game.player.get_exp_per_turn()
            else:
                # Save game data and quit the game
                save_game_data(new_game, file_name)
                sys.exit()
        else:
            # It is CPU's turn
            print("It is CPU's turn.")

            new_game.cpu.roll_dice(Dice(), new_game)
            print("Your opponent is now at:\n" + str(new_game.board.get_tiles()[new_game.cpu.position]))

            # Checking what type of tile the CPU lands on
            if isinstance(new_game.board.get_tiles()[new_game.cpu.position], EmptySpace):
                pass  # do nothing
            elif isinstance(new_game.board.get_tiles()[new_game.cpu.position], StartTile):
                pass  # do nothing
            elif isinstance(new_game.board.get_tiles()[new_game.cpu.position], ShinyZone):
                # Randomly generate a shiny
                shiny_zone: ShinyZone = new_game.board.get_tiles()[new_game.cpu.position]
                shiny: Shiny = shiny_zone.generate_shiny()
                print("Your opponent earns " + str(shiny.coin_reward) + " coins and " + str(shiny.exp_reward) + " EXP.")
                new_game.cpu.coins += shiny.coin_reward
                new_game.cpu.exp += shiny.exp_reward
                new_game.cpu.level_up()
            elif isinstance(new_game.board.get_tiles()[new_game.cpu.position], UpgradeShop):
                cpu_buy_upgrade: bool = random.random() <= 0.75
                if cpu_buy_upgrade:
                    upgrade_shop: UpgradeShop = new_game.board.get_tiles()[new_game.cpu.position]
                    upgrade_index: int = random.randint(0, len(upgrade_shop.get_upgrades_sold()) - 1)
                    to_buy: Upgrade = upgrade_shop.get_upgrades_sold()[upgrade_index]
                    if new_game.cpu.buy_upgrade(to_buy):
                        print("Your opponent has successfully bought " + str(to_buy.name))
                    else:
                        print("Your opponent has insufficient coins!")
                else:
                    pass  # Do nothing
            elif isinstance(new_game.board.get_tiles()[new_game.cpu.position], Place):
                place: Place = new_game.board.get_tiles()[new_game.cpu.position]

                # Checking whether the place has an owner or not
                # 1. If the place does not have an owner
                if place not in new_game.player.get_owned_list() and place not in new_game.cpu.get_owned_list():
                    cpu_buy_place: bool = random.random() <= 0.75
                    if cpu_buy_place:
                        if new_game.cpu.purchase_place(place):
                            print("Your opponent has successfully bought " + str(place.name))
                        else:
                            print("Your opponent has insufficient coins!")
                    else:
                        pass  # do nothing
                # 2. If the place is owned by the CPU
                elif place in new_game.cpu.get_owned_list():
                    cpu_upgrade_place: bool = random.random() <= 0.75
                    if cpu_upgrade_place:
                        if new_game.cpu.upgrade_place(place):
                            print("Your opponent has successfully upgraded " + str(place.name))
                        else:
                            print("Your opponent has insufficient coins!")
                    else:
                        pass  # do nothing
                # 3. If the place is owned by the player
                elif place in new_game.player.get_owned_list():
                    cpu_acquire_place: bool = random.random() <= 0.75
                    if cpu_acquire_place:
                        if new_game.cpu.acquire_place(place, new_game.player):
                            print("Your opponent has successfully acquired " + str(place.name))
                        else:
                            print("Your opponent has insufficient coins!")
                    else:
                        pass  # do nothing

            new_game.cpu.coins += new_game.cpu.get_coins_per_turn()
            new_game.cpu.exp += new_game.cpu.get_exp_per_turn()
        print("Enter 'Y' for yes.")
        print("Enter anything else for no.")
        continue_playing = input(
            "Do you want to continue playing 'Tenzichi Own The Planet - Board Game Edition'? ")

    # Save game data and quit the game
    save_game_data(new_game, file_name)
    sys.exit()


if __name__ == '__main__':
    main()
