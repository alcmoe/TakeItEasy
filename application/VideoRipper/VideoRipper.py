from graia.application import GraiaMiraiApplication as Slave, GroupMessage, FriendMessage
from graia.application.message.elements.internal import Plain, Image, Quote
from graia.application.message.chain import MessageChain as MeCh
from graia.broadcast.builtin.decoraters import Depend

from Listener import Listener
from utils.network import request, saveUrlVideo, Path, ClientConnectorError
from utils.thread import thread, repeatDelaySchedule

from .iwara.IwaraRipper import IwaraRipper
from . import logger, vrConfig


class VideoRipperListener(Listener):
    APP_COMMANDS = ['.VPC']
    APP_QUOTE_COMMAND = ['.DL']
    START_CHECK = False
    ripper = IwaraRipper()
    command: dict = dict()
    downloading = False

    def run(self):
        @self.bcc.receiver(GroupMessage, headless_decoraters=[Depend(self.cmdFilter)])
        async def groupCmdHandler(app: Slave, message: GroupMessage):
            await self.commandHandler(app, message)

        @self.bcc.receiver(FriendMessage, headless_decoraters=[Depend(self.quoteCMDFilter)])
        async def groupCmdHandler(app: Slave, message: FriendMessage):
            await self.quoteHandler(app, message)

    async def commandHandler(self, app: Slave, message: GroupMessage):
        commands: [str] = message.messageChain.asDisplay().split(' ')
        cmd = commands[0].upper()
        if cmd == self.APP_COMMANDS[0]:
            if self.START_CHECK:
                logger.info('already enable checking')
            else:
                thread.createTask(repeatDelaySchedule(60 * 10, self.subscriptionCheckTask, (app,)))
                self.START_CHECK = True
                logger.info('enable checking new post')

    async def quoteHandler(self, app: Slave, message):
        quote: Quote = self.command.get('quote')
        cmd: str = self.command.get('cmd')
        if quote.senderId == app.connect_info.account and cmd == self.APP_QUOTE_COMMAND[0]:
            if self.downloading:
                plain = Plain('A task is running pls wait')
                await app.sendFriendMessage(message.sender.id, MeCh.create([plain]))
                return
            if u_id_v_link := vrConfig.getConfig(self.ripper.ripper).get("quote2video").get(str(quote.id)):
                if videos := vrConfig.getConfig(self.ripper.ripper).get('user_videos').get(u_id_v_link[0]):
                    if video := videos.get(u_id_v_link[1]):
                        download_link = video['downloads'][0]['uri']
                        path_dir = 'application/VideoRipper/save/'
                        Path(path_dir).mkdir(exist_ok=True, parents=True)
                        name = path_dir + f'{video["author"]}{video["title"]}_{video["video_id"]}_source.mp4'
                        self.downloading = True
                        connector = await IwaraRipper.getConnector()
                        logger.debug('fetching ' + download_link)
                        try:
                            if not await saveUrlVideo(download_link, name, connector):
                                logger.debug(f'download url {u_id_v_link[1]} expired, refreshing video data')
                                await self.ripper.getVideo(u_id_v_link[1])
                                await saveUrlVideo(download_link, name, await IwaraRipper.getConnector())
                        except ClientConnectorError:
                            await app.sendFriendMessage(message.sender.id, MeCh.create(['Client error']))
                        finally:
                            self.downloading = False
                        vrConfig.getConfig(self.ripper.ripper).get("quote2video").pop(str(quote.id))
                        await vrConfig.save(self.ripper.ripper)
                        plain = Plain('A task is finished')
                        await app.sendFriendMessage(message.sender.id, MeCh.create([plain]))

    async def subscriptionCheckTask(self, app: Slave):
        new_videos: list = await self.ripper.checkSubscriptionsUpdate()
        if new_videos:
            q2v = vrConfig.getConfig(self.ripper.ripper).get('quote2video')
            for video in new_videos:
                user_id = video[0]
                video_link = video[1]
                video_info = await self.ripper.getVideo(video_link)
                author = Plain(video_info['author'] + '\n')
                time = Plain(video_info['time'])
                public = '' if video_info['public'] else '隐藏'
                ty = Plain('提交' + public + ('视频' if video_info['video'] else '图片') + '\n')
                title = Plain(video_info['title'] + '\n')
                connector = await IwaraRipper.getConnector()
                img_byte = await request(url=video_info['thumbnail'], connector=connector)
                thumbnail: Image = Image.fromUnsafeBytes(img_byte)
                info_text = f"\n{video_info['info']}\n" if video_info['info'] else ''
                info_text = info_text if len(info_text) < 160 else info_text[:160]
                info = Plain(info_text)
                link = Plain(self.ripper.host + video_info['url'])
                youtube = Plain('\nyoutube' if video_info['youtube'] else '')
                msg = [author, time, ty, title, thumbnail, info, link, youtube]
                qq = vrConfig.getConfig(self.ripper.ripper).get('qq')
                bot_msg = await app.sendFriendMessage(qq, MeCh.create(msg))
                q2v[str(bot_msg.messageId)] = [user_id, video_link]
            await vrConfig.save(self.ripper.ripper)
        else:
            logger.debug('nothing was post')
