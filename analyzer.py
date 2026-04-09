import re

# ── Preprocessing ──────────────────────────────────────────────────────────────

_LEET = str.maketrans({
    '4': 'a', '@': 'a', '3': 'e', '1': 'i', '!': 'i',
    '0': 'o', '5': 's', '$': 's', '7': 't', '+': 't',
    '8': 'b', '6': 'g', '9': 'g',
})

def preprocess(text: str) -> str:
    t = text.lower().translate(_LEET)
    # Collapse 3+ repeated chars: "kiiiill" → "kiil"
    t = re.sub(r'(.)\1{2,}', r'\1\1', t)
    # Collapse spaced single letters: "k i l l" → "kill"
    t = re.sub(r'(?<!\w)([a-z])( [a-z]){2,}(?!\w)', lambda m: m.group(0).replace(' ', ''), t)
    # Strip non-alphanumeric except spaces and apostrophes
    t = re.sub(r"[^\w\s']", ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


# ── Reusable sub-patterns ──────────────────────────────────────────────────────

_FUTURE = (
    r"(?:i'll|i will|i'm going to|i am going to|i'm gonna|i am gonna|"
    r"gonna|going to|about to|planning to|plan to|intend to|i want to|"
    r"i need to|i have to|i'm about to|watch me)"
)

_TARGET = r"(?:you|u|y'?all|him|her|them|your\s+family|ur\s+family|your\s+loved\s+ones|everyone\s+you\s+love|your\s+kids|your\s+children|your\s+parents|your\s+whole\s+family)"

_KILL_VERBS = (
    r"(?:kill|murder|slay|slaughter|execute|assassinate|eliminate|terminate|"
    r"neutralize|exterminate|butcher|annihilate|end|finish\s+off|take\s+out|"
    r"snuff\s+(?:you\s+)?out|wipe\s+(?:you\s+)?out|get\s+rid\s+of|"
    r"dispose\s+of|put\s+you\s+(?:six\s+feet\s+)?under|put\s+you\s+in\s+the\s+ground|"
    r"send\s+you\s+to\s+(?:hell|your\s+(?:maker|grave))|"
    r"get\s+(?:merked|bodied|smoked|clapped|dropped|wetted)|"
    r"catch\s+a\s+body|spin\s+the\s+block)"
)

_HARM_VERBS = (
    r"(?:hurt|harm|injure|maim|cripple|disable|"
    r"hit|punch|kick|slap|strike|swing\s+(?:at|on)|"
    r"beat(?:\s+(?:up|the\s+(?:hell|shit|life|crap)\s+out\s+of))?|"
    r"assault|attack|bash|batter|stomp|smash|pound|thrash|pummel|maul|"
    r"destroy|obliterate|demolish|annihilate|wreck|mess\s+up|"
    r"brutali[sz]e|f+u+c+k+\s+(?:you\s+)?up|"
    r"run\s+up\s+on|pull\s+up\s+on|fade|rush|jump|"
    r"put\s+hands\s+on|lay\s+hands\s+on)"
)


# ── Main threat pattern library ────────────────────────────────────────────────
# Format: { "Category": [(pattern, risk_score), ...] }

THREAT_PATTERNS: dict[str, list[tuple[str, int]]] = {

    # ── Murder / Death threats ────────────────────────────────────────────────
    "Murder / Death Threat": [
        # I'll + kill verb + target
        (_FUTURE + r".{0,60}" + _KILL_VERBS + r".{0,30}" + _TARGET, 92),
        # Kill verb directly + target
        (r"\b(?:kill|murder|slay|slaughter|execute|assassinate|butcher|annihilate)\b.{0,30}" + _TARGET, 90),
        # "You're dead / dead man walking"
        (r"\byou'?r?e?\s*(?:dead|as\s+good\s+as\s+dead|a\s+dead\s+(?:man|woman|person)|done\s+for|finished)\b", 88),
        # "You won't see tomorrow"
        (r"\byou\s+won'?t\s+(?:see|live\s+to\s+see)\s+(?:another|the\s+next)\s+(?:day|sunrise|morning|week)\b", 87),
        # Dead man walking / marked for death
        (r"\b(?:dead\s+(?:man|woman|person)\s+walking|marked\s+for\s+death)\b", 88),
        # "Put a bullet in you / put you in a coffin"
        (r"\b(?:put\s+(?:a\s+)?(?:bullet|round|slug|shot)\s+(?:in|through|between)|"
         r"put\s+you\s+in\s+(?:a\s+)?(?:box|coffin|grave|body\s+bag))\b.{0,20}" + _TARGET, 90),
        # Third-party commission: "have you killed / put a hit on you"
        (r"\b(?:have|get|put\s+a\s+(?:hit|bounty|price)\s+on|hired\s+someone\s+to|"
         r"send\s+someone\s+to)\b.{0,30}" + _TARGET + r".{0,20}"
         r"\b(?:killed|murdered|hurt|taken\s+(?:care\s+of|out)|dealt\s+with|eliminated)\b", 90),
        # "Going to get you / coming for your head"
        (r"\b(?:coming\s+for\s+your\s+(?:head|neck|life|blood)|"
         r"i'?m\s+going\s+to\s+get\s+you|i\s+will\s+get\s+you)\b", 85),
        # Watch your back (lower — implied)
        (r"\bwatch\s+your\s+(?:back|step|mouth)\b", 62),
    ],

    # ── Physical violence ─────────────────────────────────────────────────────
    "Physical Violence": [
        # Future intent + harm verb + target
        (_FUTURE + r".{0,50}" + _HARM_VERBS + r".{0,25}" + _TARGET, 82),
        # Choke / strangle
        (r"\b(?:choke|strangle|throttle|suffocate|asphyxiate)\b.{0,25}" + _TARGET, 85),
        # Specific body-part destruction
        (r"\b(?:break|snap|crush|smash|shatter|fracture|dislocate)\b.{0,20}\b(?:your|ur)\b.{0,15}"
         r"\b(?:neck|skull|spine|bones?|arm|leg|finger|hand|jaw|face|teeth|ribs?|kneecaps?)\b", 84),
        # Burn (person)
        (r"\b(?:burn|set\s+(?:on\s+fire|alight|ablaze)|torch|incinerate)\b.{0,25}" + _TARGET, 83),
        # Drown / poison
        (r"\b(?:drown|poison|drug|spike)\b.{0,25}" + _TARGET, 82),
        # Direct hit/punch/destroy + target (no future word needed)
        (r"\b(?:hit|punch|kick|slap|strike|smash|destroy|obliterate|demolish)\b.{0,25}" + _TARGET, 78),
        # Property arson tied to a person
        (r"\b(?:burn\s+(?:down|your)|torch|destroy|blow\s+up)\b.{0,25}\b(?:your|ur)\b.{0,15}"
         r"\b(?:house|home|car|vehicle|property|place|apartment)\b", 73),
        # "An hero" / "neck yourself" (internet slang used to encourage harm)
        (r"\b(?:an\s*-?\s*hero|neck\s+yourself|rope\s+yourself|toaster\s+bath)\b", 88),
    ],

    # ── Weapon threats ─────────────────────────────────────────────────────────
    "Weapon Threat": [
        # Shoot / gun down
        (r"\b(?:shoot|gun\s+(?:down|you)|cap|blast|unload|open\s+fire\s+on|"
         r"put\s+(?:one|two|shots?|rounds?|bullets?)\s+(?:in|through))\b.{0,30}" + _TARGET, 88),
        # Pull / aim a weapon
        (r"\b(?:pull|draw|point|aim|whip\s+out)\b.{0,20}\b(?:a\s+)?"
         r"(?:gun|pistol|rifle|shotgun|revolver|piece|strap|heat|glock|nine|weapon|firearm|uzi|ak)\b"
         r".{0,20}\b(?:at|on|toward)\b.{0,15}" + _TARGET, 88),
        # Stab / knife attack
        (r"\b(?:stab|shank|shiv|cut|slash|slice|gut|impale|knife)\b.{0,30}" + _TARGET, 86),
        # Knife / blade context alone
        (r"\b(?:knife|blade|shank|shiv|cleaver|machete|switchblade|razor)\b.{0,25}" + _TARGET, 82),
        # "I'm strapped / armed and coming for you"
        (r"\b(?:strapped|armed|packing|carrying|loaded)\b.{0,40}"
         r"\b(?:and\s+(?:i'll|i\s+will|gonna)|find|kill|hurt|come\s+for|coming\s+for)\b", 80),
        # "Come at you armed"
        (r"\bcome\s+(?:at|for)\s+you\b.{0,30}\b(?:strapped|armed|with\s+(?:a\s+)?(?:gun|knife|weapon|bat|pipe))\b", 83),
        # Baseball bat / blunt weapon
        (r"\b(?:beat|hit|crack|smash)\b.{0,20}\b(?:your|ur|you)\b.{0,10}"
         r"\b(?:with\s+a\s+(?:bat|pipe|club|wrench|hammer|brick|crowbar|stick))\b", 80),
    ],

    # ── Explosive / Mass attack / Terrorism ───────────────────────────────────
    "Explosive / Mass Attack": [
        # Bomb / explosive devices
        (r"\b(?:bomb|bombs?|bombing|detonate|detonation|explosives?|ied|c-?4|rdx|tnt|"
         r"pipe\s+bomb|car\s+bomb|suicide\s+(?:bomb|vest)|semtex|fertiliser\s+bomb|"
         r"improvised\s+(?:explosive|device))\b", 92),
        # Mass shooting planning
        (r"\b(?:mass\s+(?:shooting|killing|murder|attack|stabbing|casualt)|"
         r"school\s+shooting|active\s+shooter|rampage|killing\s+spree|murder\s+spree)\b", 95),
        # Shoot up a location
        (r"\b(?:shoot\s+up|shot\s+up|open\s+fire\s+(?:at|on|in)|"
         r"attack|bomb|blow\s+up)\b.{0,40}"
         r"\b(?:school|college|university|mall|church|mosque|synagogue|temple|"
         r"concert|club|bar|hospital|office|building|crowd|workplace|store|market|subway|train)\b", 95),
        # Terrorism
        (r"\b(?:terrorism|terrorist|terroris[sm]|jihad|martyr\s+operation|"
         r"holy\s+war|isis|al\s+qaeda|lone\s+wolf\s+attack)\b", 88),
        # Chemical / biological / radiological
        (r"\b(?:chemical\s+weapon|nerve\s+agent|poison\s+gas|sarin|vx\s+gas|"
         r"anthrax|bioweapon|biological\s+weapon|radiological|dirty\s+bomb)\b", 95),
        # Genocide / ethnic cleansing
        (r"\b(?:genocide|ethnic\s+cleansing|final\s+solution|"
         r"race\s+war|holocaust\s+(?:2|ii|again)|great\s+replacement)\b", 95),
    ],

    # ── Stalking / Location threats ───────────────────────────────────────────
    "Stalking / Location Threat": [
        # I know where you live / work / are
        (r"\b(?:i\s+know\s+where\s+you\s+(?:live|are|work|sleep|go)|"
         r"know\s+your\s+(?:address|location|home\s+address|house|school|workplace))\b", 83),
        # Been watching / tracking you
        (r"\b(?:been\s+(?:watching|following|tracking|stalking)\s+(?:you|u)|"
         r"i\s+see\s+you\s+every|watching\s+your\s+every\s+move|"
         r"i\s+know\s+your\s+routine|i\s+know\s+your\s+schedule)\b", 82),
        # Outside your location
        (r"\b(?:outside\s+your|near\s+your|at\s+your|by\s+your|in\s+front\s+of\s+your)\b"
         r".{0,15}\b(?:house|home|school|work|building|apartment|place|door|window)\b", 80),
        # Will find / hunt you down
        (r"\b(?:i'll\s+find\s+you|will\s+find\s+you|hunt\s+you\s+down|"
         r"track\s+you\s+down|come\s+to\s+your\s+(?:house|home|work|school)|"
         r"show\s+up\s+at\s+your|i\s+know\s+your\s+face)\b", 82),
        # I know your family
        (r"\b(?:i\s+know\s+(?:where\s+your|about\s+your)\s+"
         r"(?:family|kids?|children|parents?|wife|husband|partner|girlfriend|boyfriend|siblings?))\b", 85),
        # We're watching you
        (r"\b(?:we'?re\s+watching\s+(?:you|u)|we\s+know\s+where\s+you)\b", 80),
    ],

    # ── Sexual threats ────────────────────────────────────────────────────────
    "Sexual Threat": [
        # Rape / sexual assault
        (r"\b(?:i'll|i will|gonna|going\s+to)\b.{0,30}"
         r"\b(?:rape|sexually\s+assault|violate|force\s+myself\s+on)\b.{0,20}" + _TARGET, 93),
        (r"\b(?:rape|sexual\s+assault|gang\s+(?:rape|bang))\b.{0,20}" + _TARGET, 93),
        # Non-consensual sharing threats
        (r"\b(?:send|post|share|leak|distribute|upload|spread|blast)\b.{0,30}"
         r"\b(?:your|ur)\b.{0,20}"
         r"\b(?:nudes?|naked\s+(?:photos?|pictures?|pics?|images?|videos?)|"
         r"sex\s+(?:tape|video)|explicit\s+(?:photos?|images?|content)|"
         r"porn|intimate\s+(?:photos?|images?))\b", 90),
        # "Send me nudes or I'll"
        (r"\b(?:send\s+(?:me\s+)?(?:nudes?|naked\s+pics?|pics?)|"
         r"sleep\s+with\s+me|have\s+sex\s+with\s+me)\b.{0,40}"
         r"\b(?:or\s+(?:i'll|else|i\s+will|otherwise))\b", 90),
        # Drugging threat for assault
        (r"\b(?:spike|drug)\b.{0,20}\b(?:your|ur)\b.{0,15}\b(?:drink|food|water)\b", 85),
    ],

    # ── Cyber threats ─────────────────────────────────────────────────────────
    "Cyber Threat": [
        # Doxxing
        (r"\b(?:dox|doxx|dox(?:x)?ing)\b.{0,30}" + _TARGET, 80),
        (r"\b(?:leak|expose|post|publish|release|dump)\b.{0,30}"
         r"\b(?:your|ur)\b.{0,25}"
         r"\b(?:personal\s+(?:info|information|details?)|home\s+address|address|"
         r"phone\s+number|ip\s+(?:address)?|real\s+name|identity|location|"
         r"private\s+(?:info|data)|ssn|social\s+security)\b", 80),
        # Hacking
        (r"\b(?:hack|breach|break\s+into|access|compromise|take\s+over)\b.{0,25}"
         r"\b(?:your|ur)\b.{0,20}"
         r"\b(?:account(?:s)?|computer|device|phone|email|social\s+media|"
         r"profile|server|system|network|router)\b", 75),
        # Swatting
        (r"\b(?:swat|swatting|send\s+(?:swat|cops|police|feds|authorities)\s+to\s+your|"
         r"call\s+(?:a\s+)?(?:swat|bomb\s+threat|false\s+report)\s+on)\b.{0,25}" + _TARGET, 80),
        # Virus / malware threat
        (r"\b(?:send|install|drop|infect)\b.{0,20}"
         r"\b(?:a\s+)?(?:virus|malware|ransomware|trojan|keylogger|spyware)\b"
         r".{0,20}\b(?:on|in|to)\b.{0,10}\b(?:your|ur)\b", 75),
        # Account destruction
        (r"\b(?:destroy|ruin|report\s+(?:all\s+)?|terminate|get\s+banned|get\s+you\s+banned)\b.{0,25}"
         r"\b(?:your|ur)\b.{0,25}"
         r"\b(?:account(?:s)?|channel|page|profile|youtube|twitter|instagram|social\s+media)\b", 70),
    ],

    # ── Blackmail / Extortion ─────────────────────────────────────────────────
    "Blackmail / Extortion": [
        # Demand + or + threat verb (handles "ill" = "i'll" without apostrophe)
        (r"\b(?:pay|give\s+me|send\s+me|transfer|wire)\b.{0,50}"
         r"\bor\b.{0,30}\b(?:i'll|i\s+will|ill|i'm\s+going\s+to|gonna|else|otherwise)\b", 85),
        # Demand + or + threat verb (broad: catches "or ill post", "or i'll expose")
        (r"\b(?:pay|give\s+me|send\s+me|transfer|wire|do\s+(?:it|what\s+i\s+say))\b.{0,50}"
         r"\bor\b.{0,40}\b(?:post|share|leak|expose|distribute|release|publish|tell|send|hurt|kill|destroy|ruin|end)\b", 83),
        # Do as I say or
        (r"\b(?:do\s+(?:what\s+i\s+say|as\s+i\s+(?:say|tell\s+you)|it\s+now)|"
         r"follow\s+my\s+(?:orders?|instructions?|demands?))\b.{0,40}"
         r"\b(?:or\s+(?:else|i'll|i\s+will|ill))\b", 83),
        # Unless you / if you don't cooperate
        (r"\b(?:unless\s+you|if\s+you\s+don'?t|if\s+you\s+(?:fail|refuse|won'?t|don'?t\s+comply))\b"
         r".{0,60}\b(?:i'll|i\s+will|ill|gonna|i'm\s+going\s+to)\b", 82),
        # "or else I'll [threat]" — reversed order
        (r"\bor\s+(?:else\s+)?(?:i'll|i\s+will|ill|i'm\s+going\s+to|gonna)\s+"
         r"(?:post|share|leak|expose|tell|send|hurt|kill|destroy|ruin|publish|release)\b", 85),
        # I have evidence — will expose you
        (r"\b(?:i\s+have|i'?ve\s+got|i\s+(?:saved|recorded|captured|filmed|screenshotted))\b"
         r".{0,40}\b(?:evidence|proof|photos?|videos?|recordings?|screenshots?|your\s+nudes?|the\s+receipts?)\b"
         r".{0,50}\b(?:unless|or\s+(?:else|i'll|ill)|send\s+(?:it|them)|expose|share|leak|post|release)\b", 88),
        # Expose/leak your content unless you pay
        (r"\b(?:post|share|leak|expose|distribute|release|publish)\b.{0,40}"
         r"\b(?:your|ur)\b.{0,25}\b(?:photos?|nudes?|videos?|pics?|images?|content|info|details?)\b"
         r".{0,40}\b(?:unless|if\s+you\s+don'?t|pay|give\s+me|send\s+me)\b", 87),
        # Last warning / final chance
        (r"\b(?:last\s+(?:chance|warning|time|call)|final\s+warning|"
         r"this\s+is\s+your\s+(?:last|final)|one\s+last\s+(?:chance|warning))\b", 68),
        # Ransom
        (r"\b(?:ransom|pay\s+(?:up|me|the\s+ransom)|wire\s+(?:me\s+)?(?:money|funds|crypto|bitcoin))\b", 83),
        # "I have your account / data — pay me"
        (r"\b(?:i\s+own|i\s+control|i\s+have\s+access\s+to)\b.{0,30}"
         r"\b(?:your|ur)\b.{0,20}\b(?:account|data|files|computer|device)\b"
         r".{0,40}\b(?:pay|give\s+me|transfer|send\s+me)\b", 85),
    ],

    # ── Harassment / Intimidation ─────────────────────────────────────────────
    "Harassment / Intimidation": [
        # Make your life hell
        (r"\b(?:make\s+your\s+life\s+(?:hell|a\s+living\s+hell|miserable|a\s+nightmare)|"
         r"ruin\s+(?:your|ur)\s+(?:life|existence|world))\b", 70),
        # You'll regret this
        (r"\byou'?(?:'ll|will|re\s+going\s+to)\s+(?:regret|be\s+sorry|pay\s+for\s+this|"
         r"wish\s+you\s+(?:hadn't|never))\b", 65),
        # Coming for you / after you
        (r"\b(?:i'?m\s+(?:coming\s+for|after)\s+(?:you|u)|"
         r"coming\s+for\s+(?:you|u|your\s+(?:head|neck)))\b", 68),
        # Nowhere to hide / can't escape
        (r"\b(?:nowhere\s+to\s+(?:hide|run|go|escape)|"
         r"can'?t\s+(?:hide|run|escape)\s+from\s+(?:me|us|this))\b", 70),
        # Destroy reputation / social life
        (r"\b(?:destroy|ruin|end|ruin)\b.{0,25}\b(?:your|ur)\b.{0,15}"
         r"\b(?:reputation|life|career|future|relationships?|marriage|family|social\s+life)\b", 72),
        # Tell everyone your secrets
        (r"\b(?:tell|show|send|post|expose)\b.{0,20}"
         r"\b(?:everyone|the\s+whole\s+(?:school|office|internet|world)|"
         r"all\s+your|your\s+(?:friends|family|followers|coworkers|boss))\b"
         r".{0,30}\b(?:about\s+you|what\s+you\s+did|your\s+secret|the\s+truth)\b", 68),
        # "There will be consequences / you're going to pay"
        (r"\b(?:there\s+will\s+be\s+(?:consequences|repercussions)|"
         r"you'?(?:'ll|re\s+going\s+to)\s+pay\s+(?:for\s+this|dearly)|"
         r"consequences\s+are\s+coming)\b", 65),
        # "Consider yourself warned / this is a warning"
        (r"\b(?:consider\s+(?:this|yourself)\s+(?:a\s+)?(?:warning|warned)|"
         r"this\s+is\s+(?:your\s+(?:only|last)\s+)?warning|"
         r"i'?m\s+warning\s+you)\b", 62),
        # "You made a mistake messing with me"
        (r"\byou\s+(?:made\s+a\s+(?:big\s+)?mistake|fucked\s+up|messed\s+up)\s+"
         r"(?:messing|fucking|screwing|dealing)\s+with\s+(?:me|us)\b", 65),
    ],

    # ── Self-harm promotion ───────────────────────────────────────────────────
    "Self-Harm Promotion": [
        # KYS (very common abbreviation)
        (r"\bkys\b", 95),
        # Kill yourself — all variants
        (r"\b(?:go\s+)?(?:kill|hang|shoot|stab|poison)\s+(?:your|ur)s?(?:elf|elves)\b", 95),
        # "You should / deserve to die"
        (r"\byou\s+(?:should|deserve\s+to|need\s+to|ought\s+to|might\s+as\s+well)\s+die\b", 93),
        # "Why don't you just end it"
        (r"\b(?:why\s+don'?t\s+you\s+(?:just\s+)?(?:kill|end|die|hang)|"
         r"just\s+(?:kill|end|hang)\s+(?:your|ur)s?(?:elf)?|"
         r"do\s+(?:everyone|the\s+world|us\s+all)\s+a\s+favor\s+and\s+(?:die|kill\s+yourself))\b", 95),
        # Better off dead / world better without you
        (r"\b(?:better\s+off\s+(?:dead|gone)|"
         r"the\s+world\s+(?:is|would\s+be)\s+better\s+(?:off\s+)?without\s+you|"
         r"no\s+one\s+would\s+miss\s+you)\b", 92),
        # End it all
        (r"\b(?:just\s+end\s+it(?:\s+all)?|"
         r"end\s+(?:your|ur)\s+(?:life|suffering|existence|misery|pain)|"
         r"take\s+(?:your|ur)\s+(?:own\s+)?life)\b", 93),
        # Method + self (specific method instructions)
        (r"\b(?:rope|hang|overdose\s+on|slit\s+(?:your|ur)\s+(?:wrists?|throat)|"
         r"jump\s+off|in\s+front\s+of\s+a\s+(?:train|truck|bus|car)|"
         r"an\s*-?\s*hero|neck\s+yourself|toaster\s+bath|bridge\s+jump)\b", 94),
        # Worthless + die
        (r"\b(?:worthless|useless|pathetic|waste\s+of\s+(?:space|air|oxygen|life)|"
         r"nobody\s+(?:wants?|cares?|loves?|needs?|would\s+miss)\s+(?:you|u))\b"
         r".{0,60}\b(?:die|dead|kill\s+your?s?e?l?f?|end\s+it|disappear|go\s+away\s+forever)\b", 90),
        # No one loves you + die
        (r"\b(?:no\s+one|nobody)\s+(?:cares?|loves?|wants?|needs?|misses?|would\s+miss)\s+(?:you|u)\b"
         r".{0,50}\b(?:die|dead|kill|end\s+it|disappear)\b", 88),
        # "An hero" / neck yourself internet slang
        (r"\b(?:an\s*hero|neck\s+yourself|unalive\s+yourself|commit\s+(?:die|not\s+live))\b", 93),
    ],

    # ── Hate crime / group threats ────────────────────────────────────────────
    "Hate Crime / Group Threat": [
        # All [group] should die
        (r"\ball\s+\w+(?:\s+\w+)?\s+(?:should|must|need\s+to|deserve\s+to|ought\s+to)\s+"
         r"(?:die|be\s+(?:killed|eliminated|exterminated|eradicated|wiped\s+out)|suffer|burn|disappear)\b", 92),
        # Kill/eliminate all [group]
        (r"\b(?:kill|murder|eliminate|exterminate|wipe\s+out|get\s+rid\s+of|eradicate)\s+all\s+(?:the\s+)?\w+\b", 90),
        # Dehumanization + violence
        (r"\b(?:those\s+(?:animals?|vermin|parasites?|creatures?|subhumans?|rats?|cockroaches?|filth))\b"
         r".{0,40}\b(?:should|need\s+to|deserve\s+to)\s+(?:die|be\s+(?:killed|eliminated|exterminated))\b", 92),
        # Purge / cleanse
        (r"\b(?:purge|cleanse|exterminate|eradicate|eliminate|get\s+rid\s+of)\b.{0,20}"
         r"\b(?:them|those\s+\w+|the\s+\w+|all\s+\w+)\b", 85),
        # "Race war / holy war now"
        (r"\b(?:race\s+war\s+now|start\s+(?:a\s+)?race\s+war|holy\s+war|"
         r"jihad\s+against|crusade\s+against)\b", 90),
    ],

    # ── Organized / gang violence ─────────────────────────────────────────────
    "Organized Violence": [
        # Put a hit / bounty on someone
        (r"\b(?:put\s+a\s+(?:hit|bounty|price|contract)\s+on|"
         r"taken\s+(?:out\s+a\s+)?contract\s+on|hired\s+(?:someone|a\s+(?:hitman|shooter)))\b"
         r".{0,25}" + _TARGET, 88),
        # Send people after you
        (r"\b(?:send\s+(?:people|someone|my\s+(?:boys|guys|crew|people|homies|squad|team))|"
         r"have\s+(?:people|someone|my\s+boys))\b.{0,30}\b(?:after|for)\s+(?:you|u|him|her|them)\b", 85),
        # We know where you are / we're watching
        (r"\b(?:we'?re\s+watching\s+(?:you|u)|we\s+know\s+where\s+you|we\s+have\s+eyes\s+on\s+you)\b", 80),
        # "You're marked / you're next / on the list"
        (r"\byou'?r?e?\s+(?:marked|next|on\s+the\s+(?:list|hit\s+list)|a\s+target|flagged)\b", 75),
        # "My gang / my people will handle you"
        (r"\b(?:my\s+(?:gang|crew|people|boys|squad)|we)\b.{0,30}"
         r"\b(?:will|gonna|going\s+to)\b.{0,20}"
         r"\b(?:handle|deal\s+with|get|find|hurt|kill)\b.{0,15}" + _TARGET, 83),
    ],
}

# ── Standalone high-risk terms (no context needed) ────────────────────────────

STANDALONE_PATTERNS: list[tuple[str, int, str]] = [
    # Explosives
    (r"\bbombs?\b", 88, "Explosive / Mass Attack"),
    (r"\bexplosives?\b", 88, "Explosive / Mass Attack"),
    (r"\bdetonate\b", 88, "Explosive / Mass Attack"),
    (r"\bc-?4\b", 88, "Explosive / Mass Attack"),
    (r"\bpipe\s+bomb\b", 90, "Explosive / Mass Attack"),
    (r"\bsuicide\s+(vest|bomber)\b", 93, "Explosive / Mass Attack"),
    (r"\bchemical\s+weapon\b", 95, "Explosive / Mass Attack"),
    (r"\bnerve\s+agent\b", 95, "Explosive / Mass Attack"),
    # Terrorism
    (r"\bterror(?:ism|ist)s?\b", 85, "Explosive / Mass Attack"),
    (r"\bmass\s+(shooting|killing)\b", 95, "Explosive / Mass Attack"),
    (r"\bschool\s+shooting\b", 95, "Explosive / Mass Attack"),
    (r"\bactive\s+shooter\b", 95, "Explosive / Mass Attack"),
    # Self-harm
    (r"\bkys\b", 95, "Self-Harm Promotion"),
    (r"\ban\s*-?\s*hero\b", 92, "Self-Harm Promotion"),
    (r"\bunalive\s+(?:your|ur)s?(?:elf)?\b", 93, "Self-Harm Promotion"),
    # Organized
    (r"\bhit\s+(?:man|list)\b", 82, "Organized Violence"),
    (r"\bcontract\s+killer\b", 85, "Organized Violence"),
    # Cyber
    (r"\bdox+(?:ing)?\b", 78, "Cyber Threat"),
    (r"\bswatt?ing\b", 78, "Cyber Threat"),
    (r"\bransom(?:ware)?\b", 80, "Blackmail / Extortion"),
]


# ── Risk level ─────────────────────────────────────────────────────────────────

def _risk_level(score: int) -> str:
    if score == 0:   return "safe"
    if score < 60:   return "low"
    if score < 75:   return "medium"
    if score < 88:   return "high"
    return "critical"


# ── Main analysis function ────────────────────────────────────────────────────

def analyze_message(content: str) -> dict:
    preprocessed = preprocess(content)

    matched: list[str] = []
    categories: set[str] = set()
    max_score = 0

    # Standalone patterns first
    for pattern, score, cat in STANDALONE_PATTERNS:
        if re.search(pattern, preprocessed, re.IGNORECASE):
            if cat not in categories:
                matched.append(f"[{cat}] High-risk term")
            max_score = max(max_score, score)
            categories.add(cat)

    # Combination patterns
    for category, patterns in THREAT_PATTERNS.items():
        hit = False
        for pattern, score in patterns:
            try:
                if re.search(pattern, preprocessed, re.IGNORECASE):
                    max_score = max(max_score, score)
                    categories.add(category)
                    if not hit:
                        matched.append(category)
                        hit = True
            except re.error:
                continue

    risk_level = _risk_level(max_score)
    is_flagged = max_score >= 60

    return {
        "is_flagged": is_flagged,
        "risk_level": risk_level,
        "risk_score": max_score,
        "matched_patterns": matched,
        "categories": list(categories),
        "preprocessed": preprocessed,
    }
