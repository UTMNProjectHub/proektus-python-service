from __future__ import annotations

import re
from typing import List


__all__ = ["RepoLinkExtractor"]

_REPO_HOSTS = r"(?:github\.com|gitlab\.com|bitbucket\.org|sourceforge\.net|gitee\.com|codeberg\.org)"

class RepoLinkExtractor:
    pattern = re.compile(rf"https?://(?:www\.)?{_REPO_HOSTS}/[\w\-./]+", flags=re.I)

    @staticmethod
    def extract(text: str) -> List[str]:
        return RepoLinkExtractor.pattern.findall(text)
