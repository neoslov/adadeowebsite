#!/usr/bin/env python3
"""Link checker for the adadeo.ie static site and the backend /legal/info map.

Validates, in one run:

  1. every HTML page parses, and every internal link resolves to a page that
     exists (and, when the link carries a ``#fragment``, to an element whose
     ``id`` matches it);
  2. the language switch is consistent: one page per language declared in
     ``lang.js``, every ``secye-XX.html`` reachable from every other language
     page, ``<html lang>`` matching ``<body data-page-lang>`` and exactly one
     active link in the header switch;
  3. ``/api/v1/legal/info`` (when ``--api`` is given) maps every supported
     language to a live page and every anchor it appends exists on that page.

Runs against your local checkout by default (fast, catches breakage before
deploying). Add ``--base https://adadeo.ie`` to check the live site instead,
``--api https://api.adadeo.ie`` to also validate the backend map, and
``--check-external`` to additionally verify off-site links respond.

Exit code is 0 when everything is healthy.
"""

import argparse
import json
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

UA = "adadeo-linkcheck/1.0"
TIMEOUT = 20
OFF_SITE = ("index.html", "qa.html")  # non-language pages checked too

SITE_HOSTS = {"adadeo.ie", "www.adadeo.ie"}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.html_lang = None
        self.page_lang = None
        self.ids = set()
        self.links = []            # list of href strings
        self.switch_links = []     # list of (lang, is_active)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html" and "lang" in attrs:
            self.html_lang = attrs["lang"]
        if tag == "body" and "data-page-lang" in attrs:
            self.page_lang = attrs["data-page-lang"]
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a":
            if "href" in attrs:
                self.links.append(attrs["href"])
            if "data-lang-link" in attrs:
                on = "active" in (attrs.get("class") or "").split()
                self.switch_links.append((attrs["data-lang-link"], on))


def load_lang_js(text):
    m = re.search(r"var PAGES\s*=\s*\{(.*?)\};", text, re.S)
    if not m:
        return {}
    return dict(re.findall(r"(\w+)\s*:\s*'([^']+)'", m.group(1)))


def fetch(url):
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read(250_000).decode("utf-8", errors="replace")


class Checker:
    def __init__(self, base, api, check_external, lang_pages):
        self.base = base.rstrip("/") if base else None
        self.api = api.rstrip("/") if api else None
        self.check_external = check_external
        self.lang_pages = lang_pages
        api_host = urlparse(api).netloc.lower().replace("www.", "") if api else ""
        self.allowed_hosts = SITE_HOSTS | ({api_host} if api_host else set())
        self.cache = {}          # page name -> PageParser | None
        self.failures = []
        self.checks = 0

    def note(self, ok, message):
        self.checks += 1
        if not ok:
            self.failures.append(message)

    def load(self, name):
        """name is a page filename relative to the site root."""
        if name in self.cache:
            return self.cache[name]
        if self.base:
            url = f"{self.base}/{name}"
            try:
                text = fetch(url)
                parser = parse_page(text)
            except Exception as exc:
                self.note(False, f"unfetchable {url}: {exc}")
                parser = None
        else:
            if not os.path.exists(name):
                self.note(False, f"missing page {name}")
                parser = None
            else:
                try:
                    with open(name, encoding="utf-8") as fh:
                        parser = parse_page(fh.read())
                except Exception as exc:
                    self.note(False, f"unreadable page {name}: {exc}")
                    parser = None
        self.cache[name] = parser
        return parser

    def page_url(self, name):
        return os.path.join(self.base or "", name) if (self.base and self.base) else name

    def resolve(self, from_url, href):
        """Return (host, page_name, fragment) jellies of a link."""
        full = urljoin(from_url, href)
        parsed = urlparse(full)
        host = parsed.netloc.lower().replace("www.", "")
        name = parsed.path.lstrip("/")
        return host, name, parsed.fragment

    def run(self, page_names):
        for name in page_names:
            self.load(name)

        for name, parser in self.cache.items():
            if parser is None:
                continue
            if parser.html_lang and parser.page_lang:
                self.note(
                    parser.html_lang == parser.page_lang,
                    f"{name}: <html lang=\"{parser.html_lang}\"> mismatch with page-lang {parser.page_lang}",
                )

        # one page per language, no duplicates
        seen_lang = {}
        for name, parser in self.cache.items():
            if parser and parser.page_lang:
                if parser.page_lang in seen_lang:
                    self.note(False, f"duplicate page-lang '{parser.page_lang}': {seen_lang[parser.page_lang]} and {name}")
                seen_lang[parser.page_lang] = name
        for lang, target in self.lang_pages.items():
            self.note(
                seen_lang.get(lang) == target,
                f"lang '{lang}': lang.js says {target}, but site page-lang is {seen_lang.get(lang)}",
            )

        for name, parser in self.cache.items():
            if parser is None:
                continue
            from_url = self.page_url(name)
            for href in parser.links:
                if not href:
                    continue
                if href.startswith("#"):
                    frag = href.lstrip("#")
                    if frag:
                        self.note(
                            frag in parser.ids,
                            f"{name}: anchor #{frag} not on page",
                        )
                    continue
                host, tname, fragment = self.resolve(from_url, href)
                if host not in self.allowed_hosts:
                    if self.check_external and href.startswith("http"):
                        try:
                            req = Request(href, headers={"User-Agent": UA})
                            resp = urlopen(req, timeout=TIMEOUT)
                            status = getattr(resp, "status", resp.getcode())
                            self.note(200 <= status < 400, f"external {name}: {href} -> HTTP {status}")
                        except Exception as exc:
                            self.note(False, f"external {name}: {href} -> unreachable ({exc})")
                    continue
                if not tname:
                    continue  # bare link to the site root
                target = self.load(tname) if tname != name else parser
                if target is None:
                    self.note(False, f"{name}: {href} -> target {tname} unavailable")
                    continue
                if fragment:
                    self.note(fragment in target.ids, f"{name}: #{fragment} not found on {tname}")

        # language-switch consistency across every secye page
        secye = sorted(
            n for n, p in self.cache.items() if p and n.startswith("secye")
        )
        for name in secye:
            parser = self.cache[name]
            switch = dict(parser.switch_links)
            for lang, target in self.lang_pages.items():
                if target == name:
                    self.note(switch.get(lang) is True, f"{name}: no active self-link for '{lang}'")
                else:
                    linked = any(self.resolve(self.page_url(name), h)[1] == target for h in parser.links)
                    self.note(linked, f"{name}: missing link to {target} ('{lang}')")
            active = [lang for lang, on in parser.switch_links if on]
            self.note(len(active) == 1, f"{name}: expected one active switch link, got {active}")

    def check_api(self):
        if not self.api:
            return
        try:
            info = json.loads(fetch(f"{self.api}/api/v1/legal/info"))
        except Exception as exc:
            self.note(False, f"could not fetch /legal/info from {self.api}: {exc}")
            return
        pages = info.get("pages", {})
        for lang in self.lang_pages:
            self.note(lang in pages, f"/legal/info missing language '{lang}' in pages")
        for lang, page in pages.items():
            for anchor in ("privacy", "terms", "healthDisclaimer", "deleteAccount", "support"):
                url = page.get(anchor)
                if not url:
                    self.note(False, f"/legal/info {lang}.{anchor} missing")
                    continue
                host, tname, fragment = self.resolve(url, url)
                text = None
                if not self.base and os.path.exists(tname):
                    with open(tname, encoding="utf-8") as fh:
                        text = fh.read()
                else:
                    try:
                        text = fetch(url)
                    except Exception as exc:
                        self.note(False, f"/legal/info {lang}.{anchor}: unfetchable ({exc})")
                if text is not None:
                    p = parse_page(text) if text else None
                    if p:
                        self.note(fragment in p.ids, f"/legal/info {lang}.{anchor}: #{fragment} not on {tname}")
        for flat in ("privacyPolicyUrl", "termsOfServiceUrl", "healthDisclaimerUrl", "deleteAccountUrl", "supportUrl"):
            self.note(flat in info, f"/legal/info missing legacy field '{flat}'")


def parse_page(text):
    parser = PageParser()
    parser.feed(text)
    return parser


def main():
    ap = argparse.ArgumentParser(description="adadeo.ie link checker")
    ap.add_argument("--base", help="live base URL e.g. https://adadeo.ie (default: local checkout)")
    ap.add_argument("--api", help="backend base URL e.g. https://api.adadeo.ie to validate /legal/info")
    ap.add_argument("--check-external", action="store_true", help="also verify off-site links")
    args = ap.parse_args()

    base = args.base or "https://adadeo.ie"
    try:
        lang_js_text = (
            open("lang.js", encoding="utf-8").read()
            if not args.base
            else fetch(f"{base}/lang.js")
        )
    except Exception as exc:
        sys.exit(f"could not read lang.js: {exc}")
    lang_pages = load_lang_js(lang_js_text)
    if not lang_pages:
        sys.exit("could not parse lang.js PAGES mapping")

    if args.base:
        page_names = sorted(set(OFF_SITE) | set(lang_pages.values()))
    else:
        found = sorted(
            n for n in os.listdir(".")
            if n.endswith(".html") and os.path.isfile(n)
        )
        extra = [n for n in found if n.startswith("secye") and n not in lang_pages.values()]
        missing = [n for n in lang_pages.values() if n not in found]
        for n in extra:
            print(f"warning: {n} not referenced by lang.js")
        for n in missing:
            print(f"warning: lang.js references {n} but it is missing locally")
        page_names = sorted(set(found) | set(lang_pages.values()))

    checker = Checker(args.base, args.api, args.check_external, lang_pages)
    checker.run(page_names)
    checker.check_api()

    print(f"checked {checker.checks} assertions")
    if checker.failures:
        print(f"{len(checker.failures)} problem(s):")
        for f in checker.failures:
            print("  - " + f)
        sys.exit(1)
    print("all links healthy")
    return 0


if __name__ == "__main__":
    sys.exit(main())