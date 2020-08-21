from datetime import datetime
import re
from typing import Optional, Tuple


URL_RE = r"(https?:\/\/www.redd)(.it|it.com)\/r\/(\w*)\/?(\w*)?"
# group 3 is the sub
# group 4 is either empty or `comments`


# utils
def parse_dt(timestamp: float) -> datetime:
    return datetime.fromtimestamp(timestamp)


def is_post(url: str) -> Tuple[bool, str, Optional[str]]:
    # use regex to extract group 3 (sub) and group 4 ([method]), `True, sub, None` or False, sub, method
    match = re.search(URL_RE, url)
    sub, method = match.groups()[2:]
    if method == 'comments':
        return True, sub, None
    return False, sub, method

