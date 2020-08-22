"""
MIT License

Copyright (c) 2020 - sudosnok

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

from datetime import datetime
import re
from typing import Optional, Tuple


URL_RE = r"(https?:\/\/(www.)?redd)(.it|it.com)\/r\/(\w*)\/?(\w*)?"
# group 3 is the sub
# group 4 is either the method, empty or `comments`


def parse_dt(timestamp: float) -> datetime:
    return datetime.fromtimestamp(timestamp)


def is_post(url: str) -> Tuple[bool, str, Optional[str]]:
    # use regex to extract group 3 (sub) and group 4 ([method]), `True, sub, None` or False, sub, method
    match = re.search(URL_RE, url)
    sub, method = match.groups()[3:]
    if method == 'comments':
        return True, sub, None
    return False, sub, method

