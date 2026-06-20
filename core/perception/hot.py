"""热点采集（吸收自 JD 的 hot_perception.py）。

抓百度实时热搜。CSS 选择器依赖百度页面结构，**明知脆弱**——抓空/异常时返回 []，
由 SenseAgent 决定回退到内置热点，保证系统始终可演示。
"""
from datetime import datetime
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from core.config import HOT_FETCH_LIMIT, REQUEST_TIMEOUT

BAIDU_HOT_URL = "https://top.baidu.com/board?tab=realtime"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def fetch_baidu_hot(limit: int = HOT_FETCH_LIMIT, timeout: int = REQUEST_TIMEOUT) -> List[Dict]:
    """抓百度热搜前 N 条。失败返回 []。

    返回每条: {rank, title, heat, source, url, fetched_at}
    """
    try:
        resp = requests.get(BAIDU_HOT_URL, headers=_HEADERS, timeout=timeout)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        # 百度热搜标题链接（class 含 title_dIF3，移植自 JD；百度改版会失效）
        links = soup.select('a[class*="title_dIF3"]') or soup.select('div.c-single-text-plain a')
        now = datetime.now().isoformat()
        topics: List[Dict] = []
        for idx, link in enumerate(links[:limit], 1):
            title = link.get_text(strip=True)
            if not title:
                continue
            topics.append({
                "rank": idx,
                "title": title,
                "heat": (len(links) - idx + 1) * 10000,
                "source": "baidu",
                "url": f"https://www.baidu.com/s?wd={title}",
                "fetched_at": now,
            })
        return topics
    except Exception as e:  # noqa: BLE001
        print(f"[hot] 抓取百度热搜失败: {e}")
        return []
