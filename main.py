import os
import uuid
import json
import aiohttp
import argparse
from datetime import datetime, timezone
from fake_useragent import UserAgent
from colorama import *

green = Fore.LIGHTGREEN_EX
red = Fore.LIGHTRED_EX
magenta = Fore.LIGHTMAGENTA_EX
white = Fore.LIGHTWHITE_EX
black = Fore.LIGHTBLACK_EX
reset = Style.RESET_ALL
yellow = Fore.LIGHTYELLOW_EX


class Grass:
    def __init__(self, userid, proxy):
        self.userid = userid
        self.proxy = proxy
        self.ses = aiohttp.ClientSession()
        self.log("Initialization successful!")

    def log(self, msg):
        now = datetime.now(tz=timezone.utc).isoformat(" ").split(".")[0]
        print(f"{black}[{now}] {reset}{msg}{reset}")

    @staticmethod
    async def ipinfo(proxy=None):
        async with aiohttp.ClientSession() as client:
            result = await client.get("https://api.ipify.org/", proxy=proxy)
            return await result.text()

    async def start(self):
        max_retry = 20
        retry = 1
        proxy = self.proxy
        if proxy is None:
            proxy = await Grass.ipinfo()
        browser_id = uuid.uuid5(uuid.NAMESPACE_URL, proxy)
        useragent = UserAgent().random
        headers = {
            'User-Agent': useragent,
            'Pragma': 'no-cache',
            'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'OS': 'Windows',
            'Platform': 'Desktop',
            'Browser': 'Mozilla'
        }
        self.log("Starting to connect to the server!")
        while True:
            try:
                if retry >= max_retry:
                    self.log("max retrying reacted, skip the proxy !")
                    await self.ses.close()
                    return
                async with self.ses.ws_connect(
                    "wss://proxy2.wynd.network:4650/",
                    headers=headers,
                    proxy=self.proxy,
                    timeout=1000,
                    autoclose=False,
                ) as wss:
                    res = await wss.receive_json()
                    auth_id = res.get("id")
                    if auth_id is None:
                        self.log("auth id is None")
                        return None
                    auth_data = {
                        "id": auth_id,
                        "origin_action": "AUTH",
                        "result": {
                            "browser_id": browser_id.__str__(),
                            "user_id": self.userid,
                            "user_agent": useragent,
                            "timestamp": int(datetime.now().timestamp()),
                            "device_type": "desktop",
                            "version": "4.28.2",
                        },
                    }
                    auth_result = await wss.send_json(auth_data)
                    self.log(f"Successfully connected to the server! Auth result: {auth_result}")
                    retry = 1
                    while True:
                        ping_data = {
                            "id": uuid.uuid4().__str__(),
                            "version": "1.0.0",
                            "action": "PING",
                            "data": {},
                        }
                        ping_result = await wss.send_json(ping_data)
                        self.log("Sending ping to the server ! " + str(ping_data) + " Result: " + str(ping_result))
                        pong_data = {"id": "F3X", "origin_action": "PONG"}
                        pong_result = await wss.send_json(pong_data)
                        self.log("Sending pong to the server ! " + str(pong_data) + " Result: " + str(pong_result))
                        await countdown(120)
            except KeyboardInterrupt:
                await self.ses.close()
                exit()
            except Exception as e:
                self.log("error : " + str(e))
                retry += 1
                continue


async def countdown(t):
    for i in range(t, 0, -1):
        minute, seconds = divmod(i, 60)
        hour, minute = divmod(minute, 60)
        seconds = str(seconds).zfill(2)
        minute = str(minute).zfill(2)
        hour = str(hour).zfill(2)
        print(f"waiting for {hour}:{minute}:{seconds} ", flush=True, end="\r")
        await asyncio.sleep(1)


async def main():
    arg = argparse.ArgumentParser()
    arg.add_argument(
        "--proxy", "-P", default="proxies.txt", help="Custom proxy input file "
    )
    args = arg.parse_args()
    os.system("cls" if os.name == "nt" else "clear")
    token = open("token.txt", "r").read()
    userid = open("userid.txt", "r").read()
    if len(userid) <= 0:
        print("Error: Please enter your user ID first!")
        exit()
    if not os.path.exists(args.proxy):
        print(args.proxy + " not found, please ensure " + args.proxy + " is available!")
        exit()
    proxies = open(args.proxy, "r").read().splitlines()
    if len(proxies) <= 0:
        proxies = [None]
    tasks = [Grass(userid, proxy).start() for proxy in proxies]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        import asyncio
        if os.name == "nt":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        exit()
