"""
HCI/UX Keyword Extractor — v2 (Multi-Country)
==============================================
9 dil öğrenme uygulamasının son 12 aylık İngilizce yorumlarını
en çok indirme yapılan 5 ülkeden (US, IN, GB, AU, CA) çekerek
HCI/UX/öğrenme deneyimi odaklı yeni anahtar kelimeler üretir.

Mevcut 471 kelimeyle çakışma yoktur.
Çıktı: new_keywords_hci_ux_v2.csv  +  new_keywords_hci_ux_v2.xml
"""

import re, time, random, csv, os
from datetime import datetime, timezone, timedelta
from collections import Counter

# ── Konfigürasyon ────────────────────────────────────────────────────────────

MONTHS         = 24          # tüm uygulamalar için tek tip zaman penceresi
MAX_PER_APP    = 3000        # uygulama başına max yorum
MIN_FREQ_CURATED   = 5
MIN_FREQ_UNIGRAM   = 20
MIN_FREQ_BIGRAM    = 12
MIN_FREQ_TRIGRAM   = 8

# Test sonucu: lang="en" ile tüm ülkeler aynı global havuzu döndürüyor.
# reviewId'ler birebir örtüşüyor (test: Cambly US/GB/IN → %100 overlap).
# Bu nedenle çok ülke yaklaşımı yerine az yorumlu uygulamalar için
# zaman penceresi 24 aya genişletildi.
COUNTRY = "us"

# (app_name, app_id, play_store_url)
APPS = [
    ("Speak",      "com.selabs.speak",           "https://play.google.com/store/apps/details?id=com.selabs.speak"),
    ("Praktika",   "ai.praktika.android",         "https://play.google.com/store/apps/details?id=ai.praktika.android"),
    ("ELSA Speak", "us.nobarriers.elsa",          "https://play.google.com/store/apps/details?id=us.nobarriers.elsa"),
    ("Duolingo",   "com.duolingo",                "https://play.google.com/store/apps/details?id=com.duolingo"),
    ("Babbel",     "com.babbel.mobile.android.en","https://play.google.com/store/apps/details?id=com.babbel.mobile.android.en"),
    ("Busuu",      "com.busuu.android.enc",       "https://play.google.com/store/apps/details?id=com.busuu.android.enc"),
    ("Cambly",     "com.cambly.cambly",           "https://play.google.com/store/apps/details?id=com.cambly.cambly"),
    ("Preply",     "com.preply",                  "https://play.google.com/store/apps/details?id=com.preply"),
    ("HelloTalk",  "com.hellotalk",               "https://play.google.com/store/apps/details?id=com.hellotalk"),
]

# ── Mevcut 471 kelime (çakışma kontrolü) ─────────────────────────────────────
EXISTING = {k.lower().strip() for k in """
feedback
accurate feedback
false hope
marked as correct
mispronounce
pronunciation
speak correctly
AI voice
silent letters
grammar rules
misunderstands
glorified flashcard
speech recognition lenient
overly lenient
wrong correction
error detection
feedback depth
fluency check
pronunciation feedback
AI assessment
voice accuracy
repeats herself
no variety
scripted conversation
not detailed enough
subtle errors
no feedback automatically
always follows random plan
topic unpredictable
inaccurate
wrong answer
score incorrect
marks wrong
AI mistake
feedback easy to miss
feedback hard to find
instant correction
real-time correction
correction feels natural
no grammar explanation
lacks depth
brief feedback
actionable feedback
helpful correction
corrects my mistakes
transcribe
wrong language
conversation flow
buggy
doesn't register
speech not recognized
broken
fix sentence
delete sentence
glitch
drops
mistakes kanji for Chinese
speaks wrong language
crash when minimised
won't even open
stopped working
app crashes
connection issues
freezes
doesn't save progress
tutor did not show up
no connection
video glitched
slides freeze
messages not loading
lag
unresponsive
cuts off
stutters
recognition error
disconnects
technical issue
natural conversation flow
conversation feels forced
feels like interrogation
one-sided conversation
shallow conversation
repetitive exercises
too repetitive
lack of variety
no offline mode
offline access
tutor
real people
AI to chat with
native speaker
demonic voice
creepy voice
ChatGPT
fish not nets
AI answer
introverted
scared to speak
feels natural
robotic
human-like
real conversation
like a real person
replace a live tutor
scripted
animated role-play
sticks to a script
speaking anxiety
biometric data
AI mining operation
practice without fear
no judgment
natural
unnatural
authentic
feels robotic
like a bot
human feedback
personal tutor
tutor no show
tutor canceled
tutor didn't show up
no consequence for tutor
tutor unprepared
tutor indifferent
tutor blocked me
tutor quality varies
not certified
no teaching qualification
native speaker advantage
real person
human connection
personal relationship
tutor friendliness
tutor patience
great tutor
amazing teacher
tutor didn't prepare
unqualified tutor
poorly speaking English tutor
inconsistent tutor
tutor attitude
low pressure environment
speaking confidence
uncanny valley
3D avatar
animated avatar
avatar distracting
AI feels like a person
AI character personality
no fear of judgment
practice without pressure
relaxed environment
beginner
existing knowledge
level
overwhelming
unnecessary words
skip
mismatch
first principles
too advanced
A1
A2
incremental
proficiency
course structure repetitive
higher levels repetitive
little integration
one-size-fits-all
hyper-personalization
tailored learning
structured plan
progress tracking
adaptive
personalized learning path
goal-focused lessons
learning plan doesn't work
always random
doesn't adapt
customized
tailored
difficulty
too easy
too hard
my level
curriculum
progression
tutor adapts to my level
lesson style
structured lesson
no curriculum
unstructured
informal lesson
casual conversation practice
flexible schedule
lesson recording
homework
tutor matches learning style
goal-focused
tutor didn't follow plan
no lesson plan
surface answers
not organized
on time
rigid learning path
learning path resets
no spaced repetition
no vocabulary tracking
bite-sized lessons
well-paced
too simple
real-world context
artificial phrases
strange example sentences
not enough levels
content depth
shallow features
limited content
actually improved
saw progress
felt improvement
streak
energy
hearts
league
leaderboard
motivated
daily streak
obsessive compulsive
quit
dread
cap
energy system
cash grab
greedy
punished for using the app
locked out
energy depletes
perfect lesson drains energy
waiting for recharge
18 hours
habit loop
trust loop
drives people away
user anxiety
calculating energy costs
robotic answer machines
XP points
collectibles
reward
badge
daily goal
addictive
give up
lost motivation
boring
engagement
keep going
fun to use
enjoyable
engaging
no longer fun
feels like a game
too gamified
excessive gamification
intrinsic motivation
extrinsic reward
competitive
keeps me engaged
stopped using
uninstalled
deleted the app
came back to
interface
layout
navigation
touch
one hand
snappy
primitive
notification
open beta
airpods
calendar
full access
no back button
badly designed
very repetitive
silly screens
doesn't explain
copy-paste emails
closing tickets
support team is rubbish
hard to reach support
confusing platform
lesson management terrible
built-in navigation missing
chat box won't go away
images won't send
slow loading
simply never loads
UX
UI
usability
design
accessible
responsive
dark mode
login
sync
button
scroll
video call quality
screen sharing
virtual classroom
classroom freezes
enter classroom button
scheduling conflict
rescheduling
booking system
calendar sync
availability
on-demand
instant access
connection dropped
video quality poor
audio issues
whiteboard
screen share blurry
app not optimized
mobile app buggy
no centralized system
intuitive
not intuitive
easy to use
hard to use
user-friendly
cluttered
confusing interface
easy to navigate
hard to navigate
clean design
polished
well-organized
disorganized
seamless
friction
learning curve
confusing copy
vague explanations
unclear instructions
onboarding
restricted navigation
can't jump between lessons
linear path
no search function
notification overload
push notification
permission prompt
too many options
minimal design
outdated design
visually appealing
touch-friendly
smooth
laggy
premium
subscription
free trial
refund
cancel
auto renew
expired
deducted
tricks
customer service
minutes lost
money back
upsell
charged $250
shady sign up
misleading pricing
no refund
cancellation fee
false advertising
not willing to refund
annual subscription cannot be canceled
unauthorized debit
account deactivated without notice
subscription increases
pressure to pay
ad-heavy
unskippable ads
restricted free learning
convert to paid
dark patterns
dark UX
paywall
free tier
in-app purchase
billing
scam
hidden fee
worth it
overpriced
value for money
cancel anytime
unused lessons expired
lessons disappeared
paid for lessons not used
minutes don't roll over
unused minutes lost
strict refund policy
no cash refund
commission too high
trial lesson not paid
100% satisfaction guarantee
charged for missed lesson
account deactivated with money
subscription downgrade failed
funds frozen
blocked account
money not refunded
subscription renewed higher
no way to cancel
expiring minutes
per minute billing
confusing subscription tiers
unclear pricing
misleading trial
charged without notice
shady sign-up process
transparent pricing
no hidden costs
good value
not worth the money
too expensive
fairly priced
free version enough
free version too limited
forced to subscribe
upsell every lesson
great tutor bad platform
tutor good app bad
platform disappointing
service good app not
despite bad app
tutor makes up for it
platform lets me down
tutor accountability
no consequence for cancellation
tutor loyalty
favorite tutor banned
tutor deactivated
lost my teacher
teacher disappeared
tutor consistency
same tutor every week
tutor relationship
personal connection
real human interaction
human touch
authentic interaction
native speaker quality
cultural context
accent practice
natural speech patterns
conversational fluency
idioms from native
real world English
""".strip().split('\n') if k.strip()}

# ── HCI/UX curated term listesi ──────────────────────────────────────────────
CURATED_HCI_TERMS = [
    # Interaction patterns
    "tap to continue", "double tap", "long press", "swipe up", "swipe down",
    "swipe left", "swipe right", "pinch to zoom", "pull to refresh",
    "haptic feedback", "vibration feedback", "force touch",
    "gesture navigation", "back gesture", "home gesture",
    # UI components
    "progress bar", "loading screen", "loading spinner", "splash screen",
    "bottom sheet", "side menu", "hamburger menu", "floating button",
    "action button", "submit button", "next button", "skip button",
    "modal window", "pop up", "popup window", "dialog box", "alert box",
    "dropdown menu", "checkbox", "toggle switch", "radio button",
    "text input", "search bar", "search box", "filter option",
    "sort option", "tab bar", "bottom navigation", "top navigation",
    "status bar", "header", "footer", "banner", "card view",
    "list view", "grid view", "carousel", "slider", "stepper",
    "breadcrumb", "pagination", "infinite scroll", "load more",
    "empty state", "placeholder text", "hint text", "label",
    "icon", "thumbnail", "avatar", "profile picture",
    # UX quality
    "user experience", "user interface", "user flow", "user journey",
    "user testing", "usability testing", "a/b testing",
    "first time experience", "first launch", "first use",
    "onboarding experience", "setup process", "account creation",
    "sign up process", "log in process", "password reset",
    "forgot password", "email verification", "phone verification",
    "two factor", "biometric login", "face id", "fingerprint",
    "single sign on", "social login", "guest mode",
    # Performance UX
    "slow loading", "fast loading", "load time", "response time",
    "lag time", "delay", "buffer", "timeout", "session expired",
    "battery drain", "overheats", "storage space", "data usage",
    "offline mode", "sync issue", "cloud sync", "auto save",
    "data loss", "progress lost", "history gone", "reset progress",
    # Error handling
    "error message", "error screen", "crash report", "bug report",
    "force close", "unexpected error", "something went wrong",
    "try again", "retry button", "refresh button", "reload",
    "404 error", "server error", "network error", "timeout error",
    # Notification UX
    "push notification", "notification settings", "notification spam",
    "mute notifications", "notification badge", "alert sound",
    "daily reminder", "weekly reminder", "study reminder",
    "notification permission", "opt in", "opt out",
    # Accessibility
    "screen reader", "font size", "text size", "high contrast",
    "color blind", "accessibility mode", "voice over",
    "closed caption", "subtitle", "visual impairment",
    # Cognitive / learning UX
    "cognitive load", "mental effort", "information overload",
    "decision fatigue", "choice overload", "attention span",
    "distraction free", "focus mode", "study mode",
    "spaced repetition", "active recall", "retrieval practice",
    "interleaving", "elaborative interrogation", "self testing",
    "metacognition", "learning strategy", "study technique",
    "memory palace", "mnemonic", "association learning",
    "contextual learning", "immersive learning", "task based learning",
    "project based learning", "gamified learning", "microlearning",
    "adaptive learning", "personalized learning", "self paced",
    "blended learning", "hybrid learning", "flipped classroom",
    "social learning", "peer learning", "collaborative learning",
    "feedback mechanism", "immediate feedback", "delayed feedback",
    "formative feedback", "summative feedback", "corrective feedback",
    "diagnostic feedback", "motivational feedback",
    # Engagement
    "engagement loop", "reward loop", "feedback loop",
    "variable reward", "random reward", "points system",
    "achievement system", "badge system", "level system",
    "progress tracking", "goal setting", "milestone",
    "streak system", "combo streak", "streak freeze",
    "daily challenge", "weekly challenge", "monthly challenge",
    "time limit", "countdown timer", "speed challenge",
    "hearts system", "lives system", "energy bar",
    "coins", "gems", "diamonds", "currency", "virtual currency",
    "power up", "boost", "multiplier", "bonus round",
    "tournament", "competition mode", "challenge mode",
    "practice mode", "exam mode", "story mode",
    # Social UX
    "social feature", "friend list", "follow system",
    "comment section", "like button", "share button",
    "language partner", "practice partner", "study buddy",
    "group lesson", "group chat", "community forum",
    "discussion board", "native speaker match", "language exchange partner",
    "correction feature", "translation feature", "dictionary lookup",
    "word definition", "example usage", "pronunciation guide",
    # Subscription UX
    "subscription model", "freemium model", "premium plan",
    "trial period", "free trial", "trial expired", "upgrade prompt",
    "paywall experience", "in app purchase", "one time purchase",
    "lifetime access", "annual plan", "monthly plan",
    "price increase", "renewal notice", "cancellation flow",
    "refund process", "billing issue", "payment failed",
    # Support UX
    "help center", "faq section", "live chat support",
    "chatbot support", "ticket system", "response time",
    "customer support", "support quality", "issue resolution",
    # Settings UX
    "settings menu", "account settings", "privacy settings",
    "notification settings", "language settings", "display settings",
    "audio settings", "microphone settings", "camera settings",
    "playback speed", "font settings", "theme settings",
    "dark theme", "light theme", "night mode",
    # Multimodal
    "voice input", "voice command", "voice navigation",
    "speech recognition", "microphone access", "audio input",
    "text to speech", "speech to text", "read aloud",
    "listen mode", "speaking mode", "writing mode", "reading mode",
    "video lesson", "audio lesson", "text lesson", "interactive lesson",
    "live session", "recorded session", "replay feature",
    "speed control", "subtitle toggle",
    # Trust / privacy
    "data privacy", "privacy policy", "terms of service",
    "account security", "password strength", "secure connection",
    "data breach", "account hacked", "suspicious activity",
    "content moderation", "report feature", "block feature",
    "safe messaging", "age restriction", "parental control",
    # Device / platform
    "tablet support", "ipad support", "landscape mode", "portrait mode",
    "split screen", "picture in picture", "widget support",
    "cross platform", "web version", "desktop app", "browser extension",
    "app size", "download size", "update size",
    "force update", "update required", "version compatibility",
    # Learning flow UX
    "lesson structure", "lesson format", "lesson content",
    "exercise type", "question type", "answer format",
    "multiple choice question", "open ended question",
    "fill in blank", "word order", "sentence construction",
    "matching exercise", "listening exercise", "speaking exercise",
    "writing exercise", "reading comprehension", "grammar exercise",
    "vocabulary exercise", "pronunciation exercise", "dictation",
    "role play", "dialogue practice", "scenario based",
    "story based", "topic based", "theme based",
    "grammar point", "vocabulary set", "word list",
    "lesson review", "chapter review", "unit test",
    "placement test", "proficiency test", "level assessment",
    "skill assessment", "progress report", "performance stats",
    "accuracy rate", "completion rate", "mastery level",
    "weak area", "strength area", "recommended review",
    "review queue", "due review", "overdue review",
    "study plan", "weekly plan", "custom schedule",
    "time per day", "study session", "break reminder",
    "rest period", "fatigue warning", "session summary",
    "daily summary", "weekly summary", "monthly report",
]

# ── Stop words ────────────────────────────────────────────────────────────────
STOPWORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "is","it","this","that","be","are","was","were","has","have","had",
    "do","does","did","will","would","can","could","should","may","might",
    "not","no","so","if","as","by","from","up","out","my","me","we","you",
    "he","she","they","i","its","just","very","much","more","also","than",
    "then","when","there","here","what","which","who","how","all","some",
    "any","about","into","their","your","our","his","her","been","being",
    "after","before","because","like","even","only","still","now","get",
    "got","use","used","make","made","let","go","going","good","great",
    "really","too","well","way","time","app","it's","i've","i'm","don't",
    "can't","won't","they're","it's","there's","that's","didn't","doesn't",
    "wasn't","wouldn't","couldn't","shouldn't","haven't","hasn't","hadn't",
    "want","need","try","tried","said","says","every","each",
    "new","old","own","same","other","another","first","last","next",
    "take","taken","takes","taking","come","came","coming","find","found",
    "see","seen","know","knew","think","thought","feel","felt",
    "give","gave","given","keep","kept","look","looked","looks",
    "many","most","best","better","worse","worst","big","small","long","short",
    "years","months","weeks","days","hours","minutes","seconds","times",
    "people","person","user","users","anyone","everyone","someone","thing","things",
    "always","never","sometimes","often","usually","again","already","ever",
    "since","while","though","although","however","therefore","thus","hence",
    "bit","lot","kind","type","sort","few","little","quite","pretty",
}

GENERIC_PHRASES = {
    "language learning", "the language", "language and", "learning and",
    "learning the", "language in", "for learning", "in learning",
    "learning language", "language learning app", "best language",
    "the best", "learn language", "new language", "the app",
    "this app", "the lessons", "the lesson", "account and", "lesson and",
    "the word", "the voice", "the community", "and learning",
    "for language", "the best language", "for language learning",
    "learning new language", "learning the language", "language learning and",
    "in the language", "learning language and", "the voice recognition",
}

# ── Scraper ───────────────────────────────────────────────────────────────────
def scrape_app(app_id, app_name, months, max_reviews):
    try:
        from google_play_scraper import reviews, Sort
    except ImportError:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)
    collected = []
    token = None

    while len(collected) < max_reviews:
        try:
            batch, token = reviews(
                app_id, lang="en", country=COUNTRY,
                sort=Sort.NEWEST, count=200,
                continuation_token=token,
            )
        except Exception:
            break

        if not batch:
            break

        for r in batch:
            at = r.get("at")
            if at is None:
                continue
            if at.tzinfo is None:
                at = at.replace(tzinfo=timezone.utc)
            if at < cutoff:
                return collected
            text = r.get("content", "")
            if text and isinstance(text, str) and len(text) > 10:
                collected.append(text)

        if not token:
            break
        time.sleep(random.uniform(0.2, 0.5))

    return collected


# ── N-gram helpers ────────────────────────────────────────────────────────────
def extract_ngrams(text, n):
    words = re.findall(r"\b[a-z][a-z'-]{1,}\b", text.lower())
    if n == 1:
        return words
    return [" ".join(words[i:i+n]) for i in range(len(words)-n+1)]


def is_meaningful(phrase):
    if phrase.lower() in GENERIC_PHRASES:
        return False
    words = phrase.lower().split()
    if len(words) == 1 and words[0] in STOPWORDS:
        return False
    if all(w in STOPWORDS for w in words):
        return False
    if len(phrase) < 4:
        return False
    content = [w for w in words if w not in STOPWORDS and len(w) > 3]
    return bool(content)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    print("=" * 65)
    print("  HCI/UX Keyword Extractor v2 — Multi-Country")
    print(f"  Run: {run_date}")
    print("=" * 65)

    app_stats = {}
    all_texts = []

    for app_name, app_id, app_url in APPS:
        texts = scrape_app(app_id, app_name, MONTHS, MAX_PER_APP)
        all_texts.extend(texts)
        app_stats[app_name] = {
            "id": app_id, "url": app_url,
            "count": len(texts), "months_used": MONTHS,
        }
        print(f"  {app_name:12s}: {len(texts):5d} reviews")
        time.sleep(random.uniform(0.3, 0.7))

    total_reviews = len(all_texts)
    print(f"\nTotal unique reviews: {total_reviews}")

    # ── Keyword extraction ───────────────────────────────────────────────────
    print("\nExtracting keywords…")

    seed_words = set()
    for s in CURATED_HCI_TERMS:
        seed_words.update(s.lower().split())
    seed_words -= STOPWORDS

    uni_c, bi_c, tri_c = Counter(), Counter(), Counter()
    for text in all_texts:
        uni_c.update(extract_ngrams(text, 1))
        bi_c.update(extract_ngrams(text, 2))
        tri_c.update(extract_ngrams(text, 3))

    # Stage 1: n-gram candidates
    ngram_candidates = {}
    for phrase, freq in uni_c.items():
        if freq >= MIN_FREQ_UNIGRAM and is_meaningful(phrase) and phrase.lower() not in EXISTING:
            sc = len(set(phrase.lower().split()) & seed_words)
            if sc > 0:
                ngram_candidates[phrase] = {"freq": freq, "score": sc}
    for phrase, freq in bi_c.items():
        if freq >= MIN_FREQ_BIGRAM and is_meaningful(phrase) and phrase.lower() not in EXISTING:
            sc = len(set(phrase.lower().split()) & seed_words)
            if sc > 0:
                ngram_candidates[phrase] = {"freq": freq, "score": sc}
    for phrase, freq in tri_c.items():
        if freq >= MIN_FREQ_TRIGRAM and is_meaningful(phrase) and phrase.lower() not in EXISTING:
            sc = len(set(phrase.lower().split()) & seed_words)
            if sc > 0:
                ngram_candidates[phrase] = {"freq": freq, "score": sc}

    # Stage 2: curated matching
    combined = " ".join(all_texts).lower()
    curated_found = {}
    for term in CURATED_HCI_TERMS:
        if term.lower() in EXISTING:
            continue
        count = len(re.findall(r'\b' + re.escape(term.lower()) + r'\b', combined))
        if count >= MIN_FREQ_CURATED:
            curated_found[term] = count

    # Merge
    final = {}
    for term, freq in sorted(curated_found.items(), key=lambda x: x[1], reverse=True):
        final[term] = {"freq": freq, "source": "curated"}
    for phrase, meta in sorted(ngram_candidates.items(), key=lambda x: x[1]["freq"], reverse=True):
        if phrase.lower() not in final:
            words = phrase.lower().split()
            content = [w for w in words if w not in STOPWORDS and len(w) >= 5]
            if content:
                final[phrase] = {"freq": meta["freq"], "source": "extracted"}

    sorted_final = sorted(
        final.items(),
        key=lambda x: (1 if x[1]["source"] == "curated" else 0, x[1]["freq"]),
        reverse=True
    )

    n_curated   = sum(1 for _, m in sorted_final if m["source"] == "curated")
    n_extracted = len(sorted_final) - n_curated
    print(f"New keywords found: {len(sorted_final)} ({n_curated} curated + {n_extracted} extracted)")

    # ── Export ───────────────────────────────────────────────────────────────
    out_dir  = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(out_dir, "new_keywords_hci_ux_v2.csv")
    xml_path = os.path.join(out_dir, "new_keywords_hci_ux_v2.xml")

    # CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["=== KAYNAK BİLGİSİ ==="])
        w.writerow(["Analiz tarihi", run_date])
        w.writerow(["Kapsam", f"Son {MONTHS} ay"])
        w.writerow(["Toplam benzersiz yorum", total_reviews])
        w.writerow(["Ülke", "United States (us) — lang=en, tüm uygulamalar için tek tip"])
        w.writerow([])
        w.writerow(["=== UYGULAMA BAZLI YORUM SAYILARI ==="])
        w.writerow(["Uygulama", "App ID", "Play Store Linki", "Yorum Sayısı", "Kapsam (ay)"])
        for app_name, _, app_url in APPS:
            s = app_stats[app_name]
            w.writerow([app_name, s["id"], app_url, s["count"], s["months_used"]])
        w.writerow([])
        w.writerow(["=== YENİ HCI/UX ANAHTAR KELİMELER ==="])
        w.writerow(["keyword", "frequency_in_reviews", "source"])
        for phrase, meta in sorted_final:
            w.writerow([phrase, meta["freq"], meta["source"]])

    # XML
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write("<keyword_analysis>\n")
        f.write(f'  <meta run_date="{run_date}" months="{MONTHS}" country="{COUNTRY}" '
                f'total_reviews="{total_reviews}" '
                f'new_keywords="{len(sorted_final)}" '
                f'curated="{n_curated}" extracted="{n_extracted}"/>\n')
        f.write("  <sources>\n")
        for app_name, _, app_url in APPS:
            s = app_stats[app_name]
            safe_name = app_name.replace("&", "&amp;")
            f.write(f'    <app name="{safe_name}" id="{s["id"]}" '
                    f'reviews="{s["count"]}" months="{s["months_used"]}" url="{app_url}"/>\n')
        f.write("  </sources>\n")
        f.write("  <keywords>\n")
        for phrase, meta in sorted_final:
            safe = phrase.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            f.write(f'    <keyword freq="{meta["freq"]}" source="{meta["source"]}">'
                    f'{safe}</keyword>\n')
        f.write("  </keywords>\n")
        f.write("</keyword_analysis>\n")

    print(f"\n✅  CSV  → {csv_path}")
    print(f"✅  XML  → {xml_path}")
    print(f"\nTop 30 curated HCI/UX keywords:")
    shown = 0
    for phrase, meta in sorted_final:
        if meta["source"] == "curated":
            print(f"  [{meta['freq']:4d}x]  {phrase}")
            shown += 1
            if shown >= 30:
                break


if __name__ == "__main__":
    main()
