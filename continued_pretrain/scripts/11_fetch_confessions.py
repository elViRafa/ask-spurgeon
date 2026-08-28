#!/usr/bin/env python3
"""
Fetch public-domain confessions / systematic theology into data/confessions/.

- Westminster Confession (+ larger editions with catechisms)
- 1689 Second London Baptist Confession
- Calvin Institutes (Beveridge)
- S4: unique PD systematic (Gill, Dabney, Shedd, A.A. Hodge, Witsius, Boyce)
  plus small Reformed symbols (Dort, Second Helvetic, Scots Confession)

Heidelberg + Belgic stay in continued_pretrain/data/holdouts_manual/ (NOT training).
Do not fetch more biblical commentary. Do not grow Puritan treatise mass.

Usage:
  python continued_pretrain/scripts/11_fetch_confessions.py
  python continued_pretrain/scripts/11_fetch_confessions.py --s4
  python continued_pretrain/scripts/11_fetch_confessions.py --rebuild-mix
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "search-sermons-cpt-confessions/1.0 (research; public-domain only)"
SSL_CTX = ssl._create_unverified_context()


def fetch(url: str, timeout: int = 240) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as r:
        return r.read()


def to_text(data: bytes) -> str:
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def clean(text: str) -> str:
    if "<html" in text[:1200].lower() or "<body" in text[:1200].lower():
        text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
        text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
        text = re.sub(r"(?is)<[^>]+>", " ", text)
        text = html_lib.unescape(text)
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
    text = text.replace("\f", "\n\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def ocr_quality_ok(text: str) -> tuple[bool, str]:
    """Cheap OCR garbage gate (same thresholds as 10_fetch_puritans.py)."""
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
    if spaces / max(len(sample), 1) < 0.06 and letter_ratio > 0.5:
        return False, f"space_ratio={spaces / len(sample):.3f}"
    return True, "ok"


def holdout_leak(text: str) -> str | None:
    """Refuse Heidelberg / Belgic training dumps (eval holdouts)."""
    head = text[:80_000].lower()
    if "only comfort in life and death" in head and (
        "lord's day 1" in head or "question 1." in head[:4000]
    ):
        return "heidelberg holdout leak"
    if "we all believe with the heart" in head and "belgic" in head[:8000]:
        return "belgic holdout leak"
    return None


def passes(text: str, keys_any: list[str] | None, keys_all: list[str] | None, min_chars: int) -> bool:
    if len(text) < min_chars:
        return False
    leak = holdout_leak(text)
    if leak:
        print(f"    REJECT {leak}")
        return False
    ok, reason = ocr_quality_ok(text)
    if not ok:
        print(f"    REJECT OCR quality ({reason})")
        return False
    head = text[:30_000].lower()
    body = text[:250_000].lower()
    if keys_all and not all(k in head or k in body for k in keys_all):
        return False
    if keys_any and not any(k in head or k in body for k in keys_any):
        return False
    return True


def save(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"  SAVED {path} ({len(text):,} chars)")


def try_urls(
    dest: Path,
    urls: list[str],
    keys_any: list[str] | None = None,
    keys_all: list[str] | None = None,
    min_chars: int = 3000,
    force: bool = False,
    sleep: float = 1.2,
) -> bool:
    if dest.exists() and dest.stat().st_size > 2000 and not force:
        print(f"  skip exists: {dest} ({dest.stat().st_size:,} bytes)")
        return True
    for url in urls:
        print(f"  try {url}")
        try:
            text = clean(to_text(fetch(url)))
        except Exception as e:
            print(f"    ERR {e}")
            continue
        if sleep:
            time.sleep(sleep)
        print(f"    got {len(text):,} chars; head={text[:100]!r}")
        if not passes(text, keys_any, keys_all, min_chars):
            print("    REJECT verification")
            continue
        save(dest, text)
        return True
    return False


def ia_download(ident: str, name: str | None = None) -> str:
    return f"https://archive.org/download/{ident}/{name or ident + '_djvu.txt'}"


def search_ia(q: str, rows: int = 8) -> list[dict]:
    params = urllib.parse.urlencode(
        {"q": q, "rows": str(rows), "page": "1", "output": "json", "fl": "identifier,title"}
    )
    url = "https://archive.org/advancedsearch.php?" + params
    data = json.loads(to_text(fetch(url, timeout=60)))
    return data.get("response", {}).get("docs", [])


def meta_text_files(ident: str) -> list[str]:
    m = json.loads(to_text(fetch(f"https://archive.org/metadata/{ident}", timeout=60)))
    out = []
    for f in m.get("files") or []:
        name = f.get("name") or ""
        size = int(f.get("size") or 0)
        if size < 2000:
            continue
        if name.endswith("_djvu.txt") or (
            name.endswith(".txt") and "hocr" not in name and "meta" not in name.lower()
        ):
            out.append(name)
    return out


# Curated public-domain 1689 LBCF (standard English text; PD).
LBCF_1689 = r'''THE SECOND LONDON BAPTIST CONFESSION OF FAITH (1689)
(Public domain; classic English text)

Chapter 1 — Of the Holy Scriptures
1. The Holy Scripture is the only sufficient, certain, and infallible rule of all saving knowledge, faith, and obedience, although the light of nature, and the works of creation and providence do so far manifest the goodness, wisdom, and power of God, as to leave men inexcusable; yet are they not sufficient to give that knowledge of God and his will which is necessary unto salvation. Therefore it pleased the Lord at sundry times and in divers manners to reveal himself, and to declare that his will unto his church; and afterward for the better preserving and propagating of the truth, and for the more sure establishment and comfort of the church against the corruption of the flesh, and the malice of Satan, and of the world, to commit the same wholly unto writing; which maketh the Holy Scriptures to be most necessary, those former ways of God's revealing his will unto his people being now ceased.
2. Under the name of Holy Scripture, or the Word of God written, are now contained all the books of the Old and New Testament, which are these: Of the Old Testament: Genesis, Exodus, Leviticus, Numbers, Deuteronomy, Joshua, Judges, Ruth, I Samuel, II Samuel, I Kings, II Kings, I Chronicles, II Chronicles, Ezra, Nehemiah, Esther, Job, Psalms, Proverbs, Ecclesiastes, The Song of Songs, Isaiah, Jeremiah, Lamentations, Ezekiel, Daniel, Hosea, Joel, Amos, Obadiah, Jonah, Micah, Nahum, Habakkuk, Zephaniah, Haggai, Zechariah, Malachi. Of the New Testament: Matthew, Mark, Luke, John, The Acts of the Apostles, Paul's Epistle to the Romans, I Corinthians, II Corinthians, Galatians, Ephesians, Philippians, Colossians, I Thessalonians, II Thessalonians, I Timothy, II Timothy, To Titus, To Philemon, The Epistle to the Hebrews, The Epistle of James, The first and second Epistles of Peter, The first, second, and third Epistles of John, The Epistle of Jude, The Revelation. All which are given by the inspiration of God, to be the rule of faith and life.
3. The books commonly called Apocrypha, not being of divine inspiration, are no part of the canon or rule of the Scripture, and, therefore, are of no authority to the church of God, nor to be any otherwise approved or made use of than other human writings.
4. The authority of the Holy Scripture, for which it ought to be believed, dependeth not upon the testimony of any man or church, but wholly upon God (who is truth itself), the author thereof; therefore it is to be received because it is the Word of God.
5. We may be moved and induced by the testimony of the church of God to an high and reverent esteem of the Holy Scriptures; and the heavenliness of the matter, the efficacy of the doctrine, and the majesty of the style, the consent of all the parts, the scope of the whole (which is to give all glory to God), the full discovery it makes of the only way of man's salvation, and many other incomparable excellencies, and entire perfections thereof, are arguments whereby it doth abundantly evidence itself to be the Word of God; yet notwithstanding, our full persuasion and assurance of the infallible truth, and divine authority thereof, is from the inward work of the Holy Spirit bearing witness by and with the Word in our hearts.
6. The whole counsel of God concerning all things necessary for his own glory, man's salvation, faith and life, is either expressly set down or necessarily contained in the Holy Scripture: unto which nothing at any time is to be added, whether by new revelation of the Spirit, or traditions of men. Nevertheless, we acknowledge the inward illumination of the Spirit of God to be necessary for the saving understanding of such things as are revealed in the Word, and that there are some circumstances concerning the worship of God, and government of the church, common to human actions and societies, which are to be ordered by the light of nature and Christian prudence, according to the general rules of the Word, which are always to be observed.
7. All things in Scripture are not alike plain in themselves, nor alike clear unto all; yet those things which are necessary to be known, believed and observed for salvation, are so clearly propounded and opened in some place of Scripture or other, that not only the learned, but the unlearned, in a due use of ordinary means, may attain to a sufficient understanding of them.
8. The Old Testament in Hebrew (which was the native language of the people of God of old), and the New Testament in Greek (which at the time of the writing of it was most generally known to the nations), being immediately inspired by God, and by his singular care and providence kept pure in all ages, are therefore authentic; so as in all controversies of religion, the church is finally to appeal to them. But because these original tongues are not known to all the people of God, who have a right unto, and interest in the Scriptures, and are commanded in the fear of God to read and search them, therefore they are to be translated into the vulgar language of every nation unto which they come, that the Word of God dwelling plentifully in all, they may worship him in an acceptable manner, and through patience and comfort of the Scriptures may have hope.
9. The infallible rule of interpretation of Scripture is the Scripture itself; and therefore when there is a question about the true and full sense of any Scripture (which is not manifold, but one), it must be searched by other places that speak more clearly.
10. The supreme judge, by which all controversies of religion are to be determined, and all decrees of councils, opinions of ancient writers, doctrines of men, and private spirits, are to be examined, and in whose sentence we are to rest, can be no other but the Holy Scripture delivered by the Spirit, into which Scripture so delivered, our faith is finally resolved.

Chapter 2 — Of God and of the Holy Trinity
1. The Lord our God is but one only living and true God; whose subsistence is in and of himself, infinite in being and perfection; whose essence cannot be comprehended by any but himself; a most pure spirit, invisible, without body, parts, or passions, who only hath immortality, dwelling in the light which no man can approach unto; who is immutable, immense, eternal, incomprehensible, almighty, every way infinite, most holy, most wise, most free, most absolute; working all things according to the counsel of his own immutable and most righteous will for his own glory; most loving, gracious, merciful, long-suffering, abundant in goodness and truth, forgiving iniquity, transgression, and sin; the rewarder of them that diligently seek him, and withal most just and terrible in his judgments, hating all sin, and who will by no means clear the guilty.
2. God, having all life, glory, goodness, blessedness, in and of himself, is alone in and unto himself all-sufficient, not standing in need of any creature which he hath made, nor deriving any glory from them, but only manifesting his own glory in, by, unto, and upon them; he is the alone fountain of all being, of whom, through whom, and to whom are all things, and he hath most sovereign dominion over all creatures, to do by them, for them, or upon them, whatsoever himself pleaseth; in his sight all things are open and manifest, his knowledge is infinite, infallible, and independent upon the creature, so as nothing is to him contingent or uncertain; he is most holy in all his counsels, in all his works, and in all his commands; to him is due from angels and men, whatsoever worship, service, or obedience, as creatures they owe unto the Creator, and whatever he is further pleased to require of them.
3. In this divine and infinite Being there are three subsistences, the Father, the Word or Son, and Holy Spirit, of one substance, power, and eternity, each having the whole divine essence, yet the essence undivided: the Father is of none, neither begotten nor proceeding; the Son is eternally begotten of the Father; the Holy Spirit proceeding from the Father and the Son; all infinite, without beginning, therefore but one God, who is not to be divided in nature and being, but distinguished by several peculiar relative properties and personal relations; which doctrine of the Trinity is the foundation of all our communion with God, and comfortable dependence on him.

Chapter 3 — Of God's Decree
1. God hath decreed in himself, from all eternity, by the most wise and holy counsel of his own will, freely and unchangeably, all things, whatsoever comes to pass; yet so as thereby is God neither the author of sin nor hath fellowship with any therein; nor is violence offered to the will of the creature, nor yet is the liberty or contingency of second causes taken away, but rather established; in which appears his wisdom in disposing all things, and power and faithfulness in accomplishing his decree.
2. Although God knoweth whatsoever may or can come to pass, upon all supposed conditions, yet hath he not decreed anything, because he foresaw it as future, or as that which would come to pass upon such conditions.
3. By the decree of God, for the manifestation of his glory, some men and angels are predestinated, or foreordained to eternal life through Jesus Christ, to the praise of his glorious grace; others being left to act in their sin to their just condemnation, to the praise of his glorious justice.
4. These angels and men thus predestinated and foreordained, are particularly and unchangeably designed, and their number so certain and definite, that it cannot be either increased or diminished.
5. Those of mankind that are predestinated to life, God, before the foundation of the world was laid, according to his eternal and immutable purpose, and the secret counsel and good pleasure of his will, hath chosen in Christ unto everlasting glory, out of his mere free grace and love, without any other thing in the creature as a condition or cause moving him thereunto.
6. As God hath appointed the elect unto glory, so he hath, by the eternal and most free purpose of his will, foreordained all the means thereunto; wherefore they who are elected, being fallen in Adam, are redeemed by Christ, are effectually called unto faith in Christ, by his Spirit working in due season, are justified, adopted, sanctified, and kept by his power through faith unto salvation; neither are any other redeemed by Christ, or effectually called, justified, adopted, sanctified, and saved, but the elect only.
7. The doctrine of the high mystery of predestination is to be handled with special prudence and care, that men attending the will of God revealed in his Word, and yielding obedience thereunto, may, from the certainty of their effectual vocation, be assured of their eternal election; so shall this doctrine afford matter of praise, reverence, and admiration of God, and of humility, diligence, and abundant consolation to all that sincerely obey the gospel.

Chapter 4 — Of Creation
1. In the beginning it pleased God the Father, Son, and Holy Spirit, for the manifestation of the glory of his eternal power, wisdom, and goodness, to create or make the world, and all things therein, whether visible or invisible, in the space of six days, and all very good.
2. After God had made all other creatures, he created man, male and female, with reasonable and immortal souls, rendering them fit unto that life to God for which they were created; being made after the image of God, in knowledge, righteousness, and true holiness; having the law of God written in their hearts, and power to fulfil it, and yet under a possibility of transgressing, being left to the liberty of their own will, which was subject to change.
3. Besides the law written in their hearts, they received a command not to eat of the tree of knowledge of good and evil, which whilst they kept, they were happy in their communion with God, and had dominion over the creatures.

Chapter 5 — Of Divine Providence
1. God the good Creator of all things, in his infinite power and wisdom doth uphold, direct, dispose, and govern all creatures and things, from the greatest even to the least, by his most wise and holy providence, to the end for the which they were created, according unto his infallible foreknowledge, and the free and immutable counsel of his own will; to the praise of the glory of his wisdom, power, justice, infinite goodness, and mercy.
2. Although in relation to the foreknowledge and decree of God, the first cause, all things come to pass immutably and infallibly; so that there is not anything befalls any by chance, or without his providence; yet by the same providence he ordereth them to fall out according to the nature of second causes, either necessarily, freely, or contingently.
3. God, in his ordinary providence maketh use of means, yet is free to work without, above, and against them at his pleasure.
4. The almighty power, unsearchable wisdom, and infinite goodness of God, so far manifest themselves in his providence, that his determinate counsel extendeth itself even to the first fall, and all other sinful actions both of angels and men; and that not by a bare permission, which also he most wisely and powerfully boundeth, and otherwise ordereth and governeth, in a manifold dispensation to his most holy ends; yet so, as the sinfulness of their acts proceedeth only from the creatures, and not from God, who, being most holy and righteous, neither is nor can be the author or approver of sin.
5. The most wise, righteous, and gracious God doth oftentimes leave for a season his own children to manifold temptations and the corruptions of their own hearts, to chastise them for their former sins, or to discover unto them the hidden strength of corruption and deceitfulness of their hearts, that they may be humbled; and to raise them to a more close and constant dependence for their support upon himself; and to make them more watchful against all future occasions of sin, and for sundry other just and holy ends. So that whatsoever befalls any of his elect is by his appointment, for his glory, and their good.
6. As for those wicked and ungodly men whom God, as the righteous judge, for former sin doth blind and harden; from them he not only withholdeth his grace, whereby they might have been enlightened in their understanding, and wrought upon their hearts; but sometimes also withdraweth the gifts which they had, and exposeth them to such objects as their corruption makes occasion of sin; and withal, gives them over to their own lusts, the temptations of the world, and the power of Satan, whereby it comes to pass that they harden themselves, under those means which God useth for the softening of others.
7. As the providence of God doth in general reach to all creatures, so after a more special manner it taketh care of his church, and disposeth of all things to the good thereof.

Chapter 6 — Of the Fall of Man, of Sin, and of the Punishment Thereof
1. Although God created man upright and perfect, and gave him a righteous law, which had been unto life had he kept it, and threatened death upon the breach thereof, yet he did not long abide in this honour; Satan using the subtlety of the serpent to subdue Eve, then by her seducing Adam, who, without any compulsion, did wilfully transgress the law of their creation, and the command given unto them, in eating the forbidden fruit, which God was pleased, according to his wise and holy counsel to permit, having purposed to order it to his own glory.
2. Our first parents, by this sin, fell from their original righteousness and communion with God, and we in them whereby death came upon all: all becoming dead in sin, and wholly defiled in all the faculties and parts of soul and body.
3. They being the root, and by God's appointment, standing in the room and stead of all mankind, the guilt of the sin was imputed, and corrupted nature conveyed, to all their posterity descending from them by ordinary generation, being now conceived in sin, and by nature children of wrath, the servants of sin, the subjects of death, and all other miseries, spiritual, temporal, and eternal, unless the Lord Jesus set them free.
4. From this original corruption, whereby we are utterly indisposed, disabled, and made opposite to all good, and wholly inclined to all evil, do proceed all actual transgressions.
5. The corruption of nature, during this life, doth remain in those that are regenerated; and although it be through Christ pardoned and mortified, yet both itself, and the first motions thereof, are truly and properly sin.

Chapter 7 — Of God's Covenant
1. The distance between God and the creature is so great, that although reasonable creatures do owe obedience to him as their creator, yet they could never have attained the reward of life but by some voluntary condescension on God's part, which he hath been pleased to express by way of covenant.
2. Moreover, man having brought himself under the curse of the law by his fall, it pleased the Lord to make a covenant of grace, wherein he freely offereth unto sinners life and salvation by Jesus Christ, requiring of them faith in him, that they may be saved; and promising to give unto all those that are ordained unto eternal life, his Holy Spirit, to make them willing and able to believe.
3. This covenant is revealed in the gospel; first of all to Adam in the promise of salvation by the seed of the woman, and afterwards by farther steps, until the full discovery thereof was completed in the New Testament; and it is founded in that eternal covenant transaction that was between the Father and the Son about the redemption of the elect; and it is alone by the grace of this covenant that all the posterity of fallen Adam that ever were saved did obtain life and blessed immortality, man being now utterly incapable of acceptance with God upon those terms on which Adam stood in his state of innocency.

Chapter 8 — Of Christ the Mediator
1. It pleased God, in his eternal purpose, to choose and ordain the Lord Jesus, his only begotten Son, according to the covenant made between them both, to be the mediator between God and man; the prophet, priest, and king; head and saviour of the church, the heir of all things, and judge of the world; unto whom he did from all eternity give a people to be his seed and to be by him in time redeemed, called, justified, sanctified, and glorified.
2. The Son of God, the second person in the Holy Trinity, being very and eternal God, the brightness of the Father's glory, of one substance and equal with him who made the world, who upholdeth and governeth all things he hath made, did, when the fullness of time was come, take upon him man's nature, with all the essential properties and common infirmities thereof, yet without sin; being conceived by the Holy Spirit in the womb of the Virgin Mary, the Holy Spirit coming down upon her: and the power of the Most High overshadowing her; and so was made of a woman of the tribe of Judah, of the seed of Abraham and David according to the Scriptures; so that two whole, perfect, and distinct natures were inseparably joined together in one person, without conversion, composition, or confusion; which person is very God and very man, yet one Christ, the only mediator between God and man.
3. The Lord Jesus, in his human nature thus united to the divine, in the person of the Son, was sanctified and anointed with the Holy Spirit above measure, having in him all the treasures of wisdom and knowledge; in whom it pleased the Father that all fullness should dwell, to the end that being holy, harmless, undefiled, and full of grace and truth, he might be thoroughly furnished to execute the office of mediator and surety; which office he took not upon himself, but was thereunto called by his Father; who also put all power and judgment in his hand, and gave him commandment to execute the same.
4. This office the Lord Jesus did most willingly undertake, which that he might discharge he was made under the law, and did perfectly fulfil it, and underwent the punishment due to us, which we should have borne and suffered, being made sin and a curse for us; enduring most grievous sorrows in his soul, and most painful sufferings in his body; was crucified, and died, and remained in the state of the dead, yet saw no corruption: on the third day he arose from the dead with the same body in which he suffered, with which he also ascended into heaven, and there sitteth at the right hand of his Father making intercession, and shall return to judge men and angels at the end of the world.
5. The Lord Jesus, by his perfect obedience and sacrifice of himself, which he through the eternal Spirit once offered up unto God, hath fully satisfied the justice of God, procured reconciliation, and purchased an everlasting inheritance in the kingdom of heaven, for all those whom the Father hath given unto him.
6. Although the price of redemption was not actually paid by Christ till after his incarnation, yet the virtue, efficacy, and benefit thereof were communicated to the elect in all ages, successively from the beginning of the world, in and by those promises, types, and sacrifices wherein he was revealed, and signified to be the seed which should bruise the serpent's head; and the Lamb slain from the foundation of the world, being the same yesterday, and to-day and for ever.
7. Christ, in the work of mediation, acteth according to both natures, by each nature doing that which is proper to itself; yet by reason of the unity of the person, that which is proper to one nature is sometimes in Scripture, attributed to the person denominated by the other nature.
8. To all those for whom Christ hath obtained eternal redemption, he doth certainly and effectually apply and communicate the same, making intercession for them; uniting them to himself by his Spirit, revealing unto them, in and by his Word, the mystery of salvation, persuading them to believe and obey, governing their hearts by his Word and Spirit, and overcoming all their enemies by his almighty power and wisdom, in such manner and ways as are most consonant to his wonderful and unsearchable dispensation; and all of free and absolute grace, without any condition foreseen in them to procure it.
9. This office of mediator between God and man is proper only to Christ, who is the prophet, priest, and king of the church of God; and may not be either in whole, or any part thereof, transferred from him to any other.
10. This number and order of offices is necessary; for in respect of our ignorance, we stand in need of his prophetical office; and in respect of our alienation from God, and imperfection of the best of our services, we need his priestly office to reconcile us and present us acceptable unto God; and in respect to our averseness and utter inability to return to God, and for our rescue and security from our spiritual adversaries, we need his kingly office to convince, subdue, draw, uphold, deliver, and preserve us to his heavenly kingdom.

Chapter 9 — Of Free Will
1. God hath endued the will of man with that natural liberty and power of acting upon choice, that it is neither forced, nor by any necessity of nature determined to do good or evil.
2. Man, in his state of innocency, had freedom and power to will and to do that which was good and well-pleasing to God, but yet was unstable, so that he might fall from it.
3. Man, by his fall into a state of sin, hath wholly lost all ability of will to any spiritual good accompanying salvation; so as a natural man, being altogether averse from that good, and dead in sin, is not able by his own strength to convert himself, or to prepare himself thereunto.
4. When God converts a sinner, and translates him into the state of grace, he freeth him from his natural bondage under sin, and by his grace alone enables him freely to will and to do that which is spiritually good; yet so as that by reason of his remaining corruptions, he doth not perfectly, nor only will, that which is good, but doth also will that which is evil.
5. This will of man is made perfectly and immutably free to good alone in the state of glory only.

Chapter 10 — Of Effectual Calling
1. Those whom God hath predestinated unto life, he is pleased in his appointed, and accepted time, effectually to call, by his Word and Spirit, out of that state of sin and death in which they are by nature, to grace and salvation by Jesus Christ; enlightening their minds spiritually and savingly to understand the things of God; taking away their heart of stone, and giving unto them a heart of flesh; renewing their wills, and by his almighty power determining them to that which is good, and effectually drawing them to Jesus Christ; yet so as they come most freely, being made willing by his grace.
2. This effectual call is of God's free and special grace alone, not from anything at all foreseen in man, nor from any power or agency in the creature, being wholly passive therein, being dead in sins and trespasses, until being quickened and renewed by the Holy Spirit; he is thereby enabled to answer this call, and to embrace the grace offered and conveyed in it, and that by no less power than that which raised up Christ from the dead.
3. Elect infants dying in infancy are regenerated and saved by Christ through the Spirit; who worketh when, and where, and how he pleaseth; so also are all elect persons, who are incapable of being outwardly called by the ministry of the Word.
4. Others not elected, although they may be called by the ministry of the Word, and may have some common operations of the Spirit, yet not being effectually drawn by the Father, they neither will nor can truly come to Christ, and therefore cannot be saved: much less can men that receive not the Christian religion be saved; be they never so diligent to frame their lives according to the light of nature and the law of that religion they do profess.

Chapter 11 — Of Justification
1. Those whom God effectually calleth, he also freely justifieth, not by infusing righteousness into them, but by pardoning their sins, and by accounting and accepting their persons as righteous; not for anything wrought in them, or done by them, but for Christ's sake alone; not by imputing faith itself, the act of believing, or any other evangelical obedience to them, as their righteousness; but by imputing Christ's active obedience unto the whole law, and passive obedience in his death for their whole and sole righteousness, they receiving and resting on him and his righteousness by faith, which faith they have not of themselves; it is the gift of God.
2. Faith thus receiving and resting on Christ and his righteousness, is the alone instrument of justification; yet it is not alone in the person justified, but is ever accompanied with all other saving graces, and is no dead faith, but worketh by love.
3. Christ, by his obedience and death, did fully discharge the debt of all those that are justified; and did, by the sacrifice of himself in the blood of his cross, undergoing in their stead the penalty due unto them, make a proper, real, and full satisfaction to God's justice in their behalf; yet, inasmuch as he was given by the Father for them, and his obedience and satisfaction accepted in their stead, and both freely, not for anything in them, their justification is only of free grace, that both the exact justice and rich grace of God might be glorified in the justification of sinners.
4. God did from all eternity decree to justify all the elect, and Christ did in the fullness of time die for their sins, and rise again for their justification; nevertheless, they are not justified personally, until the Holy Spirit doth in due time actually apply Christ unto them.
5. God doth continue to forgive the sins of those that are justified, and although they can never fall from the state of justification, yet they may, by their sins, fall under God's fatherly displeasure; and in that condition they have not usually the light of his countenance restored unto them, until they humble themselves, confess their sins, beg pardon, and renew their faith and repentance.
6. The justification of believers under the Old Testament was, in all these respects, one and the same with the justification of believers under the New Testament.

Chapter 14 — Of Saving Faith
1. The grace of faith, whereby the elect are enabled to believe to the saving of their souls, is the work of the Spirit of Christ in their hearts, and is ordinarily wrought by the ministry of the Word; by which also, and by the administration of baptism and the Lord's supper, prayer, and other means appointed of God, it is increased and strengthened.
2. By this faith a Christian believeth to be true whatsoever is revealed in the Word for the authority of God himself, and also apprehendeth an excellency therein above all other writings and all things in the world, as it bears forth the glory of God in his attributes, the excellency of Christ in his nature and offices, and the power and fullness of the Holy Spirit in his workings and operations: and so is enabled to cast his soul upon the truth thus believed; and also acteth differently upon that which each particular passage thereof containeth; yielding obedience to the commands, trembling at the threatenings, and embracing the promises of God for this life and that which is to come; but the principal acts of saving faith have immediate relation to Christ, accepting, receiving, and resting upon him alone for justification, sanctification, and eternal life, by virtue of the covenant of grace.
3. This faith, although it be different in degrees, and may be weak or strong, yet it is in the least degree of it different in the kind or nature of it, as is all other saving grace, from the faith and common grace of temporary believers; and therefore, though it may be many times assailed and weakened, yet it gets the victory, growing up in many to the attainment of a full assurance through Christ, who is both the author and finisher of our faith.

Chapter 29 — Of Baptism
1. Baptism is an ordinance of the New Testament, ordained by Jesus Christ, to be unto the party baptized, a sign of his fellowship with him, in his death and resurrection; of his being engrafted into him; of remission of sins; and of giving up into God, through Jesus Christ, to live and walk in newness of life.
2. Those who do actually profess repentance towards God, faith in, and obedience to, our Lord Jesus Christ, are the only proper subjects of this ordinance.
3. The outward element to be used in this ordinance is water, wherein the party is to be baptized, in the name of the Father, and of the Son, and of the Holy Spirit.
4. Immersion, or dipping of the person in water, is necessary to the due administration of this ordinance.

Chapter 32 — Of the Last Judgment
1. God hath appointed a day wherein he will judge the world in righteousness, by Jesus Christ; to whom all power and judgment is given of the Father; in which day, not only the apostate angels shall be judged, but likewise all persons that have lived upon earth shall appear before the tribunal of Christ, to give an account of their thoughts, words, and deeds, and to receive according to what they have done in the body, whether good or evil.
2. The end of God's appointing this day, is for the manifestation of the glory of his mercy, in the eternal salvation of the elect; and of his justice, in the eternal damnation of the reprobate, who are wicked and disobedient; for then shall the righteous go into everlasting life, and receive that fullness of joy and glory with everlasting reward, in the presence of the Lord; but the wicked, who know not God, and obey not the gospel of Jesus Christ, shall be cast aside into everlasting torments, and punished with everlasting destruction, from the presence of the Lord, and from the glory of his power.
3. As Christ would have us to be certainly persuaded that there shall be a day of judgment, both to deter all men from sin, and for the greater consolation of the godly in their adversity, so will he have the day unknown to men, that they may shake off all carnal security, and be always watchful, because they know not at what hour the Lord will come, and may ever be prepared to say, Come Lord Jesus; come quickly. Amen.
'''


CATALOG = [
    {
        "dest": "data/confessions/westminster/westminster_confession.txt",
        "title": "Westminster Confession of Faith (with proofs)",
        "urls": [
            ia_download("confessionoffa00west"),
            ia_download("confessionoffait1658west"),
        ],
        "keys_any": ["confession", "faith", "westminster", "scripture"],
        "min_chars": 20_000,
    },
    {
        "dest": "data/confessions/westminster/wcf_catechisms_1756.txt",
        "title": "WCF + Larger & Shorter Catechisms (1756 Scottish edition)",
        "urls": [
            ia_download(
                "bim_eighteenth-century_the-confession-of-faith-_westminster-assembly-16_1756",
                "bim_eighteenth-century_the-confession-of-faith-_westminster-assembly-16_1756_djvu.txt",
            ),
            ia_download("confessionoffait1658west"),
        ],
        "keys_any": ["confession", "catechism", "larger", "shorter"],
        "min_chars": 80_000,
    },
    {
        "dest": "data/confessions/institutes/institutes_beveridge_vol1.txt",
        "title": "Calvin Institutes (Beveridge) vol. 1",
        "urls": [
            ia_download("institutesofchrbeve01calv"),
            ia_download("instituteschrist01calvuoft"),
        ],
        "keys_any": ["calvin", "institute", "beveridge", "christian religion"],
        "min_chars": 100_000,
    },
    {
        "dest": "data/confessions/institutes/institutes_beveridge_vol2.txt",
        "title": "Calvin Institutes (Beveridge) vol. 2",
        "urls": [
            ia_download("institutesofchribeve02calv"),
            ia_download("institutesofreli02calvuoft"),
            ia_download("institutesofthec03calvuoft"),
        ],
        "keys_any": ["calvin", "institute", "christian"],
        "min_chars": 100_000,
    },
]


def ccel_cache(letter: str, author: str, work: str) -> str:
    return f"https://ccel.org/ccel/{letter}/{author}/{work}/cache/{work}.txt"


# Unique PD confession/ST for share-band lift. Not commentary. Not Puritan treatises.
# Not Turretin English (P&R/Dennison 1992–97 is in copyright). Not Heidelberg/Belgic.
S4_CATALOG = [
    {
        "key": "gill_doctrinal",
        "dest": "data/confessions/systematic/gill_body_of_doctrinal_divinity.txt",
        "title": "John Gill, Body of Doctrinal Divinity",
        "urls": [
            ccel_cache("g", "gill", "doctrinal"),
            "https://ccel.org/ccel/g/gill/doctrinal/cache/doctrinal.txt",
        ],
        "keys_any": ["gill", "doctrinal divinity", "body of doctrinal"],
        "min_chars": 80_000,
    },
    {
        "key": "dabney_syllabus",
        "dest": "data/confessions/systematic/dabney_systematic_theology.txt",
        "title": "R.L. Dabney, Syllabus and Notes of Systematic and Polemic Theology",
        "urls": [ia_download("syllabusnotesofc00dabn")],
        "keys_all": ["dabney"],
        "keys_any": ["systematic", "polemic", "syllabus", "theology"],
        "min_chars": 400_000,
    },
    {
        "key": "shedd_dogmatic_vol1",
        "dest": "data/confessions/systematic/shedd_dogmatic_theology_vol1.txt",
        "title": "W.G.T. Shedd, Dogmatic Theology vol. 1",
        "urls": [
            ia_download("dogmatictheology01shed"),
            ia_download("cu31924092342538"),
        ],
        "keys_any": ["shedd", "dogmatic"],
        "min_chars": 200_000,
    },
    {
        "key": "shedd_dogmatic_vol2",
        "dest": "data/confessions/systematic/shedd_dogmatic_theology_vol2.txt",
        "title": "W.G.T. Shedd, Dogmatic Theology vol. 2",
        "urls": [
            ia_download("dogmatictheology02shed"),
            ia_download("cu31924092342546"),
        ],
        "keys_any": ["shedd", "dogmatic"],
        "min_chars": 200_000,
    },
    {
        "key": "shedd_dogmatic_vol3",
        "dest": "data/confessions/systematic/shedd_dogmatic_theology_vol3.txt",
        "title": "W.G.T. Shedd, Dogmatic Theology vol. 3",
        "urls": [
            ia_download("dogmatictheology03shed"),
            ia_download("cu31924092342553"),
        ],
        "keys_any": ["shedd", "dogmatic"],
        "min_chars": 200_000,
    },
    {
        "key": "aa_hodge_outlines",
        "dest": "data/confessions/systematic/aa_hodge_outlines_of_theology.txt",
        "title": "A.A. Hodge, Outlines of Theology (1878 rewritten)",
        "urls": [
            ia_download("outlinesoftheolo1878hodg"),
            ia_download("outlinesoftheolo1860hodg"),
        ],
        "keys_all": ["hodge"],
        "keys_any": ["outlines", "archibald"],
        "min_chars": 300_000,
    },
    {
        "key": "witsius_covenants_vol1",
        "dest": "data/confessions/systematic/witsius_economy_of_the_covenants_vol1.txt",
        "title": "Herman Witsius, Economy of the Covenants vol. 1 (Crookshank)",
        "urls": [
            ia_download("oeconomyofcovena01wits"),
            ia_download("oeconomyofcovena176201wits"),
        ],
        "keys_any": ["witsius", "covenant", "oeconomy", "economy of the covenants"],
        "min_chars": 200_000,
    },
    {
        "key": "witsius_covenants_vol2",
        "dest": "data/confessions/systematic/witsius_economy_of_the_covenants_vol2.txt",
        "title": "Herman Witsius, Economy of the Covenants vol. 2 (Crookshank)",
        "urls": [
            ia_download("oeconomyofcovena02wits"),
            ia_download("oeconomyofcovena176202wits"),
        ],
        "keys_any": ["witsius", "covenant", "oeconomy", "economy of the covenants"],
        "min_chars": 200_000,
    },
    {
        "key": "boyce_abstract",
        "dest": "data/confessions/systematic/boyce_abstract_of_systematic_theology.txt",
        "title": "J.P. Boyce, Abstract of Systematic Theology",
        "urls": [ia_download("abstractofsystem00boyc")],
        "keys_any": ["boyce", "abstract of systematic"],
        "min_chars": 200_000,
    },
    {
        "key": "second_helvetic",
        "dest": "data/confessions/reformed/second_helvetic_confession.txt",
        "title": "Second Helvetic Confession (Bullinger)",
        "urls": [
            "https://www.ccel.org/ccel/schaff/creeds3.v.ix.html",
            "https://ccel.org/ccel/schaff/creeds3.v.ix.html",
            ccel_cache("a", "anonymous", "helvetic"),
        ],
        "keys_any": ["helvetic", "bullinger"],
        "min_chars": 8_000,
    },
    {
        "key": "scots_confession",
        "dest": "data/confessions/reformed/scots_confession_1560.txt",
        "title": "Scots Confession (1560)",
        "urls": [
            ccel_cache("a", "anonymous", "scotconf"),
            "https://ccel.org/ccel/a/anonymous/scotconf/cache/scotconf.txt",
        ],
        "keys_any": ["scotland", "knox", "scots confession", "scottish confession"],
        "min_chars": 8_000,
    },
    {
        "key": "canons_of_dort",
        "dest": "data/confessions/reformed/canons_of_dort.txt",
        "title": "Canons of Dort (Schaff English; not Heidelberg/Belgic)",
        "urls": [
            "https://www.ccel.org/ccel/schaff/creeds3.iv.xvi.html",
            "https://ccel.org/ccel/schaff/creeds3.iv.xvi.html",
        ],
        "keys_any": ["dort", "dordt", "dordrecht", "remonstrant"],
        "min_chars": 8_000,
    },
]


def try_fetch_1689(repo: Path, force: bool) -> bool:
    dest = repo / "data" / "confessions" / "1689" / "second_london_confession.txt"
    if dest.exists() and dest.stat().st_size > 2000 and not force:
        print(f"  skip exists: {dest}")
        return True

    # Prefer an Archive.org full text if we can find one
    print("Searching Archive.org for 1689 Baptist Confession...")
    try:
        docs = search_ia(
            'title:("1689" OR "second london") AND (confession) AND (baptist OR baptist)',
            rows=12,
        )
        for d in docs:
            ident = d.get("identifier")
            title = str(d.get("title") or "")
            print(f"  candidate {ident} | {title[:90]}")
            if not ident:
                continue
            try:
                files = meta_text_files(ident)
            except Exception as e:
                print(f"    meta fail: {e}")
                continue
            for name in files[:3]:
                url = ia_download(ident, name)
                print(f"    try {url}")
                try:
                    text = clean(to_text(fetch(url)))
                except Exception as e:
                    print(f"    ERR {e}")
                    continue
                # Verify 1689-ish content, avoid pure sermon audio transcripts
                if passes(
                    text,
                    keys_any=["baptism", "immersion", "confession", "scripture", "1689", "london"],
                    keys_all=None,
                    min_chars=15_000,
                ) and (
                    "baptis" in text.lower()
                    or "immersion" in text.lower()
                    or "second london" in text.lower()
                ):
                    save(dest, text)
                    return True
    except Exception as e:
        print(f"  IA search failed: {e}")

    # Fallback: curated PD text of core chapters (not full 32 chapters, but solid)
    print("  Using curated public-domain 1689 text (selected chapters + essentials)")
    save(dest, LBCF_1689)
    return True


PROVENANCE = """# Confessions / Institutes provenance

| Work | Path | Source |
|------|------|--------|
| WCF (with proofs) | `westminster/westminster_confession.txt` | IA `confessionoffa00west` |
| WCF + catechisms (1756) | `westminster/wcf_catechisms_1756.txt` | IA Scottish edition |
| WSC (curated earlier) | `westminster/westminster_shorter_catechism.txt` | curated PD |
| 1689 LBCF | `1689/second_london_confession.txt` | IA if found, else curated PD core chapters |
| Hodge ST vol.1–3 | `systematic/systematic_theology_vol*.txt` | IA `systematictheolo0{1,2,3}hodg` (moved from puritans/) |
| Calvin Institutes Beveridge vol.1–2 | `institutes/institutes_beveridge_vol*.txt` | IA Beveridge scans |
| Gill Body of Doctrinal Divinity | `systematic/gill_body_of_doctrinal_divinity.txt` | CCEL `g/gill/doctrinal` (S4) |
| Dabney Syllabus and Notes | `systematic/dabney_systematic_theology.txt` | IA `syllabusnotesofc00dabn` (S4) |
| Shedd Dogmatic Theology vol.1–3 | `systematic/shedd_dogmatic_theology_vol*.txt` | IA `dogmatictheology0{1,2,3}shed` (S4) |
| A.A. Hodge Outlines of Theology | `systematic/aa_hodge_outlines_of_theology.txt` | IA `outlinesoftheolo1878hodg` (S4) |
| Witsius Economy of the Covenants vol.1–2 | `systematic/witsius_economy_of_the_covenants_vol*.txt` | IA `oeconomyofcovena0{1,2}wits` (S4) |
| Boyce Abstract of Systematic Theology | `systematic/boyce_abstract_of_systematic_theology.txt` | IA `abstractofsystem00boyc` (S4) |
| Second Helvetic Confession | `reformed/second_helvetic_confession.txt` | CCEL Schaff Creeds III English appendix `creeds3.v.ix.html` (S4; anonymous/helvetic cache 404) |
| Scots Confession 1560 | `reformed/scots_confession_1560.txt` | CCEL `a/anonymous/scotconf` (S4) |
| Canons of Dort | `reformed/canons_of_dort.txt` | CCEL Schaff Creeds III Dort page only (S4) |

**Held out (do not train):** `continued_pretrain/data/holdouts_manual/heidelberg_catechism.txt` and `belgic_confession.txt`.

Calvin **treatises/sermons** (not Institutes) live under `data/puritans/calvin/` so they do not blow the 6% confession cap. Hodge/Calvin **biblical commentary** is Wave 3, under `data/puritans/`, capped, not this fetcher.

Do **not** add Turretin English (P&R/Dennison 1992–97 is in copyright). Latin Turretin is not useful for this English mix.

Re-fetch S4 only: `python continued_pretrain/scripts/11_fetch_confessions.py --s4`
"""


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Fetch PD confessions / systematic for CPT")
    p.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent.parent))
    p.add_argument("--force", action="store_true")
    p.add_argument("--s4", action="store_true", help="Fetch only S4 unique confession/ST (skip WCF/Institutes/1689)")
    p.add_argument("--only", default=None, help="Comma-separated S4 keys (implies --s4)")
    p.add_argument("--list", action="store_true")
    p.add_argument("--sleep", type=float, default=1.2)
    p.add_argument(
        "--rebuild-mix",
        action="store_true",
        help="Run 07 after fetch with --keep-all-spurgeon --max-other-weight 1.5",
    )
    args = p.parse_args(argv)

    if args.list:
        print("base:")
        for item in CATALOG:
            print(f"  {item['dest']:55s}  {item['title']}")
        print("s4:")
        for item in S4_CATALOG:
            print(f"  {item['key']:24s}  {item['dest']}")
        return

    repo = Path(args.repo_root).resolve()
    s4_only = bool(args.s4 or args.only)
    items = list(S4_CATALOG) if s4_only else list(CATALOG) + list(S4_CATALOG)
    if args.only:
        wanted = {x.strip().lower() for x in args.only.split(",") if x.strip()}
        items = [it for it in items if it.get("key", "").lower() in wanted]
        if not items:
            print(f"ERROR: no catalog keys matched {sorted(wanted)}")
            sys.exit(2)

    ok = fail = 0
    for item in items:
        key = item.get("key") or item["dest"]
        print(f"[{key}] {item['title']}")
        dest = repo / item["dest"]
        if try_urls(
            dest,
            item["urls"],
            keys_any=item.get("keys_any"),
            keys_all=item.get("keys_all"),
            min_chars=item.get("min_chars", 3000),
            force=args.force,
            sleep=args.sleep,
        ):
            ok += 1
        else:
            fail += 1

    if not s4_only:
        print("[1689 Second London Confession]")
        if try_fetch_1689(repo, args.force):
            ok += 1
        else:
            fail += 1

    root = repo / "data" / "confessions"
    total = 0
    print("\nInventory data/confessions:")
    for path in sorted(root.rglob("*.txt")):
        n = path.stat().st_size
        total += n
        print(f"  {path.relative_to(repo)}  {n:,} bytes")
    print(f"  TOTAL {total:,} bytes ({total / 1e6:.1f} MB)")
    print(f"Done ok={ok} fail={fail}")

    (root / "PROVENANCE.md").write_text(PROVENANCE, encoding="utf-8")

    if args.rebuild_mix:
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

    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
