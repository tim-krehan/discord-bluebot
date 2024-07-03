# https://github.com/proxmoxer/proxmoxer
# https://pve.proxmox.com/pve-docs/api-viewer/index.html

from dotenv import load_dotenv
from proxmoxer import ProxmoxAPI
import discord
import os
import json

load_dotenv()

discord_token = os.environ.get("DISCORD_TOKEN")
proxmox_token = {
    "endpoints": os.environ.get("PROXMOX_ENDPOINTS").split(","),
    "user": os.environ.get("PROXMOX_USER"),
    "name": os.environ.get("PROXMOX_TOKEN_NAME"),
    "value": os.environ.get("PROXMOX_TOKEN_VALUE"),
}

games = {}
with open("games.json", "r") as handle:
    config_string = handle.read()
    games = json.loads(config_string)


def start_game(game):
    print("connecting to the proxmox host")
    proxmox = ProxmoxAPI(
        proxmox_token["endpoints"][0],
        user=proxmox_token["user"],
        token_name=proxmox_token["name"],
        token_value=proxmox_token["value"],
        backend="https",
        service="PVE",
        verify_ssl=False,
    )

    game_server = ""
    endpoint = ""
    print("searching for the node this container belongs to")
    for node in proxmox_token["endpoints"]:
        print(f"looking in inventory of {node}")
        lxc_container = proxmox.nodes(node).lxc.get()
        print(f"filtering result, got {len(node)} container")
        desired_container = [
            cnt for cnt in lxc_container if cnt["name"] == game["container"]
        ]
        if len(desired_container) == 1:
            game_server = desired_container[0]
            endpoint = node
            print(f"found it on {node}")
            break
        else:
            continue


    if len(game_server) < 1:
        exit()

    if game_server["status"] == "stopped":
        print(f"starting container with id {game_server['vmid']}")
        proxmox.nodes(endpoint).lxc(
            game_server["vmid"]
        ).status.start.post()
    else:
        print(f"container is in state {game_server['status']}")


class BlueBot(discord.Client):
    async def on_ready(self):
        print(f"logged in as {self.user} (ID: {self.user.id})")

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        if message.content.startswith(">help"):
            reply_content = (
                f"Currently there are {len(games.keys())} supported game(s):\n"
            )
            for key, game in games:
                reply_content += f"- {game.name}\n"
            reply_content += (
                "Type ``` >start server [GAMENAME] ``` to start that game server"
            )
            await message.reply(reply_content, mention_author=True)

        if message.content.startswith(">start server"):
            game_name = str(message.content).split(" ")[2].lower()
            if game_name in games.keys():
                desired_game = games[game_name]
                print(f"trying to start {desired_game['name']} for {message.author.name}")
                await message.reply(f"Starting {desired_game['name']} server", mention_author=True)
                start_game(game=desired_game)
                await message.reply(
                    f"game is up and running! You can connect to {desired_game['url']}\nThe Server will automatically stop at 2am.",
                    mention_author=True,
                )
            else:
                await message.reply(
                    f"{game_name} is not in the list of supported games, try ``` >help ```",
                    mention_author=True,
                )
            print(f"done")


intents = discord.Intents.default()
intents.message_content = True

discord_client = BlueBot(intents=intents)
discord_client.run(discord_token)
