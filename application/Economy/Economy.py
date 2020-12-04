import time

from . import logger, ecConfig

unit = ecConfig.getConfig('setting').get('unit')
users: dict = ecConfig.Configs['config']
minus = ecConfig.getConfig('setting').get('enable_minus')
credit_pay = ecConfig.getConfig('setting').get('credit_pay')
capitalist: int = ecConfig.getConfig('setting').get('capitalist')
payments = {
    1: '余额支付',
    2: f'{unit}呗支付',
    3: f'余额-{unit}呗支付',
    4: f'{unit}呗-余额支付'
}


def debugIt(func):
    # @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f'{func.__name__} {args[1]} {unit} for {args[0]}')
        return func(*args, **kwargs)

    return wrapper


class Economy:

    @staticmethod
    async def addValue(money: int):
        ecConfig.Configs['setting']['value'] += money

    @staticmethod
    @debugIt
    async def addMoney(account: int, money: int) -> bool:
        account = str(account)
        await Economy.has(account)
        users[account]['balance'] += money
        return True

    @staticmethod
    @debugIt
    async def reduceMoney(account: int, money: int) -> bool:
        account = str(account)
        await Economy.has(account)
        if minus:
            users[account]['balance'] -= money
        else:
            if users[account]['balance'] >= money:
                users[account]['balance'] -= money
            else:
                # users[account]['balance'] = 0
                return False
        return True

    @staticmethod
    @debugIt
    async def setMoney(account: int, money: int):
        account = str(account)
        await Economy.has(account)
        if minus:
            users[account]['balance'] = money
        else:
            if money >= 0:
                users[account]['balance'] = money
            else:
                users[account]['balance'] = 0
                return False
        return True

    @staticmethod
    async def payMoney(payer: int, target: int, money: int) -> bool:
        payer = str(payer)
        target = str(target)
        await Economy.has(payer)
        await Economy.has(target)
        if users[payer]['balance'] >= money:
            users[payer]['balance'] -= money
            users[target]['balance'] += money
            logger.debug(f'{payer} pay {target} {money} {unit}')
            return True
        else:
            return False

    @staticmethod
    @debugIt
    async def addCredit(account: int, money: int) -> bool:
        account = str(account)
        await Economy.has(account)
        if users[account]['credit_pay_use'] < money:
            users[account]['credit_pay_use'] = 0
            logger.debug(f'add credit {money} > credit balance')
            return False
        else:
            users[account]['credit_pay_use'] -= money
            return True

    @staticmethod
    @debugIt
    async def reduceCredit(account: int, money: int) -> bool:
        account = str(account)
        await Economy.has(account)
        if (await Economy.getCreditBalance(account)) < money:
            # users[account]['credit_pay_use'] = credit_pay['base_balance'] + users[account]['credit_pay_adjust']
            logger.debug(f'reduce credit {money} > credit use')
            return False
        else:
            users[account]['credit_pay_use'] += money
            return True

    @staticmethod
    @debugIt
    async def setCredit(account: int, money: int) -> bool:
        account = str(account)
        await Economy.has(account)
        if 0 <= money <= credit_pay['base_balance'] + users[account]['credit_pay_adjust']:
            users[account]['credit_pay_use'] = credit_pay['base_balance'] + users[account]['credit_pay_adjust'] - money
            return True
        else:
            use = 0 if money > 0 else credit_pay['base_balance'] + users[account]['credit_pay_adjust']
            users[account]['credit_pay_use'] = use
            return False

    @staticmethod
    async def payCredit(payer: int, target: int, money: int, force: bool = False) -> bool:
        payer = str(payer)
        target = str(target)
        await Economy.has(payer)
        await Economy.has(target)
        if (await Economy.getCreditBalance(payer)) >= money:
            users[payer]['credit_pay_use'] += money
            users[target]['balance'] += money
            users[target]['credit_period_repay'] = int(users[payer]['credit_pay_use'] * .1)
            logger.debug(f'{payer} credit pay {target} {money} {unit}')
            return True
        else:
            if force:
                users[payer]['credit_pay_use'] += money
                users[target]['balance'] += money
                users[target]['credit_period_repay'] = int(users[payer]['credit_pay_use'] * .1)
                logger.debug(f'force {payer} credit pay {target} {money} {unit}')
            return False

    @staticmethod
    @debugIt
    async def repay(account: int, money: int = None) -> bool:
        account = str(account)
        await Economy.has(account)
        pay_min = users[account]['credit_period_pay']
        if pay_min > users[account]['credit_pay_use']:
            pay_min = users[account]['credit_pay_use']
        if not money:
            money = pay_min
        if money < pay_min:
            return False
        if money > users[account]['credit_pay_use']:
            money = users[account]['credit_pay_use']
        if await Economy.reduceMoney(account, money):
            await Economy.addCredit(account, money)
            return True
        else:
            return False

    @staticmethod
    @debugIt
    async def AutoRepay(account: int) -> bool:
        users[account] = {
            'balance': 0,
            'payment': 1,
            'credit_pay_use': 0,
            'credit_period_repay': 0,
            'credit_pay_adjust': 0,
            'update': time.time()
        }

        account = str(account)
        await Economy.has(account)
        update = users[account]['update']
        if time.time() - update > credit_pay['period']:
            users[account]['update'] = time.time()  # 1期
            pay: int = users[account]['credit_pay_use']  # 能还全还
            if await Economy.repay(account, pay):
                await Economy.adjustCredit(account, 10)
                return True
            else:
                if not await Economy.repay(account):  # 最低还款都不够
                    await Economy.adjustCredit(account, -10)
                    interest: int = ecConfig.getConfig('setting').get('interest') * users[account]['credit_pay_use']
                    return await Economy.payMix(account, capitalist, interest, 1, True)
                else:
                    await Economy.adjustCredit(account, 5)
                    return True

    @staticmethod
    @debugIt
    async def adjustCredit(account: int, num: int = 50) -> bool:
        account = str(account)
        await Economy.has(account)
        if users[account]['credit_pay_adjust'] + num + credit_pay['base_balance'] < 0:
            users[account]['credit_pay_adjust'] = -credit_pay['base_balance']
            return False
        else:
            users[account]['credit_pay_adjust'] += num
            return True

    @staticmethod
    async def payMix(payer: int, target: int, money: int, order: int, force=False) -> bool:
        if order == 1:
            if await Economy.payMoney(payer, target, money):
                return True
            else:
                m_balance: int = users[payer]['balance']
                c_balance: int = await Economy.getCreditBalance(payer)
                if m_balance + c_balance >= money:
                    await Economy.payMoney(payer, target, m_balance)
                    await Economy.payCredit(payer, target, money - m_balance, force)
                    return True
                else:
                    return False
        elif order == 2:
            if await Economy.payCredit(payer, target, money):
                return True
            else:
                m_balance: int = users[payer]['balance']
                c_balance: int = await Economy.getCreditBalance(payer)
                if m_balance + c_balance >= money:
                    await Economy.payCredit(payer, target, money - c_balance)
                    await Economy.payMoney(payer, target, m_balance)
                    return True
                else:
                    return False
        else:
            return False

    @staticmethod
    async def pay(payer: int, target: int, money: int) -> bool:
        payer = str(payer)
        target = str(target)
        await Economy.has(payer)
        await Economy.has(target)
        payment: int = users[payer]['payment']
        if payment == 1:
            return await Economy.payMoney(payer, target, money)
        if payment == 2:
            return await Economy.payCredit(payer, target, money)
        return await Economy.payMix(payer, target, money, payment - 2)

    @staticmethod
    async def money(account: int):
        account = str(account)
        await Economy.has(account)
        return users[account]

    @staticmethod
    async def has(account: str) -> bool:
        if users.get(account) is None:
            users[account] = {
                'balance': 0,
                'payment': 1,
                'credit_pay_use': 0,
                'credit_period_repay': 0,
                'credit_pay_adjust': 0,
                'update': time.time()
            }
            return False
        return True

    @staticmethod
    async def payment(account: str, payment: int) -> bool:
        account = str(account)
        await Economy.has(account)
        users[account]['payment'] = payment
        return True

    @staticmethod
    async def getCreditBalance(account: int) -> int:
        return credit_pay['base_balance'] + users[account]['credit_pay_adjust'] - users[account]['credit_pay_use']

    @staticmethod
    async def save(option=''):
        await ecConfig.save(option)

    @staticmethod
    async def trySave():
        last = ecConfig.getConfig('setting').get('last_save')
        period = ecConfig.getConfig('setting').get('save_period')
        if time.time() - last > period:
            ecConfig.getConfig('setting').set('last_save', time.time())
            await Economy.save()
            return True
        return False
