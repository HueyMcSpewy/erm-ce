import datetime
import json
import logging
import time
from dataclasses import MISSING
from pkgutil import iter_modules
import re
from collections import defaultdict
import asyncio

from datamodels.MapleKeys import MapleKeys
from datamodels.Whitelabel import Whitelabel
from tasks.iterate_ics import iterate_ics
from tasks.check_loa import check_loa
from tasks.check_reminders import check_reminders
from tasks.check_infractions import check_infractions
from tasks.iterate_prc_logs import iterate_prc_logs
from tasks.tempban_checks import tempban_checks
from tasks.process_scheduled_pms import process_scheduled_pms
from tasks.statistics_check import statistics_check
from tasks.change_status import change_status
from tasks.check_whitelisted_car import check_whitelisted_car
from tasks.sync_weather import sync_weather
from tasks.iterate_conditions import iterate_conditions
from tasks.prc_automations import prc_automations
from tasks.mc_discord_checks import mc_discord_checks
from utils.accounts import Accounts
from utils.emojis import EmojiController

from utils.log_tracker import LogTracker
from utils.mc_api import MCApiClient
from utils.mongo import Document

import aiohttp
import decouple
import discord.mentions
import motor.motor_asyncio
import asyncio
import pytz
import sentry_sdk
from decouple import config
from discord import app_commands
from discord.ext import tasks, commands
from roblox import client as roblox
from sentry_sdk import push_scope, capture_exception
from sentry_sdk.integrations.pymongo import PyMongoIntegration

from datamodels.CustomFlags import CustomFlags
from datamodels.ServerKeys import ServerKeys
from datamodels.ShiftManagement import ShiftManagement
from datamodels.ActivityNotice import ActivityNotices
from datamodels.Analytics import Analytics
from datamodels.Consent import Consent
from datamodels.CustomCommands import CustomCommands
from datamodels.Errors import Errors
from datamodels.FiveMLinks import FiveMLinks
from datamodels.LinkStrings import LinkStrings
from datamodels.PunishmentTypes import PunishmentTypes
from datamodels.Reminders import Reminders
from datamodels.Settings import Settings
from datamodels.APITokens import APITokens
from datamodels.StaffConnections import StaffConnections
from datamodels.Views import Views
from datamodels.Actions import Actions
from datamodels.Warnings import Warnings
from datamodels.ProhibitedUseKeys import ProhibitedUseKeys
from datamodels.PendingOAuth2 import PendingOAuth2
from datamodels.OAuth2Users import OAuth2Users
from datamodels.IntegrationCommandStorage import IntegrationCommandStorage
from datamodels.SavedLogs import SavedLogs
from menus import CompleteReminder, LOAMenu, RDMActions
from utils.viewstatemanger import ViewStateManager
from utils.bloxlink import Bloxlink
from utils.prc_api import PRCApiClient
from utils.prc_api import ResponseFailure
from utils.utils import *
from utils.constants import *
import utils.prc_api


_global_fetch_semaphore = asyncio.Semaphore(45)
_fetch_delays = defaultdict(float)

async def rate_limited_fetch(coro, endpoint_type="default"):
    """Rate-limited wrapper for Discord API calls"""
    async with _global_fetch_semaphore:
        if _fetch_delays[endpoint_type] > 0:
            await asyncio.sleep(_fetch_delays[endpoint_type])
        
        try:
            result = await coro
            _fetch_delays[endpoint_type] = max(0, _fetch_delays[endpoint_type] - 0.1)
            return result
        except discord.HTTPException as e:
            if e.status == 429:
                _fetch_delays[endpoint_type] = min(_fetch_delays[endpoint_type] + 0.5, 5.0)
                if e.retry_after:
                    await asyncio.sleep(e.retry_after)
            raise

setup = False

try:
    sentry_url = config("SENTRY_URL")
    bloxlink_api_key = config("BLOXLINK_API_KEY")
except decouple.UndefinedValueError:
    sentry_url = ""
    bloxlink_api_key = ""

discord.utils.setup_logging(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

credentials_dict = {}
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]


class Bot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_status: bool = False
        self._member_cache = {}
        self._guild_cache = {}
        self._cache_timeout = 300

    async def close(self):
        for session in self.external_http_sessions:
            if session is not None and session.closed is False:
                await session.close()
        await super().close()

    async def is_owner(self, user: discord.User):
        if user.id == 881062877526654987:
            return True
        if environment != "CUSTOM":
            return await super().is_owner(user)
        else:
            return False

    async def setup_hook(self) -> None:
        self.external_http_sessions: list[aiohttp.ClientSession] = []
        self.view_state_manager: ViewStateManager = ViewStateManager()

        if not self.setup_status:
            logging.info(
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━���━━━━━━\n\n{} is online!".format(
                    self.user.name
                )
            )
            self.mongo = motor.motor_asyncio.AsyncIOMotorClient(str(mongo_url))
            if environment == "DEVELOPMENT":
                self.db = self.mongo["erm"]
            elif environment == "PRODUCTION":
                self.db = self.mongo["erm"]
            elif environment == "ALPHA":
                self.db = self.mongo["erm"]
            elif environment == "CUSTOM":
                self.db = self.mongo["erm"]
            else:
                raise Exception("Invalid environment")
            
            self.panel_db = self.mongo["UserIdentity"]
            self.priority_settings = Document(self.panel_db, "PrioritySettings")
            self.staff_requests = Document(self.panel_db, "StaffRequests")

            self.start_time = time.time()

            self.log_tracker = LogTracker(self)
            self.scheduled_pm_queue = asyncio.Queue()
            self.pm_counter = {}
            self.team_restrictions_infractions = {}

            self.shift_management = ShiftManagement(self.db, "shift_management")
            self.errors = Errors(self.db, "errors")
            self.loas = ActivityNotices(self.db, "leave_of_absences")
            self.reminders = Reminders(self.db, "reminders")
            self.custom_commands = CustomCommands(self.db, "custom_commands")
            self.analytics = Analytics(self.db, "analytics")
            self.punishment_types = PunishmentTypes(self.db, "punishment_types")
            self.custom_flags = CustomFlags(self.db, "custom_flags")
            self.views = Views(self.db, "views")
            self.api_tokens = APITokens(self.db, "api_tokens")
            self.link_strings = LinkStrings(self.db, "link_strings")
            self.fivem_links = FiveMLinks(self.db, "fivem_links")
            self.consent = Consent(self.db, "consent")
            self.punishments = Warnings(self)
            self.settings = Settings(self.db, "settings")
            self.server_keys = ServerKeys(self.db, "server_keys")

            self.maple_county = self.mongo["MapleCounty"]
            self.mc_keys = MapleKeys(self.maple_county, "Auth")

            self.staff_connections = StaffConnections(self.db, "staff_connections")
            self.ics = IntegrationCommandStorage(self.db, "logged_command_data")
            self.actions = Actions(self.db, "actions")
            self.prohibited = ProhibitedUseKeys(self.db, "prohibited_keys")
            self.saved_logs = SavedLogs(self.db, "saved_logs")
            self.whitelabel = Whitelabel(self.mongo["ERMProcessing"], "Instances")

            self.pending_oauth2 = PendingOAuth2(self.db, "pending_oauth2")
            self.oauth2_users = OAuth2Users(self.db, "oauth2")

            self.accounts = Accounts(self)

            if environment == "CUSTOM":
                doc = await self.whitelabel.db.find_one({"GuildID": config("CUSTOM_GUILD_ID", default="0")})
                if not doc:
                    raise Exception(
                        "Custom guild ID not found in the database. This means the whitelabel subscription is overdue."
                    )

            self.roblox = roblox.Client()
            self.prc_api = PRCApiClient(
                self,
                base_url=config(
                    "PRC_API_URL", default="https://api.policeroleplay.community/v1"
                ),
                api_key=config("PRC_API_KEY", default="default_api_key"),
            )
            self.mc_api = MCApiClient(
                self, base_url=config("MC_API_URL"), api_key=config("MC_API_KEY")
            )
            self.bloxlink = Bloxlink(self, config("BLOXLINK_API_KEY"))

            Extensions = [m.name for m in iter_modules(["cogs"], prefix="cogs.")]
            Events = [m.name for m in iter_modules(["events"], prefix="events.")]
            BETA_EXT = ["cogs.StaffConduct"]
            EXTERNAL_EXT = ["utils.api"]
            [Extensions.append(i) for i in EXTERNAL_EXT]

            self.environment = environment
            self.emoji_controller = EmojiController(self)

            await self.emoji_controller.prefetch_emojis()

            for extension in Extensions:
                try:
                    if extension not in BETA_EXT:
                        await self.load_extension(extension)
                        logging.info(f"Loaded {extension}")
                    elif environment == "DEVELOPMENT" or environment == "ALPHA":
                        await self.load_extension(extension)
                        logging.info(f"Loaded {extension}")
                except Exception as e:
                    logging.error(f"Failed to load extension {extension}.", exc_info=e)

            for extension in Events:
                try:
                    await self.load_extension(extension)
                    logging.info(f"Loaded {extension}")
                except Exception as e:
                    logging.error(f"Failed to load extension {extension}.", exc_info=e)

            bot.error_list = []
            logging.info("Connected to MongoDB!")

            await bot.load_extension("utils.hot_reload")

            # --- GLOBAL SYNC PROMPT ---
            if not bot.is_synced:
                if getattr(bot, "global_sync", False):
                    logging.info("Global syncing slash commands...")
                    await self.tree.sync()
                else:
                    logging.info("Skipping global sync; using guild sync...")
                    bot.tree.copy_global_to(guild=discord.Object(id=1403328821121388674))
                bot.is_synced = True
            # -------------------------

            asyncio.create_task(self.start_tasks())
            await bot.add_cog(ServerCountStatus(bot))
            
            async for document in self.views.db.find({}):
                if document["view_type"] == "LOAMenu":
                    for index, item in enumerate(document["args"]):
                        if item == "SELF":
                            document["args"][index] = self
                    loa_id = document["args"][3]
                    if isinstance(loa_id, dict):
                        loa_expiry = loa_id["expiry"]
                        if loa_expiry < datetime.datetime.now().timestamp():
                            await self.views.delete_by_id(document["_id"])
                            continue
                    self.add_view(
                        LOAMenu(*document["args"]), message_id=document["message_id"]
                    )
            self.setup_status = True

    async def start_tasks(self):
        logging.info("Starting tasks...")
        check_reminders.start(bot)
        logging.info("Startng the Check Reminders task...")
        await asyncio.sleep(30)
        check_loa.start(bot)
        logging.info("Starting the Check LOA task...")
        await asyncio.sleep(30)
        iterate_ics.start(bot)
        logging.info("Starting the Iterate ICS task...")
        await asyncio.sleep(30)
        iterate_prc_logs.start(bot)
        logging.info("Starting the Iterate PRC Logs task...")
        await asyncio.sleep(30)
        statistics_check.start(bot)
        logging.info("Starting the Statistics Check task...")
        await asyncio.sleep(30)
        tempban_checks.start(bot)
        logging.info("Starting the Tempban Checks task...")
        await asyncio.sleep(30)
        check_whitelisted_car.start(bot)
        logging.info("Starting the Check Whitelisted Car task...")
        if self.environment != "CUSTOM":
            await asyncio.sleep(30)
            change_status.start(bot)
        logging.info("Starting the Change Status task...")
        await asyncio.sleep(30)
        process_scheduled_pms.start(bot)
        logging.info("Starting the Process Scheduled PMs task...")
        await asyncio.sleep(30)
        sync_weather.start(bot)
        logging.info("Starting the Sync Weather task...")
        await asyncio.sleep(30)
        iterate_conditions.start(bot)
        logging.info("Starting the Iterate Conditions task...")
        await asyncio.sleep(30)
        check_infractions.start(bot)
        logging.info("Starting the Check Infractions task...")
        await asyncio.sleep(30)
        prc_automations.start(bot)
        logging.info("Starting the ER:LC Discord Checks task...")
        await asyncio.sleep(30)
        mc_discord_checks.start(bot)
        logging.info("Starting the MC Discord Checks task...")
        logging.info("All tasks are now running!")


if config("ENVIRONMENT") == "CUSTOM":
    Bot.__bases__ = (commands.Bot,)

bot = Bot(
    command_prefix=get_prefix,
    case_insensitive=True,
    intents=intents,
    help_command=None,
    allowed_mentions=discord.AllowedMentions(
        replied_user=False, everyone=False, roles=False
    ),
)
bot.is_synced = False
bot.shift_management_disabled = False
bot.punishments_disabled = False
bot.bloxlink_api_key = bloxlink_api_key
environment = config("ENVIRONMENT", default="DEVELOPMENT")
internal_command_storage = {}

# --- RUN FUNCTION WITH GLOBAL SYNC PROMPT ---
def run():
    sentry_sdk.init(
        dsn=sentry_url,
        traces_sample_rate=1.0,
        integrations=[PyMongoIntegration()],
        _experiments={
            "profiles_sample_rate": 1.0,
        },
    )

    # Ask user about global sync
    user_input = input("Do you want to globally sync commands to all servers? (y/n): ").strip().lower()
    bot.global_sync = user_input == "y"

    try:
        bot.run(bot_token)
    except Exception as e:
        with sentry_sdk.isolation_scope() as scope:
            scope.level = "error"
            capture_exception(e)
        raise e


if __name__ == "__main__":
    run()
