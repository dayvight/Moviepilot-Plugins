import re
from typing import Any, Dict, List, Optional, Tuple

import pypinyin

from app.core.event import Event, eventmanager
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.event import TransferRenameBuildEventData
from app.schemas.types import ChainEventType


class TitleInitial(_PluginBase):
    """
    标题首字母注入插件
    在重命名时向 rename_dict 注入标题首字母变量 {{initial}}，
    支持在文件夹模板中使用，如 {{initial}}-{{title}}-{{year}}-[tmdb={{tmdbid}}]
    """
    plugin_name = "标题首字母注入"
    plugin_desc = "在重命名模板中注入标题首字母变量 {{initial}}，用于文件夹首字母分类前缀。"
    plugin_icon = "https://raw.githubusercontent.com/InfinityPacer/MoviePilot-Plugins/main/icons/smartrename.png"
    plugin_version = "1.0"
    plugin_author = "MoviePilot Agent"
    author_url = "https://github.com/dayvight"
    plugin_config_prefix = "titleinitial_"
    plugin_order = 42
    auth_level = 1

    _enabled = False

    def init_plugin(self, config: dict = None):
        if not config:
            return
        self._enabled = config.get("enabled") or False

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 6},
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件',
                                            'hint': '开启后将在重命名模板中注入 {{initial}} 变量',
                                            'persistent-hint': True
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12},
                                'content': [
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info',
                                            'variant': 'tonal',
                                            'text': '启用后，在重命名模板中可使用 {{initial}} 获取标题首字母（大写）。'
                                                    '例如文件夹模板：{{initial}}-{{title}}-{{year}}-[tmdb={{tmdbid}}]'
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False
        }

    def get_page(self) -> List[dict]:
        pass

    def get_service(self) -> List[Dict[str, Any]]:
        return []

    def stop_service(self):
        pass

    @eventmanager.register(ChainEventType.TransferRenameBuild)
    def handle_rename_build(self, event: Event):
        """
        监听 TransferRenameBuild 事件，向 rename_dict 注入首字母变量
        """
        if not event or not event.event_data:
            return

        event_data: TransferRenameBuildEventData = event.event_data
        rename_dict = event_data.rename_dict

        # 优先使用 title（中文标题），回退到 en_title，再回退到 original_title
        # 中文标题取拼音首字母，英文标题取首字母
        title = rename_dict.get("title") or rename_dict.get("en_title") or rename_dict.get("original_title")
        if not title:
            logger.debug("标题首字母注入：未找到标题字段，跳过")
            return

        # 提取首字母（大写）
        title = title.strip()
        if not title:
            return

        # 判断是否包含中文字符
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', title))
        if has_chinese:
            # 中文标题：取拼音首字母
            try:
                py = pypinyin.pinyin(title, style=pypinyin.Style.FIRST_LETTER)
                initials = ''.join([p[0][0].upper() for p in py if p and p[0] and p[0][0].isalpha()])
                initial = initials[0] if initials else "#"
            except Exception:
                initial = "#"
        else:
            # 英文标题：取第一个字母字符
            match = re.search(r'[A-Za-z]', title)
            initial = match.group(0).upper() if match else "#"

        rename_dict["initial"] = initial
        logger.debug(f"标题首字母注入：{title} -> {initial}")
