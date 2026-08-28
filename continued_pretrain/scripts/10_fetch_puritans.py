#!/usr/bin/env python3
"""
Fetch public-domain Puritan texts into data/puritans/<author>/.

Every download is **title-verified** (must match expected keywords in the first
bytes) before save — Gutenberg/Archive IDs are frequently wrong.

Usage (repo root):
  python continued_pretrain/scripts/10_fetch_puritans.py
  python continued_pretrain/scripts/10_fetch_puritans.py --only owen,watson
  python continued_pretrain/scripts/10_fetch_puritans.py --list
  python continued_pretrain/scripts/10_fetch_puritans.py --wave 3
  python continued_pretrain/scripts/10_fetch_puritans.py --rebuild-mix
      (passes --keep-all-spurgeon --max-other-weight 1.5; prefer the explicit mix command)
"""

from __future__ import annotations

import argparse
import html as html_lib
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


USER_AGENT = "search-sermons-cpt-puritan-fetcher/1.0 (research; public-domain only)"
# Some Archive.org CDN nodes present expired certs; PD research downloads still OK.
SSL_CTX = ssl._create_unverified_context()


def ia_dl(ident: str, name: str | None = None) -> str:
    """Internet Archive item download URL (prefer over /stream/ which returns HTML shells)."""
    fname = name or f"{ident}_djvu.txt"
    return f"https://archive.org/download/{ident}/{fname}"


def pg_txt(gid: str) -> list[str]:
    """Project Gutenberg plain-text URL fallbacks."""
    return [
        f"https://www.gutenberg.org/files/{gid}/{gid}-0.txt",
        f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt",
        f"https://www.gutenberg.org/ebooks/{gid}.txt.utf-8",
    ]


def ccel_cache(letter: str, author: str, work: str) -> str:
    return f"https://ccel.org/ccel/{letter}/{author}/{work}/cache/{work}.txt"


def tcp_xml(ident: str) -> str:
    """EEBO-TCP Phase I TEI XML (public domain) on GitHub."""
    return f"https://raw.githubusercontent.com/textcreationpartnership/{ident}/master/{ident}.xml"


def ota_html(ident: str) -> str:
    """Oxford Text Archive HTML dump of an EEBO-TCP text."""
    return (
        "https://ota.bodleian.ox.ac.uk/repository/xmlui/bitstream/"
        f"handle/20.500.12024/{ident}/{ident}.html?sequence=5&isAllowed=y"
    )


def tcp_urls(ident: str) -> list[str]:
    """Prefer clean TCP transcription over IA OCR (S2: skip IA 403/503)."""
    return [tcp_xml(ident), ota_html(ident)]


BLOCKED_BODY_HOSTS = (
    "banneroftruth.org",
    "heritagebooks.org",
    "puritanpublications.com",
)

# Wave 3: Hodge biblical + selected Calvin commentaries (not the full CCEL dump).
COMMENTARY_CAP_BYTES = 15_000_000


# Verified catalog (title-checked downloads as of 2026-07-13). See data/puritans/PROVENANCE.md.
CATALOG: dict[str, dict] = {
    "owen_mortification": {
        "author": "owen",
        "filename": "mortification_of_sin.txt",
        "title": "Of the Mortification of Sin in Believers (Owen)",
        "urls": [ia_dl("ontemptationmort00owenuoft")],
        "must_match": ["owen", "mortification"],
    },
    "owen_indwelling_sin": {
        "author": "owen",
        "filename": "indwelling_sin.txt",
        "title": "The Nature of Indwelling Sin (Owen)",
        "urls": [ia_dl("naturepowerdecei00owen")],
        "must_match": ["owen", "sin"],
    },
    "owen_glory_of_christ": {
        "author": "owen",
        "filename": "glory_of_christ.txt",
        "title": "Meditations on the Glory of Christ (Owen)",
        "urls": [
            ia_dl(
                "bim_eighteenth-century_meditations-and-discours_owen-john_1790",
                "bim_eighteenth-century_meditations-and-discours_owen-john_1790_djvu.txt",
            )
        ],
        "must_match": ["owen", "glory"],
    },
    "owen_communion": {
        "author": "owen",
        "filename": "communion_with_god.txt",
        "title": "Of Communion with God (Owen)",
        "urls": [
            ia_dl(
                "bim_early-english-books-1475-1640_of-communion-with-god-_owen-john-dd_1700",
                "bim_early-english-books-1475-1640_of-communion-with-god-_owen-john-dd_1700_djvu.txt",
            )
        ],
        "must_match": ["communion"],
    },
    "watson_body_of_divinity": {
        "author": "watson",
        "filename": "body_of_divinity.txt",
        "title": "A Body of Practical Divinity (Watson)",
        "urls": [
            ia_dl("bodyofpracticald00wats"),
            "https://archive.org/stream/bodyofpracticald00wats/bodyofpracticald00wats_djvu.txt",
        ],
        "must_match": ["watson", "divinity"],
    },
    "sibbes_bruised_reed": {
        "author": "sibbes",
        "filename": "bruised_reed.txt",
        "title": "The Bruised Reed (Sibbes) — OCR may spell BRVISED",
        "urls": [
            ia_dl(
                "bim_early-english-books-1475-1640_the-bruised-reed-and-smo_sibbes-richard_1630",
                "bim_early-english-books-1475-1640_the-bruised-reed-and-smo_sibbes-richard_1630_djvu.txt",
            )
        ],
        "must_match_any": ["bruised", "brvised", "reed", "flax"],
        "min_chars": 50_000,
    },
    "brooks_precious_remedies": {
        "author": "brooks",
        "filename": "precious_remedies.txt",
        "title": "Precious Remedies Against Satan's Devices (Brooks)",
        "urls": [ia_dl("preciousremedies0000broo")],
        "must_match": ["brooks", "precious"],
    },
    "brooks_complete_works_v3": {
        "author": "brooks",
        "filename": "complete_works_vol3.txt",
        "title": "Complete Works of Thomas Brooks vol. 3",
        "urls": [ia_dl("completeworksoft03broo_0")],
        "must_match": ["brooks"],
    },
    "baxter_saints_rest": {
        "author": "baxter",
        "filename": "saints_everlasting_rest.txt",
        "title": "The Saints' Everlasting Rest (Baxter)",
        "urls": [ia_dl("saintseverlastin1847baxt")],
        "must_match": ["baxter", "rest"],
    },
    "baxter_reformed_pastor": {
        "author": "baxter",
        "filename": "reformed_pastor.txt",
        "title": "The Reformed Pastor (Baxter)",
        "urls": [
            ia_dl("reformedpastor00baxt"),
            "https://archive.org/stream/reformedpastor00baxt/reformedpastor00baxt_djvu.txt",
        ],
        "must_match": ["baxter"],
    },
    "flavel_providence": {
        "author": "flavel",
        "filename": "mystery_of_providence.txt",
        "title": "Divine Conduct / Mystery of Providence (Flavel)",
        "urls": [
            ia_dl("divineconductorm00flav"),
            "https://archive.org/stream/divineconductorm00flav/divineconductorm00flav_djvu.txt",
        ],
        "must_match": ["flavel", "provid"],
    },
    "flavel_keeping_heart": {
        "author": "flavel",
        "filename": "keeping_the_heart.txt",
        "title": "Keeping the Heart (Flavel)",
        "urls": [
            ia_dl("treatiseonkeepin00flav"),
            "https://archive.org/stream/treatiseonkeepin00flav/treatiseonkeepin00flav_djvu.txt",
        ],
        "must_match": ["flavel", "heart"],
    },
    "edwards_affections": {
        "author": "edwards",
        "filename": "religious_affections.txt",
        "title": "Religious Affections (Edwards)",
        "urls": [ia_dl("treatiseonreligi00edwarich")],
        "must_match_any": ["edwards", "edward", "affection"],
        "min_chars": 100_000,
    },
    # --- Expansion catalog (2026-08-24): verified PD URLs ---
    "watson_all_things_for_good": {
        "author": "watson",
        "filename": "all_things_for_good.txt",
        "title": "A Divine Cordial / All Things for Good (Watson)",
        "urls": ["https://ccel.org/ccel/w/watson/cordial/cache/cordial.txt"],
        "must_match_any": ["watson", "cordial", "romans"],
        "min_chars": 80_000,
    },
    "brooks_mute_christian": {
        "author": "brooks",
        "filename": "mute_christian.txt",
        "title": "The Mute Christian Under the Smarting Rod (Brooks)",
        "urls": [ia_dl("mutechristianun00broo")],
        "must_match": ["brooks", "mute"],
        "min_chars": 80_000,
    },
    "sibbes_souls_conflict": {
        "author": "sibbes",
        "filename": "souls_conflict.txt",
        "title": "The Soul's Conflict with Itself (Sibbes)",
        "urls": [
            ia_dl("soulsconflictwit00sibb"),
            "https://archive.org/stream/soulsconflictwit00sibb/soulsconflictwit00sibb_djvu.txt",
        ],
        "must_match_any": ["sibbes", "soul", "conflict"],
        "min_chars": 100_000,
    },
    "edwards_freedom_of_will": {
        "author": "edwards",
        "filename": "freedom_of_the_will.txt",
        "title": "Freedom of the Will (Edwards)",
        "urls": [
            ia_dl("acarefulandstric00edwauoft"),
            ia_dl("aninquiryintomo01edwagoog"),
        ],
        "must_match_any": ["edwards", "freedom", "will"],
        "min_chars": 200_000,
    },
    "edwards_justification": {
        "author": "edwards",
        "filename": "justification_by_faith_alone.txt",
        "title": "Justification by Faith Alone (Edwards)",
        "urls": ["https://www.biblebb.com/files/edwards/justification.htm"],
        "must_match_any": ["justif", "edwards", "faith"],
        "min_chars": 40_000,
    },
    "charnock_existence_attributes": {
        "author": "charnock",
        "filename": "existence_and_attributes_of_god.txt",
        "title": "Discourses upon the Existence and Attributes of God (Charnock)",
        "urls": [ia_dl("discoursesupone00symigoog")],
        "must_match_any": ["charnock", "existence", "attributes"],
        "min_chars": 500_000,
    },
    "boston_crook_in_lot": {
        "author": "boston",
        "filename": "crook_in_the_lot.txt",
        "title": "The Crook in the Lot (Boston)",
        "urls": [ia_dl("crookinlot00bost")],
        "must_match_any": ["boston", "crook"],
        "min_chars": 80_000,
    },
    "flavel_fountain_of_life": {
        "author": "flavel",
        "filename": "fountain_of_life.txt",
        "title": "The Fountain of Life (Flavel)",
        "urls": [ia_dl("fountainoflifeop00flav")],
        "must_match": ["flavel"],
        "min_chars": 200_000,
    },
    "owen_works_vol10": {
        "author": "owen",
        "filename": "works_vol10.txt",
        "title": "Works of John Owen Vol. 10 (Goold; includes Death of Death)",
        "urls": [ia_dl("worksofjohnowen10owen")],
        "must_match": ["owen"],
        "min_chars": 500_000,
    },
    "henry_exposition_vol5": {
        "author": "henry",
        "filename": "exposition_vol5.txt",
        "title": "Exposition of the Old and New Testament Vol. 5 (Matthew Henry)",
        "urls": [ia_dl("expositionofoldn05henruoft")],
        "must_match_any": ["henry", "exposition", "testament"],
        "min_chars": 500_000,
    },
    "hodge_systematic_vol1": {
        "author": "hodge",
        "filename": "systematic_theology_vol1.txt",
        "title": "Systematic Theology Vol. 1 (Charles Hodge, 1871/72 PD)",
        "urls": [ia_dl("systematictheolo01hodg")],
        "must_match": ["hodge"],
        "min_chars": 400_000,
        "dest_dir": "data/confessions/systematic",
    },
    "gurnall_armour": {
        "author": "gurnall",
        "filename": "christian_in_complete_armour.txt",
        "title": "The Christian in Complete Armour (Gurnall)",
        "urls": [
            ia_dl("christianincom00gurn"),
            "https://archive.org/stream/christianincom00gurn/christianincom00gurn_djvu.txt",
        ],
        "must_match": ["gurnall", "armour"],
    },
    "bunyan_grace_abounding": {
        "author": "bunyan",
        "filename": "grace_abounding.txt",
        "title": "Grace Abounding (Bunyan)",
        "urls": [
            ia_dl("graceaboundingto00buny"),
            "https://archive.org/stream/graceaboundingto00buny/graceaboundingto00buny_djvu.txt",
        ],
        "must_match": ["bunyan", "grace"],
    },
}


def _owen_goold_urls(vol: int) -> list[str]:
    nn = f"{vol:02d}"
    idents = [
        f"worksofjohnowen{nn}owen",
        f"worksofjohnowen{vol}owen",
        f"worksofjohnowe1850{nn}owen",
        f"worksofjohnowe1850{vol}owen",
    ]
    seen: set[str] = set()
    urls: list[str] = []
    for ident in idents:
        if ident in seen:
            continue
        seen.add(ident)
        urls.append(ia_dl(ident))
    return urls


def _wave1_catalog() -> dict[str, dict]:
    """CPT corpus v3 Wave 1 — unique PD treatises/sermons/hymns (not Henry commentary)."""
    out: dict[str, dict] = {}

    # Goold Works: skip vol.2 (Communion), vol.6 (Mortification/Indwelling), vol.10 (on disk).
    # Skip 17–24 (Hebrews commentary). Vol.1 has Christologia plus Glory of Christ.
    for n in range(1, 17):
        if n in {2, 6, 10}:
            continue
        out[f"owen_works_vol{n:02d}"] = {
            "author": "owen",
            "filename": f"works_vol{n:02d}.txt",
            "title": f"Works of John Owen (Goold) vol. {n}",
            "urls": _owen_goold_urls(n),
            "must_match": ["owen"],
            "min_chars": 200_000,
            "wave": 1,
        }

    for n in range(1, 23):
        nn = f"{n:02d}"
        out[f"manton_works_vol{nn}"] = {
            "author": "manton",
            "filename": f"works_vol{nn}.txt",
            "title": f"Complete Works of Thomas Manton vol. {n}",
            "urls": [
                ccel_cache("m", "manton", f"manton{nn}"),
                f"https://www.ccel.org/ccel/m/manton/manton{nn}/cache/manton{nn}.txt",
                # Vols 12 and 22 live under completeworkoft* (no 's'), not completeworksoft*.
                ia_dl(f"completeworkoft{nn}mantuoft"),
                ia_dl(f"completeworkoft{n}mantuoft"),
                ia_dl(f"completeworksoft{nn}mantuoft"),
                ia_dl(f"completeworksoft{n}mantuoft"),
            ],
            "must_match_any": ["manton", "sermon"],
            "min_chars": 80_000,
            "wave": 1,
        }

    out.update(
        {
            "edwards_original_sin": {
                "author": "edwards",
                "filename": "original_sin.txt",
                "title": "The Great Christian Doctrine of Original Sin Defended (Edwards)",
                "urls": [
                    ia_dl("greatchristiando1758edwa"),
                    ia_dl("worksofpresident06edwa"),
                    ia_dl("originalsinorcor00edwarich"),
                ],
                "must_match_any": ["edwards", "original sin", "original"],
                "min_chars": 150_000,
                "wave": 1,
            },
            "edwards_history_redemption": {
                "author": "edwards",
                "filename": "history_of_redemption.txt",
                "title": "A History of the Work of Redemption (Edwards)",
                "urls": [
                    ia_dl("worksofpresident02edwa"),
                    ia_dl("historyofworkofre00edwa"),
                    ia_dl("historyofredempt00edwa"),
                    ia_dl("historyofredempt00edwarich"),
                ],
                "must_match_any": ["edwards", "redemption"],
                "min_chars": 150_000,
                "wave": 1,
            },
            "edwards_distinguishing_marks": {
                "author": "edwards",
                "filename": "distinguishing_marks.txt",
                "title": "Distinguishing Marks of a Work of the Spirit of God (Edwards)",
                "urls": [
                    ia_dl("worksofpresident03edwa"),
                    ia_dl("distinguishingmar00edwa"),
                    ia_dl(
                        "bim_eighteenth-century_the-distinguishing-marks_edwards-jonathan_1742_0"
                    ),
                ],
                "must_match_any": ["edwards", "distinguishing", "revival", "spirit"],
                "min_chars": 40_000,
                "wave": 1,
            },
            "edwards_sermons_vol7": {
                "author": "edwards",
                "filename": "sermons_worcester_vol7.txt",
                "title": "Works of President Edwards vol. 7 (Worcester sermons)",
                "urls": [ia_dl("worksofpresident07edwa")],
                "must_match_any": ["edwards", "sermon"],
                "min_chars": 150_000,
                "wave": 1,
            },
            "edwards_sermons_vol8": {
                "author": "edwards",
                "filename": "sermons_worcester_vol8.txt",
                "title": "Works of President Edwards vol. 8 (Worcester sermons)",
                "urls": [ia_dl("worksofpresident08edwa")],
                "must_match_any": ["edwards", "sermon"],
                "min_chars": 150_000,
                "wave": 1,
            },
            "calvin_christian_life": {
                "author": "calvin",
                "filename": "on_the_christian_life.txt",
                "title": "On the Christian Life (Calvin; Beveridge)",
                "urls": [
                    ccel_cache("c", "calvin", "chr_life"),
                    "https://www.ccel.org/ccel/c/calvin/chr_life/cache/chr_life.txt",
                ],
                "must_match_any": ["calvin", "christian life", "self-denial"],
                "min_chars": 20_000,
                "wave": 1,
            },
            "calvin_tracts_vol1": {
                "author": "calvin",
                "filename": "tracts_vol1.txt",
                "title": "Calvin Tracts relating to the Reformation vol. 1 (CTS/Beveridge)",
                "urls": [
                    ia_dl("tractsre01calvuoft"),
                    ia_dl("tractsofcalvin01calvuoft"),
                ],
                "must_match_any": ["calvin", "reformation", "tract"],
                "min_chars": 80_000,
                "wave": 1,
            },
            "calvin_tracts_vol2": {
                "author": "calvin",
                "filename": "tracts_vol2.txt",
                "title": "Calvin Tracts vol. 2 (sacraments / treatises)",
                "urls": [
                    ia_dl("tractsre02calvuoft"),
                    ia_dl("tractsofcalvin02calvuoft"),
                ],
                "must_match_any": ["calvin", "sacrament", "tract"],
                "min_chars": 80_000,
                "wave": 1,
            },
            "calvin_tracts_vol3": {
                "author": "calvin",
                "filename": "tracts_vol3.txt",
                "title": "Calvin Tracts vol. 3 (Trent antidote, Psychopannychia)",
                "urls": [
                    ia_dl("tractsre03calvuoft"),
                    ia_dl("tractsofcalvin03calvuoft"),
                ],
                "must_match_any": ["calvin", "trent", "psychopannychia", "tract"],
                "min_chars": 80_000,
                "wave": 1,
            },
            "herbert_temple": {
                "author": "herbert",
                "filename": "the_temple.txt",
                "title": "The Temple (George Herbert)",
                "urls": [
                    ia_dl("temple00herb"),
                    "https://ccel.org/ccel/herbert/temple/cache/temple.txt",
                    ccel_cache("h", "herbert", "temple"),
                    "https://www.ccel.org/ccel/h/herbert/temple/cache/temple.txt",
                ],
                "must_match_any": ["herbert", "temple", "church porch", "easter wings"],
                "min_chars": 15_000,
                "wave": 1,
            },
            "herbert_country_parson": {
                "author": "herbert",
                "filename": "country_parson.txt",
                "title": "A Priest to the Temple / The Country Parson (Herbert)",
                "urls": [
                    ccel_cache("h", "herbert", "temple2"),
                    "https://www.ccel.org/ccel/h/herbert/temple2/cache/temple2.txt",
                    "https://ccel.org/ccel/herbert/temple2/cache/temple2.txt",
                    ia_dl("priesttothetemple00herb"),
                    ia_dl("apriesttothetem00herb"),
                ],
                "must_match_any": ["herbert", "parson", "priest to the temple", "country parson"],
                "min_chars": 15_000,
                "wave": 1,
            },
            "watts_hymns_spiritual_songs": {
                "author": "watts",
                "filename": "hymns_and_spiritual_songs.txt",
                "title": "Hymns and Spiritual Songs (Isaac Watts)",
                "urls": pg_txt("13341"),
                "must_match_any": ["watts", "hymn", "spiritual songs"],
                "min_chars": 30_000,
                "dest_dir": "data/hymns",
                "wave": 1,
            },
            "olney_hymns": {
                "author": "newton",
                "filename": "olney_hymns.txt",
                "title": "Olney Hymns (Newton / Cowper)",
                "urls": [
                    ccel_cache("n", "newton", "olneyhymns"),
                    "https://www.ccel.org/ccel/n/newton/olneyhymns/cache/olneyhymns.txt",
                    ia_dl("olneyhymnsinthree00newt"),
                    ia_dl("olneyhymns00newt"),
                ],
                "must_match_any": ["olney", "newton", "cowper", "amazing grace"],
                "min_chars": 30_000,
                "dest_dir": "data/hymns",
                "wave": 1,
            },
            "scottish_psalter_1650": {
                "author": "psalter",
                "filename": "scottish_psalter_1650.txt",
                "title": "Psalms of David in Metre (Scottish Psalter 1650)",
                "urls": [
                    "https://www.ccel.org/ccel/a/anonymous/scotpsalter/cache/scotpsalter.txt",
                    ccel_cache("a", "anonymous", "scotpsalter"),
                    ia_dl("psalmsofdavidinm00scot"),
                    ia_dl("psalmsofdavidinme00chur"),
                    ia_dl("thepsalmsofdavidi00scot"),
                    ia_dl("psalmsofdavidinmetre00unkn"),
                    ia_dl("psalmsofdavidinm1850scot"),
                    ia_dl("scottishpsalter00unkn"),
                ],
                "must_match_any": ["psalm", "metre", "meter", "david"],
                "min_chars": 40_000,
                "dest_dir": "data/hymns",
                "wave": 1,
            },
            "rutherford_letters": {
                "author": "rutherford",
                "filename": "letters.txt",
                "title": "Letters of Samuel Rutherford (Bonar ed., PG 42557)",
                "urls": pg_txt("42557"),
                "must_match_any": ["rutherford", "anwoth", "kenmure"],
                "min_chars": 80_000,
                "wave": 1,
            },
            "rutherford_lex_rex": {
                "author": "rutherford",
                "filename": "lex_rex.txt",
                "title": "Lex, Rex (Samuel Rutherford)",
                "urls": [
                    ia_dl("lexrexorlawprinc00ruth"),
                    ia_dl("lexrexlawandpri00maxwgoog"),
                    ia_dl("lexrexorlawandp00ruthgoog"),
                    ia_dl("lexrex00ruth"),
                    ia_dl("lexrexoraprincip00ruth"),
                ],
                "must_match_any": ["rutherford", "lex", "rex"],
                "min_chars": 80_000,
                "wave": 1,
            },
            "alleine_alarm": {
                "author": "alleine",
                "filename": "alarm_to_the_unconverted.txt",
                "title": "An Alarm to the Unconverted (Joseph Alleine)",
                "urls": [
                    ccel_cache("a", "alleine", "alarm"),
                    "https://www.ccel.org/ccel/a/alleine/alarm/cache/alarm.txt",
                    ia_dl("alarmtounconvert00alle"),
                    ia_dl("analarmtounconve00alle"),
                ],
                "must_match_any": ["alleine", "unconverted", "alarm", "conversion"],
                "min_chars": 30_000,
                "wave": 1,
            },
            "bayly_practice_of_piety": {
                "author": "bayly",
                "filename": "practice_of_piety.txt",
                "title": "The Practice of Piety (Lewis Bayly)",
                "urls": [
                    ia_dl("practiceofpiety00bayl"),
                    ia_dl("practiceofpietie00bayl"),
                    ia_dl("thepracticeofpie00bayl"),
                    ccel_cache("b", "bayly", "piety"),
                ],
                "must_match_any": ["bayly", "piety", "practise of piety", "practice of piety"],
                "min_chars": 50_000,
                "wave": 1,
            },
            "burroughs_rare_jewel": {
                "author": "burroughs",
                "filename": "rare_jewel_of_christian_contentment.txt",
                "title": "The Rare Jewel of Christian Contentment (Burroughs)",
                "urls": [
                    *tcp_urls("A30598"),
                    *tcp_urls("A77996"),
                    ia_dl("rarejewelofchris00burr"),
                    ia_dl("rarejewelofchris00burrgoog"),
                    ia_dl("therarejewelofch00burr"),
                    ia_dl("rarejewelofchristian00burr"),
                    ia_dl("therarejewelofchristian00burr"),
                ],
                "must_match_any": ["burroughs", "contentment", "jewel"],
                "min_chars": 80_000,
                "wave": 1,
            },
            "burroughs_gospel_worship": {
                "author": "burroughs",
                "filename": "gospel_worship.txt",
                "title": "Gospel Worship (Jeremiah Burroughs)",
                "urls": [
                    *tcp_urls("A30585"),
                    *tcp_urls("A77988"),
                    ia_dl("gospelworshipor00burr"),
                    ia_dl("gospelworshipor00burrgoog"),
                    ia_dl("gospelworship00burr"),
                ],
                "must_match_any": ["burroughs", "worship", "gospel"],
                "min_chars": 80_000,
                "wave": 1,
            },
            "perkins_golden_chain": {
                "author": "perkins",
                "filename": "golden_chain.txt",
                "title": "A Golden Chain (William Perkins)",
                "urls": [
                    *tcp_urls("A09339"),
                    ia_dl("goldenchaineorde00perk"),
                    ia_dl("goldenchaineor00perk"),
                    ia_dl("agoldenchaineor00perk"),
                    ia_dl("goldenchaine00perk"),
                    ia_dl("workesofthatfamo00perk"),
                    ia_dl("workesofthatfamous00perk"),
                    ia_dl("agoldenchaine00perk"),
                ],
                "must_match_any": ["perkins", "golden", "chaine", "chain"],
                "min_chars": 40_000,
                "wave": 1,
            },
            "perkins_cases_conscience": {
                "author": "perkins",
                "filename": "cases_of_conscience.txt",
                "title": "Cases of Conscience (William Perkins)",
                "urls": [
                    *tcp_urls("A09365"),
                    ia_dl("casesofconscienc00perk"),
                    ia_dl("thewholetreatise00perk"),
                    ia_dl("wholetreatiseofc00perk"),
                ],
                "must_match_any": ["perkins", "conscience"],
                "min_chars": 40_000,
                "wave": 1,
            },
            "watson_godly_mans_picture": {
                "author": "watson",
                "filename": "godly_mans_picture.txt",
                "title": "The Godly Man's Picture (Thomas Watson)",
                "urls": [
                    *tcp_urls("A65296"),
                    ccel_cache("w", "watson", "godly"),
                    ccel_cache("w", "watson", "picture"),
                    ia_dl("godlymanspicture00wats"),
                    ia_dl("thegodlymanspict00wats"),
                    ia_dl("godlymanspictur00wats"),
                    ia_dl("thegodlymanspicture00wats"),
                ],
                "must_match_any": ["watson", "godly"],
                "min_chars": 50_000,
                "wave": 1,
            },
            "watson_beatitudes": {
                "author": "watson",
                "filename": "beatitudes.txt",
                "title": "The Beatitudes (Thomas Watson)",
                "urls": [
                    ia_dl("beatitudesor00wats"),
                    ia_dl("thebeatitudes00wats"),
                    ia_dl("beatitudes00wats"),
                    ccel_cache("w", "watson", "beatitudes"),
                ],
                "must_match_any": ["watson", "beatitude", "blessed"],
                "min_chars": 50_000,
                "wave": 1,
            },
            "boston_fourfold_state": {
                "author": "boston",
                "filename": "fourfold_state.txt",
                "title": "Human Nature in its Fourfold State (Thomas Boston)",
                "urls": [
                    ia_dl("humannaturein00bost"),
                    ia_dl("humannatureinits02bost"),
                    ia_dl("fourfoldstateofh00bost"),
                ],
                "must_match_any": ["boston", "fourfold", "four-fold", "human nature"],
                "min_chars": 80_000,
                "wave": 1,
            },
            "hodge_systematic_vol2": {
                "author": "hodge",
                "filename": "systematic_theology_vol2.txt",
                "title": "Systematic Theology Vol. 2 (Charles Hodge)",
                "urls": [ia_dl("systematictheolo02hodg"), ia_dl("systematicth02hodg")],
                "must_match": ["hodge"],
                "min_chars": 400_000,
                "dest_dir": "data/confessions/systematic",
                "wave": 1,
            },
            "hodge_systematic_vol3": {
                "author": "hodge",
                "filename": "systematic_theology_vol3.txt",
                "title": "Systematic Theology Vol. 3 (Charles Hodge)",
                "urls": [ia_dl("systematictheolo03hodg"), ia_dl("systematicth03hodg")],
                "must_match": ["hodge"],
                "min_chars": 400_000,
                "dest_dir": "data/confessions/systematic",
                "wave": 1,
            },
            "henry_method_of_prayer": {
                "author": "henry",
                "filename": "method_of_prayer.txt",
                "title": "A Method for Prayer (Matthew Henry) — not commentary",
                "urls": [
                    ccel_cache("h", "henry", "method"),
                    ccel_cache("h", "henry", "prayer"),
                    ia_dl("a587258300henruoft"),
                    ia_dl("adirectmethodofp00henr"),
                    ia_dl("methodofprayer00henry"),
                    ia_dl("methodforprayer00henr"),
                    ia_dl("amethodforprayer00henr"),
                ],
                "must_match_any": ["henry", "prayer"],
                "min_chars": 20_000,
                "wave": 1,
            },
            "henry_communicants_companion": {
                "author": "henry",
                "filename": "communicants_companion.txt",
                "title": "The Communicant's Companion (Matthew Henry) — not commentary",
                "urls": [
                    ia_dl("thecommunicantsco00henr"),
                    ia_dl("communicantscomp00henr"),
                    ia_dl("communicantscomp00henry"),
                ],
                "must_match_any": ["henry", "communicant", "supper", "sacrament"],
                "min_chars": 20_000,
                "wave": 1,
            },
        }
    )

    for n in (1, 2, 4, 5, 6):
        urls = [ia_dl(f"completeworksoft{n:02d}broo"), ia_dl(f"completeworksoft{n:02d}broo_0")]
        if n != 3:
            urls.append(ia_dl(f"completeworksoft{n}broo"))
        out[f"brooks_works_vol{n:02d}"] = {
            "author": "brooks",
            "filename": f"complete_works_vol{n}.txt",
            "title": f"Complete Works of Thomas Brooks vol. {n}",
            "urls": urls,
            "must_match": ["brooks"],
            "min_chars": 150_000,
            "wave": 1,
        }

    for n in range(1, 7):
        out[f"flavel_works_vol{n:02d}"] = {
            "author": "flavel",
            "filename": f"works_vol{n:02d}.txt",
            "title": f"Works of John Flavel vol. {n}",
            "urls": [
                ia_dl(f"wholeworksofjohn{n:02d}flav"),
                ia_dl(f"wholeworksofjohn{n}flav"),
                ia_dl(
                    f"bim_eighteenth-century_the-whole-works-of-the-r_flavel-john_1701_{n}",
                    f"bim_eighteenth-century_the-whole-works-of-the-r_flavel-john_1701_{n}_djvu.txt",
                ),
                ia_dl(f"worksofjohnflave{n:02d}flav"),
                ia_dl(f"theworksofjohnfla{n:02d}flav"),
                ia_dl(f"wholeworksoftherev{n:02d}flav"),
                ia_dl(f"wholeworksofreve{n:02d}flav"),
                ia_dl(f"worksofrevdjohnf{n:02d}flav"),
                ia_dl(f"thewholeworksof{n:02d}flav"),
            ],
            "must_match": ["flavel"],
            "min_chars": 150_000,
            "wave": 1,
        }

    for n in range(1, 8):
        out[f"sibbes_works_vol{n:02d}"] = {
            "author": "sibbes",
            "filename": f"works_vol{n:02d}.txt",
            "title": f"Complete Works of Richard Sibbes vol. {n}",
            "urls": [
                ia_dl(f"completeworksofri{n:02d}sibb"),
                ia_dl(f"completeworksofr{n:02d}sibb"),
                ia_dl(f"thecompleteworkso{n:02d}sibb"),
                ia_dl(f"worksofrichardsib{n:02d}sibb"),
            ],
            "must_match_any": ["sibbes", "sibbs"],
            "min_chars": 80_000,
            "wave": 1,
        }

    for n in range(1, 5):
        out[f"goodwin_works_vol{n:02d}"] = {
            "author": "goodwin",
            "filename": f"works_vol{n:02d}.txt",
            "title": f"Works of Thomas Goodwin vol. {n}",
            "urls": [
                ia_dl(f"worksofthomasgoo{n:02d}good"),
                ia_dl(f"theworksofthomasg{n:02d}good"),
                ia_dl(f"worksofthomasgoodwin{n:02d}good"),
            ],
            "must_match": ["goodwin"],
            "min_chars": 80_000,
            "wave": 1,
        }

    return out


def _wave2_catalog() -> dict[str, dict]:
    """CPT corpus v3 Wave 2 — named Puritans, PD treatises/sermons (not shop bodies)."""
    return {
        "bridge_lifting_up": {
            "author": "bridge",
            "filename": "lifting_up_for_the_downcast.txt",
            "title": "A Lifting Up for the Downcast (William Bridge)",
            "urls": [
                ia_dl("theworksoftherev02briduoft"),
                ia_dl("worksofrevwillia02brid"),
                ia_dl("worksofrevwilliam02brid"),
                *tcp_urls("A29371"),
            ],
            "must_match_any": ["bridge", "downcast", "lifting"],
            "min_chars": 40_000,
            "wave": 2,
        },
        "ames_marrow": {
            "author": "ames",
            "filename": "marrow_of_sacred_divinity.txt",
            "title": "The Marrow of Sacred Divinity (William Ames)",
            "urls": [*tcp_urls("A25291"), ia_dl("marrowsacdi00ames")],
            "must_match_any": ["ames", "marrow", "divinity"],
            "min_chars": 40_000,
            "wave": 2,
        },
        "howe_blessedness": {
            "author": "howe",
            "filename": "blessedness_of_the_righteous.txt",
            "title": "The Blessedness of the Righteous (John Howe)",
            "urls": [*tcp_urls("A44666")],
            "must_match_any": ["howe", "blessed", "righteous"],
            "min_chars": 40_000,
            "wave": 2,
        },
        "william_gouge_domestical": {
            "author": "william_gouge",
            "filename": "of_domestical_duties.txt",
            "title": "Of Domestical Duties (William Gouge)",
            "urls": [*tcp_urls("A68107")],
            "must_match_any": ["gouge", "domestic", "duties"],
            "min_chars": 40_000,
            "wave": 2,
        },
        "hooker_poor_doubting": {
            "author": "hooker",
            "filename": "poor_doubting_christian.txt",
            "title": "The Poor Doubting Christian / Soul's Preparation (Thomas Hooker)",
            "urls": [
                *tcp_urls("N04231"),
                *tcp_urls("A03611"),
                ia_dl("poordoubtingchri00hook"),
            ],
            "must_match_any": ["hooker", "doubting", "contrition", "soules preparation"],
            "min_chars": 20_000,
            "wave": 2,
        },
        "shepard_sincere_convert": {
            "author": "shepard",
            "filename": "sincere_convert.txt",
            "title": "The Sincere Convert (Thomas Shepard)",
            "urls": [*tcp_urls("A59669")],
            "must_match_any": ["shepard", "sincere", "convert"],
            "min_chars": 30_000,
            "wave": 2,
        },
        "shepard_sound_believer": {
            "author": "shepard",
            "filename": "sound_believer.txt",
            "title": "The Sound Believer (Thomas Shepard)",
            "urls": [*tcp_urls("N04105"), ia_dl("soundbelievertre00shep")],
            "must_match_any": ["shepard", "believer", "evangelical"],
            "min_chars": 20_000,
            "wave": 2,
        },
        "cotton_milk_for_babes": {
            "author": "cotton",
            "filename": "milk_for_babes.txt",
            "title": "Milk for Babes (John Cotton)",
            "urls": [*tcp_urls("A80625")],
            "must_match_any": ["cotton", "milk", "babes"],
            "min_chars": 3_000,
            "wave": 2,
        },
        "cotton_keys": {
            "author": "cotton",
            "filename": "keys_of_the_kingdom.txt",
            "title": "The Keys of the Kingdom of Heaven (John Cotton)",
            "urls": [*tcp_urls("A34678")],
            "must_match_any": ["cotton", "keys", "kingdom", "church"],
            "min_chars": 8_000,
            "wave": 2,
        },
        "richard_mather_covenant": {
            "author": "richard_mather",
            "filename": "church_covenant.txt",
            "title": "Church-Covenant (Richard Mather)",
            "urls": [*tcp_urls("A50245")],
            "must_match_any": ["mather", "covenant", "church"],
            "min_chars": 10_000,
            "wave": 2,
        },
        "increase_mather_providences": {
            "author": "increase_mather",
            "filename": "illustrious_providences.txt",
            "title": "Illustrious Providences (Increase Mather)",
            "urls": [*tcp_urls("A50202")],
            "must_match_any": ["mather", "providence"],
            "min_chars": 20_000,
            "wave": 2,
        },
        "cotton_mather_bonifacius": {
            "author": "cotton_mather",
            "filename": "bonifacius_essays_to_do_good.txt",
            "title": "Bonifacius / Essays to Do Good (Cotton Mather) — sample, not Magnalia dump",
            "urls": [
                *pg_txt("26879"),
                *tcp_urls("N01847"),
                ia_dl("bonifaciusessay00math"),
            ],
            "must_match_any": ["mather", "bonifacius", "do good", "essays"],
            "min_chars": 15_000,
            "wave": 2,
        },
        "winthrop_journal": {
            "author": "winthrop",
            "filename": "journal.txt",
            "title": "Winthrop's Journal / History of New England (small historical slice)",
            "urls": [
                *pg_txt("18787"),
                *pg_txt("9701"),
                ia_dl("winthropsjournal00wint"),
            ],
            "must_match_any": ["winthrop", "massachusetts", "arbella", "new england"],
            "min_chars": 15_000,
            "wave": 2,
        },
        "bradstreet_poems": {
            "author": "bradstreet",
            "filename": "poems.txt",
            "title": "Poems of Anne Bradstreet",
            "urls": [
                *pg_txt("43739"),
                ia_dl("worksofannebrads00brad"),
                ia_dl("poemsmrsannebra00hopkgoog"),
            ],
            "must_match_any": ["bradstreet", "tenth muse", "contemplations"],
            "min_chars": 8_000,
            "wave": 2,
        },
        "bolton_true_bounds": {
            "author": "bolton",
            "filename": "true_bounds_of_christian_freedom.txt",
            "title": "The True Bounds of Christian Freedom (Samuel Bolton)",
            "urls": [*tcp_urls("A76991")],
            "must_match_any": ["bolton", "bounds", "freedome", "freedom"],
            "min_chars": 20_000,
            "wave": 2,
        },
        "love_effectual_calling": {
            "author": "love",
            "filename": "effectual_calling.txt",
            "title": "Effectual Calling and Election (Christopher Love)",
            "urls": [*tcp_urls("A49258"), *tcp_urls("A49244")],
            "must_match_any": ["love", "calling", "election", "grace"],
            "min_chars": 20_000,
            "wave": 2,
        },
        "burgess_spiritual_refining": {
            "author": "burgess",
            "filename": "spiritual_refining.txt",
            "title": "Spiritual Refining (Anthony Burgess)",
            "urls": [*tcp_urls("A30243")],
            "must_match_any": ["burgess", "refining", "assurance"],
            "min_chars": 40_000,
            "wave": 2,
        },
        "sedgwick_secret_sins": {
            "author": "sedgwick",
            "filename": "anatomy_of_secret_sins.txt",
            "title": "The Anatomy of Secret Sins / Doubting Believer (Obadiah Sedgwick)",
            "urls": [*tcp_urls("A92846"), *tcp_urls("A59036")],
            "must_match_any": ["sedgwick", "secret", "doubting"],
            "min_chars": 20_000,
            "wave": 2,
        },
        "byfield_marrow_oracles": {
            "author": "byfield",
            "filename": "marrow_of_the_oracles.txt",
            "title": "The Marrow of the Oracles of God (Nicholas Byfield)",
            "urls": [*tcp_urls("A17397")],
            "must_match_any": ["byfield", "marrow", "oracles"],
            "min_chars": 20_000,
            "wave": 2,
        },
        "mead_almost_christian": {
            "author": "mead",
            "filename": "almost_christian_discovered.txt",
            "title": "The Almost Christian Discovered (Matthew Mead)",
            "urls": [
                ccel_cache("m", "mead_matthew", "almost"),
                "https://www.ccel.org/ccel/m/mead_matthew/almost/cache/almost.txt",
                ccel_cache("m", "mead", "almost"),
                *tcp_urls("A50480"),
            ],
            "must_match_any": ["mead", "almost christian", "hypocrite"],
            "min_chars": 20_000,
            "wave": 2,
        },
        "arrowsmith_armilla": {
            "author": "arrowsmith",
            "filename": "armilla_catechetica.txt",
            "title": "Armilla Catechetica (John Arrowsmith)",
            "urls": [*tcp_urls("A75616")],
            "must_match_any": ["arrowsmith", "armilla", "chain of principles"],
            "min_chars": 20_000,
            "wave": 2,
        },
        "hildersham_fasting": {
            "author": "hildersham",
            "filename": "doctrine_of_fasting.txt",
            "title": "The Doctrine of Fasting and Prayer (Arthur Hildersam)",
            "urls": [*tcp_urls("A03339")],
            "must_match_any": ["hildersam", "hildersham", "fasting"],
            "min_chars": 10_000,
            "wave": 2,
        },
        "fenner_riches_of_grace": {
            "author": "fenner",
            "filename": "riches_of_grace.txt",
            "title": "The Riches of Grace (William Fenner)",
            "urls": [*tcp_urls("A41124"), *tcp_urls("A41118")],
            "must_match_any": ["fenner", "grace"],
            "min_chars": 15_000,
            "wave": 2,
        },
        "reynolds_passions": {
            "author": "reynolds",
            "filename": "treatise_of_the_passions.txt",
            "title": "A Treatise of the Passions (Edward Reynolds)",
            "urls": [*tcp_urls("A10663")],
            "must_match_any": ["reynolds", "passions", "soule", "soul"],
            "min_chars": 30_000,
            "wave": 2,
        },
        "richard_rogers_seven": {
            "author": "richard_rogers",
            "filename": "seven_treatises.txt",
            "title": "Seven Treatises (Richard Rogers)",
            "urls": [*tcp_urls("A10945")],
            "must_match_any": ["rogers", "treatises", "direction"],
            "min_chars": 30_000,
            "wave": 2,
        },
        "dod_sermons": {
            "author": "dod",
            "filename": "godly_sermons.txt",
            "title": "Godly and Fruitful Sermons (John Dod / Robert Cleaver)",
            "urls": [*tcp_urls("A20529")],
            "must_match_any": ["dod", "cleaver"],
            "min_chars": 10_000,
            "wave": 2,
        },
        "baynes_trial": {
            "author": "baynes",
            "filename": "trial_of_a_christians_estate.txt",
            "title": "The Trial of a Christian's Estate (Paul Baynes)",
            "urls": [*tcp_urls("A06065"), *tcp_urls("A05962")],
            "must_match_any": ["bayne", "christian"],
            "min_chars": 8_000,
            "wave": 2,
        },
        "greenham_works": {
            "author": "greenham",
            "filename": "works.txt",
            "title": "Works of Richard Greenham",
            "urls": [*tcp_urls("A02178")],
            "must_match_any": ["greenham"],
            "min_chars": 30_000,
            "wave": 2,
        },
        "whitaker_holy_scripture": {
            "author": "whitaker",
            "filename": "disputation_on_holy_scripture.txt",
            "title": "A Disputation on Holy Scripture (William Whitaker)",
            "urls": [
                *tcp_urls("A15057"),
                ia_dl("disputationonhol00whit"),
                ia_dl("adisputationonho00whituoft"),
            ],
            "must_match_any": ["whitaker", "scripture", "campian", "campion"],
            "min_chars": 20_000,
            "wave": 2,
        },
        "cartwright_helps": {
            "author": "cartwright",
            "filename": "helps_for_discovery.txt",
            "title": "Helps for Discovery of the Truth (Thomas Cartwright)",
            "urls": [*tcp_urls("A80850")],
            "must_match_any": ["cartwright", "toleration"],
            "min_chars": 5_000,
            "wave": 2,
        },
        "thomas_gouge_thriving": {
            "author": "thomas_gouge",
            "filename": "surest_and_safest_way_of_thriving.txt",
            "title": "The Surest and Safest Way of Thriving (Thomas Gouge)",
            "urls": [*tcp_urls("A41657")],
            "must_match_any": ["gouge", "thriving"],
            "min_chars": 8_000,
            "wave": 2,
        },
        "shepard_jr_if_found": {
            "author": "shepard_jr",
            "filename": "unconquerable_soldier.txt",
            "title": "Shepard Jr. PD if found (Oakes funeral mentioning Shepard Jr.)",
            "urls": [*tcp_urls("A53292")],
            "must_match_any": ["shepard"],
            "min_chars": 5_000,
            "wave": 2,
        },
    }


def _wave3_catalog() -> dict[str, dict]:
    """CPT corpus v3 Wave 3 — capped old commentary only.

    Chaderton and John Rogers: skip (no clean PD keyed here; do not force OCR).
    Do not add Henry exposition. Treatise mass stays at Wave 1–2.
    Combined dest size is gated at COMMENTARY_CAP_BYTES (15 MB).
    """
    cap = 3_500_000  # per-file ceiling so one dump cannot eat the combined cap
    return {
        "hodge_commentary_romans": {
            "author": "hodge",
            "filename": "commentary_romans.txt",
            "title": "Commentary on the Epistle to the Romans (Charles Hodge, 1871 PD)",
            "urls": [
                ia_dl("commentaryepist00hodg"),
                ia_dl("commentaryon1873hodg"),
                ia_dl("commentaryonepis00hodg"),
                ia_dl("commentaryone00hodg"),
            ],
            "must_match": ["hodge"],
            "must_match_any": ["romans"],
            "min_chars": 200_000,
            "max_chars": cap,
            "kind": "commentary",
            "wave": 3,
        },
        "hodge_commentary_1cor": {
            "author": "hodge",
            "filename": "commentary_1corinthians.txt",
            "title": "Exposition of the First Epistle to the Corinthians (Charles Hodge)",
            "urls": [
                ia_dl("expositionoffirs00hodg"),
                ia_dl("expositionoffi00hodg"),
            ],
            "must_match": ["hodge"],
            "must_match_any": ["corinth"],
            "min_chars": 150_000,
            "max_chars": cap,
            "kind": "commentary",
            "wave": 3,
        },
        "hodge_commentary_2cor": {
            "author": "hodge",
            "filename": "commentary_2corinthians.txt",
            "title": "Exposition of the Second Epistle to the Corinthians (Charles Hodge)",
            "urls": [
                ia_dl("expositionofseco00hodg"),
                ia_dl("expositionofseco00hodgrich"),
            ],
            "must_match": ["hodge"],
            "must_match_any": ["corinth"],
            "min_chars": 80_000,
            "max_chars": cap,
            "kind": "commentary",
            "wave": 3,
        },
        "hodge_commentary_ephesians": {
            "author": "hodge",
            "filename": "commentary_ephesians.txt",
            "title": "Commentary on the Epistle to the Ephesians (Charles Hodge)",
            "urls": [
                ccel_cache("h", "hodge", "ephesians"),
                "https://www.ccel.org/ccel/h/hodge/ephesians/cache/ephesians.txt",
            ],
            "must_match": ["hodge"],
            "must_match_any": ["ephes"],
            "min_chars": 80_000,
            "max_chars": cap,
            "kind": "commentary",
            "wave": 3,
        },
        "calvin_commentary_romans": {
            "author": "calvin",
            "filename": "commentary_romans.txt",
            "title": "Commentary on Romans (Calvin; CTS/Owen) — selected, not full dump",
            "urls": [
                ccel_cache("c", "calvin", "calcom38"),
                "https://www.ccel.org/ccel/c/calvin/calcom38/cache/calcom38.txt",
            ],
            "must_match_any": ["calvin", "romans"],
            "min_chars": 200_000,
            "max_chars": cap,
            "kind": "commentary",
            "wave": 3,
        },
        "calvin_commentary_1cor": {
            "author": "calvin",
            "filename": "commentary_1corinthians.txt",
            "title": "Commentary on 1 Corinthians (Calvin; CTS) — selected",
            "urls": [
                ccel_cache("c", "calvin", "calcom39"),
                "https://www.ccel.org/ccel/c/calvin/calcom39/cache/calcom39.txt",
            ],
            "must_match_any": ["calvin", "corinth"],
            "min_chars": 150_000,
            "max_chars": cap,
            "kind": "commentary",
            "wave": 3,
        },
        "calvin_commentary_2cor": {
            "author": "calvin",
            "filename": "commentary_2corinthians.txt",
            "title": "Commentary on 2 Corinthians (Calvin; CTS) — selected",
            "urls": [
                ccel_cache("c", "calvin", "calcom40"),
                "https://www.ccel.org/ccel/c/calvin/calcom40/cache/calcom40.txt",
            ],
            "must_match_any": ["calvin", "corinth"],
            "min_chars": 150_000,
            "max_chars": cap,
            "kind": "commentary",
            "wave": 3,
        },
        "calvin_commentary_gal_eph": {
            "author": "calvin",
            "filename": "commentary_galatians_ephesians.txt",
            "title": "Commentary on Galatians and Ephesians (Calvin; CTS/Pringle)",
            "urls": [
                ccel_cache("c", "calvin", "calcom41"),
                "https://www.ccel.org/ccel/c/calvin/calcom41/cache/calcom41.txt",
            ],
            "must_match_any": ["calvin", "galatian", "ephes"],
            "min_chars": 150_000,
            "max_chars": cap,
            "kind": "commentary",
            "wave": 3,
        },
        "calvin_commentary_catholic": {
            "author": "calvin",
            "filename": "commentary_catholic_epistles.txt",
            "title": "Commentary on the Catholic Epistles (Calvin; CTS) — selected",
            "urls": [
                ccel_cache("c", "calvin", "calcom45"),
                "https://www.ccel.org/ccel/c/calvin/calcom45/cache/calcom45.txt",
            ],
            "must_match_any": ["calvin", "james", "peter", "jude"],
            "min_chars": 150_000,
            "max_chars": cap,
            "kind": "commentary",
            "wave": 3,
        },
    }


CATALOG.update(_wave1_catalog())
CATALOG.update(_wave2_catalog())
CATALOG.update(_wave3_catalog())


def fetch_bytes(url: str, timeout: int = 180, retries: int = 2) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_err = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            print(f"    HTTP {e.code}: {url}")
            last_err = e
            # 403/503: try the next host, do not hammer the same URL.
            if e.code in {403, 503}:
                return None
            if e.code == 429 and attempt < retries:
                time.sleep(3.0 * (attempt + 1))
                continue
            return None
        except Exception as e:
            print(f"    fail: {e}")
            last_err = e
            if attempt < retries:
                time.sleep(2.0)
                continue
            return None
    return None


def to_text(data: bytes) -> str:
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def strip_html(text: str) -> str:
    head = text[:12_000].lower()
    is_markup = any(
        tok in head
        for tok in ("<html", "<body", "<tei", "<?xml", "<div", "<p ")
    )
    if not is_markup:
        return text
    text = re.sub(r"(?is)<teiHeader.*?</teiHeader>", " ", text)
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_pd_text(text: str) -> str:
    text = strip_html(text)
    # Gutenberg banners
    m = re.search(
        r"\*\*\*\s*START OF (THIS|THE) PROJECT GUTENBERG EBOOK.*?\*\*\*",
        text,
        re.I | re.S,
    )
    if m:
        text = text[m.end() :]
    m = re.search(
        r"\*\*\*\s*END OF (THIS|THE) PROJECT GUTENBERG EBOOK.*?\*\*\*",
        text,
        re.I | re.S,
    )
    if m:
        text = text[: m.start()]
    # CCEL cache header (underscore rules + Title/Creator block)
    if "Creator(s):" in text[:4000] or text.lstrip().startswith("_____"):
        cut = re.search(
            r"(?is)(?:Title:|Creator\(s\):|Rights:|CCEL Subjects:).*?(?:\n\s*\n|\n_{10,})",
            text[:12_000],
        )
        if cut:
            text = text[cut.end() :]
    # Archive OCR form feeds
    text = text.replace("\f", "\n\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def ocr_quality_ok(text: str) -> tuple[bool, str]:
    """Cheap OCR garbage gate: reject extreme garble / control-char dumps."""
    sample = text[:80_000]
    if not sample:
        return False, "empty"
    letters = sum(ch.isalpha() for ch in sample)
    spaces = sample.count(" ")
    weird = sum(1 for ch in sample if ord(ch) < 32 and ch not in "\n\t\r")
    letter_ratio = letters / max(len(sample), 1)
    if letter_ratio < 0.45:
        return False, f"letter_ratio={letter_ratio:.3f}"
    if weird / max(len(sample), 1) > 0.02:
        return False, f"control_chars={weird}"
    # Extremely broken OCR often has almost no spaces relative to length
    if spaces / max(len(sample), 1) < 0.06 and letter_ratio > 0.5:
        return False, f"space_ratio={spaces / len(sample):.3f}"
    return True, "ok"


def verify(text: str, entry: dict) -> bool:
    head = text[:20_000].lower()
    whole = text.lower()
    min_chars = int(entry.get("min_chars") or 1500)
    if len(text) < min_chars:
        return False
    max_chars = entry.get("max_chars")
    if max_chars and len(text) > int(max_chars):
        print(f"    REJECT max_chars ({len(text):,} > {int(max_chars):,})")
        return False
    # IA OCR title pages are often garble; search deeper than the first 50k.
    body = whole[:250_000]
    must = entry.get("must_match") or []
    if must and not all(k.lower() in head or k.lower() in body for k in must):
        return False
    any_keys = entry.get("must_match_any") or []
    if any_keys and not any(k.lower() in head or k.lower() in body for k in any_keys):
        return False
    ok, reason = ocr_quality_ok(text)
    if not ok:
        print(f"    REJECT OCR quality ({reason})")
        return False
    return True


def entry_dest(repo: Path, entry: dict) -> Path:
    dest_dir = entry.get("dest_dir")
    if dest_dir:
        return repo / dest_dir / entry["filename"]
    return repo / "data" / "puritans" / entry["author"] / entry["filename"]


def commentary_bytes_on_disk(repo: Path) -> int:
    total = 0
    for entry in CATALOG.values():
        if entry.get("kind") != "commentary":
            continue
        dest = entry_dest(repo, entry)
        if dest.exists():
            total += dest.stat().st_size
    return total


def download_entry(
    repo: Path,
    key: str,
    entry: dict,
    force: bool = False,
    sleep: float = 1.2,
) -> tuple[str, str]:
    """Returns (status, message). status in ok|skip|fail."""
    dest = entry_dest(repo, entry)
    if dest.exists() and dest.stat().st_size > 2000 and not force:
        return "skip", f"exists ({dest.stat().st_size:,} bytes)"

    for url in entry["urls"]:
        host = url.split("/")[2].lower() if "://" in url else ""
        if any(b in host for b in BLOCKED_BODY_HOSTS):
            print(f"    skip blocked shop host: {host}")
            continue
        print(f"    try {url}")
        data = fetch_bytes(url)
        if sleep:
            time.sleep(sleep)
        if not data or len(data) < 1500:
            continue
        text = clean_pd_text(to_text(data))
        if not verify(text, entry):
            print(f"    REJECT title/size check")
            print(f"    head: {text[:180]!r}")
            continue
        if entry.get("kind") == "commentary":
            existing = dest.stat().st_size if dest.exists() else 0
            projected = commentary_bytes_on_disk(repo) - existing + len(
                text.encode("utf-8")
            )
            if projected > COMMENTARY_CAP_BYTES:
                return (
                    "skip",
                    f"would exceed {COMMENTARY_CAP_BYTES / 1e6:.0f} MB commentary cap "
                    f"({projected / 1e6:.1f} MB)",
                )
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        return "ok", f"wrote {dest} ({len(text):,} chars)"

    return "fail", "all URLs failed or rejected"


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Fetch verified PD Puritan texts")
    p.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent.parent))
    p.add_argument("--list", action="store_true")
    p.add_argument("--only", default=None, help="Comma-separated keys or authors")
    p.add_argument("--wave", type=int, default=None, help="Fetch only entries tagged wave=N")
    p.add_argument("--force", action="store_true", help="Re-download even if file exists")
    p.add_argument("--sleep", type=float, default=1.2, help="Seconds between download attempts")
    p.add_argument("--rebuild-mix", action="store_true", help="Run 07_build_theology_mix after fetch")
    args = p.parse_args(argv)

    if args.list:
        for k, v in CATALOG.items():
            wave = v.get("wave", "-")
            dest = v.get("dest_dir") or f"data/puritans/{v['author']}"
            print(f"{k:32s}  w{wave}  {v['author']:12s}  {dest:36s}  {v['title']}")
        return

    repo = Path(args.repo_root).resolve()
    keys = list(CATALOG.keys())
    if args.wave is not None:
        keys = [k for k, v in CATALOG.items() if v.get("wave") == args.wave]
    if args.only:
        wanted = {x.strip().lower() for x in args.only.split(",") if x.strip()}
        keys = [
            k
            for k in keys
            if k in wanted
            or CATALOG[k]["author"] in wanted
            or k.split("_")[0] in wanted
        ]

    ok = skip = fail = 0
    results: list[str] = []
    for key in keys:
        entry = CATALOG[key]
        print(f"[{key}] {entry['title']}")
        status, msg = download_entry(
            repo, key, entry, force=args.force, sleep=args.sleep
        )
        print(f"  -> {status}: {msg}")
        results.append(f"{status}\t{key}\t{msg}")
        if status == "ok":
            ok += 1
        elif status == "skip":
            skip += 1
        else:
            fail += 1

    print("=" * 60)
    print(f"Done. ok={ok} skip={skip} fail={fail}")

    # Inventory (puritans + hymns + Hodge systematic)
    total = 0
    print("\nInventory:")
    for root in (
        repo / "data" / "puritans",
        repo / "data" / "hymns",
        repo / "data" / "confessions" / "systematic",
    ):
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.txt")):
            n = path.stat().st_size
            total += n
            print(f"  {path.relative_to(repo)}  {n:,} bytes")
    print(f"  TOTAL {total:,} bytes ({total/1e6:.1f} MB)")
    cbytes = commentary_bytes_on_disk(repo)
    print(
        f"  Wave-3 commentary cap: {cbytes:,} / {COMMENTARY_CAP_BYTES:,} bytes "
        f"({cbytes / 1e6:.1f} / {COMMENTARY_CAP_BYTES / 1e6:.0f} MB)"
    )

    log = repo / "continued_pretrain" / "data" / "puritan_fetch_log.txt"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("\n".join(results) + "\n", encoding="utf-8")
    print(f"Log: {log}")

    if args.rebuild_mix:
        import subprocess

        cmd = [
            sys.executable,
            str(repo / "continued_pretrain" / "scripts" / "07_build_theology_mix.py"),
            "--target-spurgeon-share",
            "0.45",
            "--replay-frac",
            "0.10",
            "--replay-txt",
            str(repo / "continued_pretrain" / "data" / "replay" / "general_replay.txt"),
            "--keep-all-spurgeon",
            "--max-other-weight",
            "1.5",
        ]
        print("Rebuilding mix:", " ".join(cmd))
        subprocess.check_call(cmd, cwd=str(repo))

    if fail and ok == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
