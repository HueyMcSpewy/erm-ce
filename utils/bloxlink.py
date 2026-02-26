import discord
import logging
from discord.ext import commands
import aiohttp


class Bloxlink:
    def __init__(self, bot: commands.Bot, key: str):
        self.api_key = key
        timeout = aiohttp.ClientTimeout(total=10)
        self.session = aiohttp.ClientSession()
        self.semaphore = asyncio.Semaphore(10)
        bot.external_http_sessions.append(self.session)
        self.bot = bot

    async def _send_request(self, method, url, params=None, body=None):
        try:
            async with self.session.request(
            method,
            url,
            headers={"Authorization": self.api_key},
            **kwargs
        ) as resp:

            if resp.status >= 400:
                logging.warning(f"HTTP {resp.status} from {url}")
                return resp.status, None

            data = await resp.json()
            return resp.status, data

        except asyncio.TimeoutError:
            logging.error(f"Timeout when requesting {url}")
            raise
        except aiohttp.ClientError as e:
            logging.error(f"Client error: {e}")
        raise

    async def find_roblox(self, user_id: int):
        doc = await self.bot.oauth2_users.db.find_one({"discord_id": user_id})
        if doc:
            return {"robloxID": doc["roblox_id"]}

        response, resp_json = await self._send_request(
            "GET", f"https://api.blox.link/v4/public/guilds/1403328821121388674/discord-to-roblox/{user_id}"
        )

        if resp_json.get("error"):
            return {}
        else:
            return resp_json

    async def get_roblox_info(self, user_id: int):
        if not user_id:
            return {}
        if isinstance(user_id, int): 
                url = "https://users.roblox.com/v1/users/{}" .format (user_id)
                async with self.session.get(url) as resp:
                    return await resp.json()
        else: # So if it is a username it does not break             
            payload = {
                "usernames": [user_id]
            }
            async with self.session.post(
                    "https://users.roblox.com/v1/usernames/users",
                    json=payload
                ) as response:
                    data = await response.json()
            user_list = data.get("data",[])
            if user_list:
                userid =  user_list[0].get("id")
            else:
                return {}

                url = "https://users.roblox.com/v1/users/{}" .format (userid)
                async with self.session.get(url) as resp:
                    return await resp.json()          
        # some how this jank code works


