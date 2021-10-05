import base64
import datetime
import hashlib
import json
import logging
import os
import time
from logging.handlers import TimedRotatingFileHandler

import requests

BASE_URL = "https://discord.com/api/"


def init_logger(child_name: str = None) -> logging.Logger:
    """
    Logger を初期化します。
    Args:
        child_name: プロジェクトの子 Logger である場合は、子の名前を指定
    Returns:
        logging.Logger: 初期化された Logger
    """
    _logger = logging.getLogger("Data-Crawling")
    if child_name is not None:
        _logger = _logger.getChild(child_name)
        _logger.setLevel(logging.INFO)
        return _logger

    _logger.setLevel(logging.INFO)
    dt = datetime.date.today()
    date_time = dt.strftime("%Y-%m-%d")

    if not os.path.exists("logs/"):
        os.mkdir("logs/")

    rotatedHandler = TimedRotatingFileHandler(
        filename="logs/%s.log" % date_time,
        encoding="UTF-8",
        when="MIDNIGHT",
        backupCount=30
    )
    rotatedHandler.setLevel(logging.INFO)
    rotatedHandler.setFormatter(logging.Formatter('[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s'))
    _logger.addHandler(rotatedHandler)
    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(logging.INFO)
    streamHandler.setFormatter(logging.Formatter('[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s'))
    _logger.addHandler(streamHandler)

    return _logger


def get_users_from_group(group: str):
    url = "https://api.jaoafa.com/users/perms/{group}".format(group=group)
    response = requests.get(url)
    response.raise_for_status()

    result = response.json()
    return result["data"]


def download_minecraft_head(uuid: str):
    url = "https://crafatar.com/avatars/{UUID}?overlay".format(UUID=uuid)
    response = requests.get(url)
    response.raise_for_status()
    content = response.content
    md5 = hashlib.md5(content).hexdigest()

    if not os.path.exists("images/{0}.png".format(md5)):
        with open("images/{0}.png".format(md5), "wb") as f:
            f.write(content)

    return md5


def getGuild(token,
             guild_id: str):
    url = BASE_URL + "/guilds/{0}".format(guild_id)
    response = requests.get(url, headers={
        "Content-Type": "application/json",
        "Authorization": "Bot " + token
    })
    if response.status_code != 200:
        return None

    return response.json()


def addEmoji(token,
             guild_id: str,
             name: str,
             file: str):
    with open(file, "rb") as f:
        data = f.read()
    encode = base64.b64encode(data)
    url = BASE_URL + "/guilds/{0}/emojis".format(guild_id)
    response = requests.post(url, json={
        "name": name,
        "image": "data:image/png;base64," + encode.decode("ascii")
    }, headers={
        "Content-Type": "application/json",
        "Authorization": "Bot " + token
    })
    if response.status_code == 201:
        return response.json()["id"]
    else:
        print("[ERROR] Add Emoji Failed:", response.status_code)
        print("[ERROR]", response.json())
        return None


def renameEmoji(token,
                guild_id: str,
                emoji_id: str,
                name: str):
    url = BASE_URL + "/guilds/{0}/emojis/{1}".format(guild_id, emoji_id)
    response = requests.post(url, json={
        "name": name,
    }, headers={
        "Content-Type": "application/json",
        "Authorization": "Bot " + token
    })
    return response.status_code != 200


def removeEmoji(token,
                guild_id: str,
                emoji_id: str):
    url = BASE_URL + "/guilds/{0}/emojis/{1}".format(guild_id, emoji_id)
    response = requests.delete(url, headers={
        "Content-Type": "application/json",
        "Authorization": "Bot " + token
    })
    return response.status_code != 200


def sendMessage(token,
                channel_id: str,
                content: str):
    print("sendMessage(" + channel_id + ")")
    url = BASE_URL + "/channels/{0}/messages".format(channel_id)
    response = requests.post(url, json={
        "content": content
    }, headers={
        "Content-Type": "application/json",
        "Authorization": "Bot " + token
    })
    if response.status_code == 200:
        return response.json()["id"]
    else:
        print("[ERROR] Send Message Failed:", response.status_code)
        print("[ERROR]", response.json())
        return None


def getOpeningGuildId(guilds: dict):
    # guilds -> guild_id: emoji_count
    for (guild_id, emoji_count) in guilds.items():
        if emoji_count < 50:
            return guild_id


def generateEmojiList(config):
    token = config["token"]
    guild_ids = config["guild_ids"]
    emoji_list_channels = config["emoji_list_channels"]
    for guild_id in guild_ids:
        guild_info = getGuild(token, guild_id)
        emoji_list_channel = emoji_list_channels[guild_id]
        emoji_list = []
        for emoji in guild_info["emojis"]:
            print(emoji["name"], len(emoji_list))
            emoji_list.append("<:" + emoji["name"] + ":" + emoji["id"] + "> = `:" + emoji["name"] + ":`")

            if len("\n".join(emoji_list)) >= 1900:
                sendMessage(token, emoji_list_channel, "\n".join(emoji_list))
                emoji_list = []

        sendMessage(token, emoji_list_channel, "\n".join(emoji_list))


def save(data,
         emoji_hashes,
         emoji_guild_ids,
         emoji_ids):
    with open("linking-player-uuid.json", "w") as f:
        json.dump(data, f)

    with open("linking-uuid-hashes.json", "w") as f:
        json.dump(emoji_hashes, f)

    with open("linking-emoji-guild-id.json", "w") as f:
        json.dump(emoji_guild_ids, f)

    with open("linking-uuid-emoji-id.json", "w") as f:
        json.dump(emoji_ids, f)


def main():
    if not os.path.exists("images/"):
        logger.info("mkdir images directory")
        os.mkdir("images")

    config = {}
    if os.path.exists("config.json"):
        logger.info("loading config.json")
        with open("config.json", "r") as f:
            config = json.load(f)

    # Get Users
    users = []
    admin_users = get_users_from_group("admin")
    users.extend(admin_users)
    moderator_users = get_users_from_group("moderator")
    users.extend(moderator_users)
    regular_users = get_users_from_group("regular")
    users.extend(regular_users)
    verified_users = get_users_from_group("verified")
    users.extend(verified_users)

    logger.info("Users Count:", len(users))

    # Check Emojis Count
    guilds = {}
    for guild_id in config["guild_ids"]:
        guild_info = getGuild(config["token"], guild_id)
        guilds[guild_id] = len(guild_info["emojis"])
    logger.info("Guilds Count:", len(guilds))

    # Get Cache Data
    data = {}  # UUID: PLAYER NAME
    if os.path.exists("linking-player-uuid.json"):
        with open("linking-player-uuid.json", "r") as f:
            data = json.load(f)
    logger.info("PlayerUUIDLinked Count:", len(data))

    emoji_hashes = {}  # UUID: Hash
    if os.path.exists("linking-uuid-hashes.json"):
        with open("linking-uuid-hashes.json", "r") as f:
            emoji_hashes = json.load(f)
    logger.info("Emoji Hashes Count:", len(emoji_hashes))

    emoji_guild_ids = {}  # Emoji Id: Guild Id
    if os.path.exists("linking-emoji-guild-id.json"):
        with open("linking-emoji-guild-id.json", "r") as f:
            emoji_guild_ids = json.load(f)
    logger.info("Emoji Guild Ids Count:", len(emoji_guild_ids))

    emoji_ids = {}  # UUID: Emoji Id
    if os.path.exists("linking-uuid-emoji-id.json"):
        with open("linking-uuid-emoji-id.json", "r") as f:
            emoji_ids = json.load(f)
    logger.info("Emoji Ids Count:", len(emoji_ids))

    new_users = {}
    changed_users = {}
    changed_skin_users = {}
    removed_users = list(emoji_ids.keys())
    for user in users:
        logger.info("Process:", user["mcid"], user["uuid"])
        isNew = False
        isRenamed = False
        isChanged = False

        # New?
        if user["uuid"] not in data.keys() or user["uuid"] not in emoji_ids:
            # New!
            logger.info("-> New!")
            isNew = True
            new_users[user["uuid"]] = user["mcid"]
            data[user["uuid"]] = user["mcid"]

        # Renamed?
        if data[user["uuid"]] != user["mcid"]:
            # Renamed!
            logger.info("-> Renamed!")
            isRenamed = True
            data[user["uuid"]] = user["mcid"]
            changed_users[user["uuid"]] = user["mcid"]

        # Download
        logger.info("-> Downloading...")
        md5 = download_minecraft_head(user["uuid"])
        logger.info("-> MD5:", md5)

        # Changed skin?
        if user["uuid"] in emoji_hashes.keys() and emoji_hashes[user["uuid"]] != md5:
            logger.info("-> Changed skin!")
            isChanged = True
            emoji_hashes[user["uuid"]] = md5
            changed_skin_users[user["uuid"]] = md5

        if isChanged:
            emoji_id = emoji_ids[user["uuid"]]
            guild_id = emoji_guild_ids[emoji_id]
            res = removeEmoji(config["token"], guild_id, emoji_id)
            logger.info("-> removeEmoji:", res)

        if isRenamed:
            emoji_id = emoji_ids[user["uuid"]]
            guild_id = emoji_guild_ids[emoji_id]
            res = renameEmoji(config["token"], guild_id, emoji_id, user["mcid"])
            logger.info("-> renameEmoji:", res)

        if isNew:
            guild_id = getOpeningGuildId(guilds)
            emoji_id = addEmoji(config["token"], guild_id, user["mcid"], "images/{0}.png".format(md5))
            if emoji_id is None:
                print("[ERROR] -> addEmoji: Failed")
                return
            logger.info("-> addEmoji:", emoji_id, " / Guild Id:", guild_id)
            emoji_ids[user["uuid"]] = emoji_id
            emoji_guild_ids[emoji_id] = guild_id
            guilds[guild_id] = guilds[guild_id] - 1

        time.sleep(1)
        if user["uuid"] in removed_users:
            removed_users.remove(user["uuid"])
        save(data, emoji_hashes, emoji_guild_ids, emoji_ids)

    for removed_uuid in removed_users:
        logger.info("Removed " + removed_uuid)
        emoji_id = emoji_ids[removed_uuid]
        if emoji_id in emoji_guild_ids:
            del emoji_guild_ids[emoji_id]

        if removed_uuid in emoji_ids:
            del emoji_ids[removed_uuid]

        if removed_uuid in emoji_hashes:
            del emoji_hashes[removed_uuid]

    save(data, emoji_hashes, emoji_guild_ids, emoji_ids)

    # generateEmojiList(config)  # Javajaotan2に任せる


logger = init_logger()

if __name__ == "__main__":
    main()
