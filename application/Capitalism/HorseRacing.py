import asyncio
import random

from application.Economy import Economy


class Horse:
    dead_icon = '☠️'

    def __init__(self, distance: int, number: str, nick: str, icon: str):
        self.gambler = []
        self.status = []
        self.atk = random.randint(2, 7)
        self.sld = 1
        self.vit = random.randint(15, 23) - self.atk
        self.agi = random.randint(4, 7)
        self.luk = 0
        self.distance = distance
        self.number = number
        self.nick = nick
        self.icon = icon
        self.rank = 0
        self.lastStep = 0
        self.killed = False

    def addGambler(self, qq: int, wager: int):
        self.gambler.append([qq, wager])

    def addBuff(self, buff: list):
        self.status += buff

    def forward(self, boost: list = None):
        if not self.finished():
            if boost is None:
                forward: int = random.randint(self.agi - 2, self.agi + 3 + self.luk)
                self.distance -= forward
                self.lastStep = forward
            return True
        else:
            return False

    def finished(self) -> bool:
        return self.distance <= 0

    def setRank(self, rank: int):
        self.rank = rank

    def addAtk(self):
        atk = random.randint(1, 5 + self.luk)
        self.atk += atk
        return atk

    def addSld(self):
        sld = random.randint(1, 5 + self.luk)
        self.sld += sld
        return sld

    def addVit(self):
        vit = random.randint(1, 5 + self.luk)
        self.vit += vit
        return vit

    def addAgi(self):
        agi = random.randint(1, 3 + self.luk)
        self.agi += agi
        return agi

    def addLuk(self):
        self.luk += 1
        return 1

    def attack(self, damage: int):
        if self.sld > damage:
            sld = damage
            vit = 0
        else:
            sld = self.sld
            vit = damage - self.sld
        self.vit -= vit
        if self.vit <= 0:
            self.killed = True
        return sld, vit, self.killed

    def showStake(self) -> str:
        field: str = ''
        field += f'\n{self.number}号 {self.nick}:'
        for gambler in self.gambler:
            field += f'\n  {gambler[0]}: {gambler[1]}{Economy.unit}'
        return field

    def getIcon(self) -> str:
        return Horse.dead_icon if self.killed else self.icon


class Item:
    def __init__(self, target: list):
        self.target = target


class HorseRacing:
    horses_icon = ["🐴", "🏇", "🐮", "🐉", "🐎"]
    horses_name = ['十字架', '德意志', '下雪滑坡', '强尼没眉毛', '布达佩斯弹头']
    win_count = 1
    win_rate = [.9]
    distance = 40
    ready_time = 60
    horses_count = len(horses_icon)

    def __init__(self, classic: bool = True):
        self.bonus = 0
        self.horses = {}
        self.status = 0
        self.finish = []
        self.gambler_count = 0
        self.items = []
        self.gambler = []
        self.ranks = {}
        self.winners = []
        self.tax = 0
        self.own = 0
        self.roundInfo = []
        self.dead_horse_count = 0
        self.classic = False
        self.roundAddPerk = []
        self.round_group = []
        self.initHorseRacing()

    def initHorseRacing(self):
        for number in range(1, 6):
            horse = Horse(self.distance, number, self.horses_name[number - 1], self.horses_icon[number - 1])
            self.horses[str(number)] = horse

    def join(self, qq: int, number: str, wager: int):
        self.bonus += wager
        if [qq, wager, number] in self.gambler:
            return False, 2  # staked
        if (horse := self.getHorse(number)) and self.status == 0:
            horse.addGambler(qq, wager)
            self.gambler.append([qq, wager, number])
            self.gambler_count += 1
            return True, 0
        else:
            return False, 3  # no horse

    async def start(self, ready: int):
        await asyncio.sleep(ready)
        if self.gambler_count < 2:
            self.status = 2
            for gambler in self.gambler:
                await Economy.Economy.pay(Economy.capitalist, gambler[0], gambler[1])
            return False
        else:
            self.status = 1
            self.group()
            return True

    async def tick(self):
        await asyncio.sleep(60)
        await self.useItems()
        await self.battle()
        self.group()
        self.roundAddPerk.clear()
        for k in list(self.horses.keys()):
            horse = self.horses[k]
            if not horse.killed:
                if not horse.forward():
                    self.finish.append(horse)

        if len(self.finish) >= self.win_count or self.dead_horse_count >= self.horses_count:
            self.status = 2
            self.calculateRanks()
            return await self.finishGame()
        else:
            return False
        # 显示

    def getHorse(self, number: str) -> Horse:
        return self.horses.get(number)

    def addPerk(self, member, number, ty):
        if self.classic:
            return False, 1
        if self.status != 1:
            return False, 2
        if member in self.roundAddPerk:
            return False, 3
        return self.addPerks(member, number, ty)

    def addPerks(self, member: int, number: str = None, ty: int = 1):
        if number is None:
            number: str = self.getMyHorse(member)
        if horse := self.getHorse(number):
            self.roundAddPerk.append(member)
            if ty == 1:
                return True, [number, horse.nick, horse.addAtk()]
            if ty == 2:
                return True, [number, horse.nick, horse.addVit()]
            if ty == 3:
                return True, [number, horse.nick, horse.addSld()]
            if ty == 4:
                return True, [number, horse.nick, horse.addAgi()]
            if ty == 5:
                return True, [number, horse.nick, horse.addLuk()]
        else:
            return False, 4

    def getMyHorse(self, member: int) -> str:
        for gambler in self.gambler:
            if member == gambler[0]:
                return gambler[2]
        return None

    async def battle(self):
        for group in self.round_group:
            h1 = self.horses[str(group[0])]
            h2 = self.horses[str(group[1])]
            s1, v1, k1 = h1.attack(h2.atk)
            s2, v2, k2 = h2.attack(h1.atk)
            info = HorseRacing.generateBattleLog([h1, h2], [[s1, v1], [s2, v2]])
            if k1:
                self.dead_horse_count += 1
            if k2:
                self.dead_horse_count += 1
            self.roundInfo.append(info)

    async def logForward(self, horse):
        field = f'{horse.number}号 {horse.nick} {horse.icon} forward {horse.lastStep}'
        self.roundInfo.append(field)

    @staticmethod
    def generateBattleLog(horses: [Horse], value: list):
        sv_icon = ['🛡️', '🩸']
        battle_icon = ['🗡️', '⚔', '🔪']
        logs = []
        for index, horse in enumerate(horses):
            h_s = ''
            if horse.killed:
                h_s += Horse.dead_icon
            else:
                h_s += '     '
            for i, v in enumerate(value[index]):
                if v:
                    h_s += f'  {-v}{sv_icon[i]}'
                else:
                    h_s += '     '
            h_s += horse.icon
            logs.append(h_s)
        b_i = ''
        if not horses[0].killed and not horses[1].killed:
            b_i = battle_icon[1]
        else:
            if horses[0].killed:
                b_i += battle_icon[0]
            if horses[1].killed:
                b_i += battle_icon[2]
        return logs[0] + b_i + logs[1][::-1]

    def group(self):
        order = []
        for k, horse in self.horses.items():
            if not horse.killed:
                order.append(k)
        random.shuffle(order)
        if len(order) % 2:
            order.pop()
        group = []
        while order:
            tm: list = [order.pop(), order.pop()]
            group.append(tm)
        self.round_group = group

    def calculateRanks(self):
        rank = 1
        if self.finish:
            self.finish.sort(key=lambda x: x.distance, reverse=False)
            for _ in range(0, self.win_count):
                horse_i = self.finish[0].distance
                self.ranks[rank] = []
                for index, horse in enumerate(self.finish):
                    if horse.distance == horse_i:
                        self.ranks[rank].append(horse)
                        horse.setRank(rank)
                rank += 1

    async def addItem(self, item: Item):
        self.items.append(item)

    async def useItems(self):
        while self.items:
            item = self.items.pop()
            targets = item.target
            for target in targets:
                horse: Horse = self.horses.get(target)
                horse.addBuff(item.buff)
                # 文字描述

    async def stake(self, qq: int, number: str, wager: int) -> tuple:
        if await Economy.Economy.pay(qq, Economy.capitalist, wager):
            if (re := self.join(qq, number, wager))[0]:
                return True, 0
            else:
                await Economy.Economy.pay(Economy.capitalist, qq, wager)
                return False, re[1]
        return False, 1  # not enough money

    async def finishGame(self):
        use = 0
        for rank, v in self.ranks.items():
            gamblers = []
            for horse in v:
                gamblers += horse.gambler
            rank_gambler_wager_sum = sum([gambler[1] for gambler in gamblers])
            rank_bonus = int(self.bonus * self.win_rate[rank - 1])
            for gambler in gamblers:
                bonus = int((gambler[1] / rank_gambler_wager_sum) * rank_bonus)
                use += bonus
                await Economy.Economy.pay(Economy.capitalist, gambler[0], bonus)
                self.winners.append([gambler[0], bonus])
        use_rate = sum(self.win_rate)
        self.tax = int(self.bonus * use_rate) - use
        self.own = self.bonus - int(self.bonus * use_rate)
        return await self.display()

    async def displayHorsesInfo(self, check_death: bool = False):
        field = ''
        for horse in self.horses.values():
            if horse.killed and check_death:
                continue
            status = "☠️" if horse.killed else ''
            field += f'\n[{horse.number}号 {horse.nick} {horse.icon}]:'
            field += f'\n  🔪{horse.atk}  🛡️{horse.sld}  🥾{horse.agi}  🩸{horse.vit}  🍀{horse.luk}  {status}'
        return field

    async def getStakeInfo(self) -> str:
        field = '\n\n押注'
        for _, horse in self.horses.items():
            field += horse.showStake()
        return field

    async def getWinnerInfo(self) -> str:
        field = ''
        if self.ranks:
            field += '\n颁奖台'
            for rank, v in self.ranks.items():
                field += f'\nNo.{rank}'
                for horse in v:
                    field += f' [{horse.number}号 {horse.nick}]'
        return field

    async def getRacingInfo(self):
        field = '\n赛况'
        for k, horse in self.horses.items():
            field += '\n' + str(horse.number) + '|' + horse.distance * ' ' + horse.getIcon() + '\n      ' + horse.nick
        return field

    async def getNextGroupInfo(self):
        f: str = ''
        if self.status == 1 and self.round_group:
            f = '\n下局:'
            for group in self.round_group:
                horse1: Horse = self.horses[group[0]]
                horse2: Horse = self.horses[group[1]]
                f += f'\n[{horse1.number}号 {horse1.icon}]⚔[{horse2.icon} {horse2.number}号 ]'
        return f

    async def display(self) -> str:
        field: str = await self.displayLogs()
        field += await self.displayHorsesInfo(True)
        field += await self.getRacingInfo()
        field += await self.getNextGroupInfo()
        field += await self.getWinnerInfo()
        return field

    async def displayGamblers(self) -> str:
        field = await self.displayHorsesInfo()
        field += await self.getStakeInfo()
        field += await self.getWinnerInfo()
        return field

    async def displayLogs(self):
        return await self.getBattleLogs()

    async def getBattleLogs(self):
        field = 'LOG'
        for log in self.roundInfo:
            field += f'\n{log}'
        self.roundInfo.clear()
        return field
