"""
Keyword Review Collector v2
============================
9 uygulamadan hem 6 hem 12 aylık keyword'li yorumları çeker.
Her yorum için: tarih, yazar, cinsiyet (isimden tahmin), rating,
thumbsUpCount (helpful oranı), keyword listesi, yorum metni.

Çıktılar (Desktop/learning app veriler/):
  keyword_reviews_6m.csv / .xml
  keyword_reviews_12m.csv / .xml
"""

import re, time, random, os, csv
from datetime import datetime, timezone, timedelta
from xml.sax.saxutils import escape

# ── Konfigürasyon ─────────────────────────────────────────────────────────────
COUNTRY  = "us"
MAX_PER_APP = 5000
OUT_DIR  = os.path.expanduser("~/Desktop/learning app veriler")

APPS = [
    ("Speak",      "com.selabs.speak",            "https://play.google.com/store/apps/details?id=com.selabs.speak"),
    ("Praktika",   "ai.praktika.android",          "https://play.google.com/store/apps/details?id=ai.praktika.android"),
    ("ELSA Speak", "us.nobarriers.elsa",           "https://play.google.com/store/apps/details?id=us.nobarriers.elsa"),
    ("Duolingo",   "com.duolingo",                 "https://play.google.com/store/apps/details?id=com.duolingo"),
    ("Babbel",     "com.babbel.mobile.android.en", "https://play.google.com/store/apps/details?id=com.babbel.mobile.android.en"),
    ("Busuu",      "com.busuu.android.enc",        "https://play.google.com/store/apps/details?id=com.busuu.android.enc"),
    ("Cambly",     "com.cambly.cambly",            "https://play.google.com/store/apps/details?id=com.cambly.cambly"),
    ("Preply",     "com.preply",                   "https://play.google.com/store/apps/details?id=com.preply"),
    ("HelloTalk",  "com.hellotalk",                "https://play.google.com/store/apps/details?id=com.hellotalk"),
]

# ── Keyword listesini yükle ───────────────────────────────────────────────────
def load_keywords():
    core = """feedback
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
real world English"""

    keywords = {k.strip().lower() for k in core.strip().split('\n') if k.strip()}

    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "new_keywords_hci_ux_v2.csv")
    if not os.path.exists(csv_path):
        # Masaüstünde çalışıyorsa orada ara
        csv_path = os.path.join(OUT_DIR, "new_keywords_hci_ux_v2.csv")
    if os.path.exists(csv_path):
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.reader(f)
            in_section = False
            for row in reader:
                if row and row[0] == "keyword":
                    in_section = True
                    continue
                if in_section and row and row[0]:
                    keywords.add(row[0].strip().lower())

    return sorted(keywords, key=len, reverse=True)


# ── Cinsiyet tahmini ──────────────────────────────────────────────────────────
try:
    import gender_guesser.detector as _gg
    _detector = _gg.Detector(case_sensitive=False)

    def guess_gender(name):
        if not name or name.lower() in ("anonymous", "a google user", ""):
            return "unknown"
        first = name.strip().split()[0]
        result = _detector.get_gender(first)
        mapping = {
            "male":           "male",
            "mostly_male":    "likely_male",
            "female":         "female",
            "mostly_female":  "likely_female",
            "andy":           "androgynous",
            "unknown":        "unknown",
        }
        return mapping.get(result, "unknown")
except ImportError:
    def guess_gender(_):
        return "unknown"


# ── Keyword eşleştirme ────────────────────────────────────────────────────────
def find_keywords(text, keyword_list):
    text_lower = text.lower()
    return [kw for kw in keyword_list
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower)]


# ── Scraper ───────────────────────────────────────────────────────────────────
def scrape_app(app_id, months, max_reviews):
    from google_play_scraper import reviews, Sort
    cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)
    collected, token = [], None

    while len(collected) < max_reviews:
        try:
            batch, token = reviews(
                app_id, lang="en", country=COUNTRY,
                sort=Sort.NEWEST, count=200,
                continuation_token=token,
            )
        except Exception as e:
            print(f"    ERROR: {e}")
            break
        if not batch:
            break

        hit_cutoff = False
        for r in batch:
            at = r.get("at")
            if at is None:
                continue
            if at.tzinfo is None:
                at = at.replace(tzinfo=timezone.utc)
            if at < cutoff:
                hit_cutoff = True
                break
            text = r.get("content", "")
            if text and len(text) > 10:
                collected.append({
                    "reviewId":    r.get("reviewId", ""),
                    "userName":    r.get("userName", "Anonymous"),
                    "date":        at.strftime("%Y-%m-%d"),
                    "rating":      r.get("score", 0),
                    "thumbsUp":    r.get("thumbsUpCount", 0),
                    "text":        text,
                })
        if hit_cutoff or not token:
            break
        time.sleep(random.uniform(0.2, 0.5))

    return collected


# ── Dosya yazıcılar ───────────────────────────────────────────────────────────
CSV_COLS = ["app", "date", "reviewer", "gender", "rating",
            "helpful_count", "keyword_count", "keywords", "review_text"]

def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS)
        w.writeheader()
        w.writerows(rows)

def write_xml(path, rows_by_app, run_date, months, total_reviews, total_matched):
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write("<review_corpus>\n")
        f.write(f'  <meta run_date="{run_date}" months="{months}" country="{COUNTRY}"\n')
        f.write(f'        total_reviews_fetched="{total_reviews}"\n')
        f.write(f'        total_reviews_matched="{total_matched}"\n')
        f.write(f'        gender_note="Inferred from first name via gender-guesser library. '
                f'unknown = name not recognized or anonymous user."/>\n')
        f.write("  <sources>\n")
        for app_name, app_id, app_url in APPS:
            f.write(f'    <app name="{escape(app_name)}" id="{app_id}" url="{app_url}"/>\n')
        f.write("  </sources>\n\n")

        for app_name, matched in rows_by_app:
            safe_name = escape(app_name)
            f.write(f'  <app name="{safe_name}" reviews_matched="{len(matched)}">\n')
            for r in matched:
                f.write(
                    f'    <review\n'
                    f'      date="{r["date"]}"\n'
                    f'      reviewer="{escape(r["reviewer"])}"\n'
                    f'      gender="{r["gender"]}"\n'
                    f'      rating="{r["rating"]}"\n'
                    f'      helpful_count="{r["helpful_count"]}"\n'
                    f'      keyword_count="{r["keyword_count"]}"\n'
                    f'      keywords="{escape(r["keywords"])}"\n'
                    f'    >{escape(r["review_text"])}</review>\n'
                )
            f.write(f'  </app>\n\n')
        f.write("</review_corpus>\n")


# ── Ana işlev ─────────────────────────────────────────────────────────────────
def collect(months, label):
    print(f"\n{'='*65}")
    print(f"  Collecting {label} reviews  ({months} months)")
    print(f"{'='*65}")

    keywords       = load_keywords()
    run_date       = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_reviews  = 0
    total_matched  = 0
    rows_by_app    = []
    all_csv_rows   = []

    for app_name, app_id, app_url in APPS:
        print(f"  {app_name:12s} … ", end="", flush=True)
        raw = scrape_app(app_id, months, MAX_PER_APP)
        print(f"{len(raw):5d} fetched  ", end="", flush=True)

        matched     = []
        csv_rows    = []
        for r in raw:
            found_kws = find_keywords(r["text"], keywords)
            if not found_kws:
                continue
            gender = guess_gender(r["userName"])
            row = {
                "app":          app_name,
                "date":         r["date"],
                "reviewer":     r["userName"],
                "gender":       gender,
                "rating":       r["rating"],
                "helpful_count": r["thumbsUp"],
                "keyword_count": len(found_kws),
                "keywords":     "|".join(found_kws),
                "review_text":  r["text"],
            }
            matched.append(row)
            csv_rows.append(row)

        rate = len(matched) / len(raw) * 100 if raw else 0
        print(f"→ {len(matched):5d} matched ({rate:.0f}%)")

        total_reviews  += len(raw)
        total_matched  += len(matched)
        rows_by_app.append((app_name, matched))
        all_csv_rows.extend(csv_rows)
        time.sleep(random.uniform(0.3, 0.8))

    os.makedirs(OUT_DIR, exist_ok=True)
    csv_path = os.path.join(OUT_DIR, f"keyword_reviews_{label}.csv")
    xml_path = os.path.join(OUT_DIR, f"keyword_reviews_{label}.xml")

    write_csv(csv_path, all_csv_rows)
    write_xml(xml_path, rows_by_app, run_date, months, total_reviews, total_matched)

    print(f"\n  TOPLAM  {total_reviews:6d} fetched  →  {total_matched:6d} matched")
    print(f"  ✅ CSV → {csv_path}")
    print(f"  ✅ XML → {xml_path}")
    return total_matched


if __name__ == "__main__":
    collect(months=6,  label="6m")
    collect(months=12, label="12m")
    print("\n\nTüm dosyalar hazır. Bu pencereyi kapatabilirsin.")
