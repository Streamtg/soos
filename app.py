cat > app.py <<'APPEOF'
"""
SoniTranslate Pro — CPU Version
Doblaje de video con IA
- Separación vocal/música
- Clonación de voz
- Velocidad adaptativa
- Cola de procesamiento
- UI responsive
"""

import os, gc, time, asyncio, tempfile, logging, subprocess, uuid, shutil
from pathlib import Path
from datetime import datetime
from collections import deque
from threading import Lock
import gradio as gr
import numpy as np

os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
os.environ["CT2_VERBOSE"] = "0"
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("SoniTranslate")

TEMP_DIR = Path(tempfile.gettempdir()) / "sonitranslate"
OUTPUT_DIR = TEMP_DIR / "output"
for d in [TEMP_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

MAX_DURATION = 600
MAX_QUEUE = 20
WHISPER_MODELS = ["tiny", "base", "small"]
TTS_ENGINES = ["Edge-TTS (Recomendado)", "gTTS (Google)", "Clonar Voz (Referencia)"]
SPEED_MODES = [
    "🔄 Adaptativa (sync original)", "🐢 Lenta (-20%)", "🚶 Normal (0%)",
    "🏃 Rápida (+15%)", "⚡ Muy rápida (+30%)", "🎚️ Personalizada",
]
NARR_STYLES = [
    "📰 Narrador / Noticias", "💼 Profesional / Formal",
    "😊 Conversacional / Casual", "🌟 Joven / Energético",
    "🧘 Calmado / Sereno", "👔 Maduro / Autoritario",
    "🌍 Multilingüe / Premium", "🔍 Todos",
]

# ── VOICES ──────────────────────────────────────────────────────
VSTYLES = {
    "📰 Narrador / Noticias": {
        "en-US-GuyNeural":"🇺🇸 Guy Male Narrator","en-US-ChristopherNeural":"🇺🇸 Christopher Male News",
        "en-US-EricNeural":"🇺🇸 Eric Male Narrator","en-US-RogerNeural":"🇺🇸 Roger Male Mature",
        "en-GB-RyanNeural":"🇬🇧 Ryan Male Narrator","en-GB-ThomasNeural":"🇬🇧 Thomas Male News",
        "es-ES-AlvaroNeural":"🇪🇸 Álvaro Male Narrador","es-ES-SaulNeural":"🇪🇸 Saúl Male Noticias",
        "es-MX-JorgeNeural":"🇲🇽 Jorge Male Narrador","es-MX-YagoNeural":"🇲🇽 Yago Male Narrador",
        "fr-FR-HenriNeural":"🇫🇷 Henri Male Narrateur","de-DE-ConradNeural":"🇩🇪 Conrad Male Narrator",
        "de-DE-RalfNeural":"🇩🇪 Ralf Male Narrator","pt-BR-AntonioNeural":"🇧🇷 Antonio Male Narrador",
        "pt-BR-HumbertoNeural":"🇧🇷 Humberto Male News","it-IT-DiegoNeural":"🇮🇹 Diego Male Narratore",
        "ja-JP-KeitaNeural":"🇯🇵 Keita Male Narrator","zh-CN-YunyangNeural":"🇨🇳 Yunyang Male News",
        "ko-KR-InJoonNeural":"🇰🇷 InJoon Male Narrator","ru-RU-DmitryNeural":"🇷🇺 Dmitry Male Narrator",
        "ar-SA-HamedNeural":"🇸🇦 Hamed Male Narrator",
    },
    "💼 Profesional / Formal": {
        "en-US-AriaNeural":"🇺🇸 Aria Female Professional","en-US-DavisNeural":"🇺🇸 Davis Male Professional",
        "en-US-NancyNeural":"🇺🇸 Nancy Female Professional","en-US-JasonNeural":"🇺🇸 Jason Male Formal",
        "en-GB-SoniaNeural":"🇬🇧 Sonia Female Professional","en-GB-LibbyNeural":"🇬🇧 Libby Female Professional",
        "en-GB-OliverNeural":"🇬🇧 Oliver Male Professional",
        "es-ES-IreneNeural":"🇪🇸 Irene Female Profesional","es-ES-EliasNeural":"🇪🇸 Elías Male Profesional",
        "es-MX-BeatrizNeural":"🇲🇽 Beatriz Female Profesional","es-MX-LibertoNeural":"🇲🇽 Liberto Male Profesional",
        "fr-FR-BrigitteNeural":"🇫🇷 Brigitte Female Pro","fr-FR-YvesNeural":"🇫🇷 Yves Male Pro",
        "de-DE-AmalaNeural":"🇩🇪 Amala Female Pro","de-DE-KillianNeural":"🇩🇪 Killian Male Formal",
        "pt-BR-DonatoNeural":"🇧🇷 Donato Male Pro","it-IT-IsabellaNeural":"🇮🇹 Isabella Female Pro",
        "ja-JP-DaichiNeural":"🇯🇵 Daichi Male Pro","zh-CN-YunjianNeural":"🇨🇳 Yunjian Male Pro",
    },
    "😊 Conversacional / Casual": {
        "en-US-JennyNeural":"🇺🇸 Jenny Female Conversational","en-US-AndrewNeural":"🇺🇸 Andrew Male Conversational",
        "en-US-MonicaNeural":"🇺🇸 Monica Female Conversational","en-US-BrandonNeural":"🇺🇸 Brandon Male Casual",
        "en-US-SaraNeural":"🇺🇸 Sara Female Casual","en-GB-EthanNeural":"🇬🇧 Ethan Male Casual",
        "es-ES-LiaNeural":"🇪🇸 Lía Female Conversacional","es-ES-NilNeural":"🇪🇸 Nil Male Casual",
        "es-MX-CandelaNeural":"🇲🇽 Candela Female Casual","es-MX-GerardoNeural":"🇲🇽 Gerardo Male Casual",
        "es-MX-LucianoNeural":"🇲🇽 Luciano Male Conversacional",
        "fr-FR-MauriceNeural":"🇫🇷 Maurice Male Casual","de-DE-BerndNeural":"🇩🇪 Bernd Male Casual",
        "pt-BR-FabioNeural":"🇧🇷 Fábio Male Casual","pt-BR-LeticiaNeural":"🇧🇷 Letícia Female Conversacional",
        "it-IT-CalimeroNeural":"🇮🇹 Calimero Male Casual","zh-CN-XiaohanNeural":"🇨🇳 Xiaohan Female Conversational",
    },
    "🌟 Joven / Energético": {
        "en-US-AshleyNeural":"🇺🇸 Ashley Female Young","en-US-JacobNeural":"🇺🇸 Jacob Male Young",
        "en-US-CoraNeural":"🇺🇸 Cora Female Cheerful","en-US-TonyNeural":"🇺🇸 Tony Male Cheerful",
        "en-GB-AbbiNeural":"🇬🇧 Abbi Female Young","en-GB-AlfieNeural":"🇬🇧 Alfie Male Young",
        "en-GB-HollieNeural":"🇬🇧 Hollie Female Bright",
        "es-ES-AbrilNeural":"🇪🇸 Abril Female Joven","es-ES-ArnauNeural":"🇪🇸 Arnau Male Joven",
        "es-ES-TrianaNeural":"🇪🇸 Triana Female Brillante","es-MX-LarissaNeural":"🇲🇽 Larissa Female Joven",
        "es-MX-PelayoNeural":"🇲🇽 Pelayo Male Joven",
        "fr-FR-CelesteNeural":"🇫🇷 Céleste Female Young","de-DE-KasperNeural":"🇩🇪 Kasper Male Young",
        "pt-BR-BrendaNeural":"🇧🇷 Brenda Female Young","pt-BR-GiovannaNeural":"🇧🇷 Giovanna Female Bright",
        "ja-JP-AoiNeural":"🇯🇵 Aoi Female Young","zh-CN-XiaoyiNeural":"🇨🇳 Xiaoyi Female Young",
    },
    "🧘 Calmado / Sereno": {
        "en-US-JaneNeural":"🇺🇸 Jane Female Calm","en-US-AmberNeural":"🇺🇸 Amber Female Warm",
        "en-US-SteffanNeural":"🇺🇸 Steffan Male Warm","en-GB-BellaNeural":"🇬🇧 Bella Female Warm",
        "en-GB-OliviaNeural":"🇬🇧 Olivia Female Calm",
        "es-ES-VeraNeural":"🇪🇸 Vera Female Serena","es-ES-EstrellaNeural":"🇪🇸 Estrella Female Cálida",
        "es-MX-CarlotaNeural":"🇲🇽 Carlota Female Cálida",
        "fr-FR-CoralieNeural":"🇫🇷 Coralie Female Warm","de-DE-ElkeNeural":"🇩🇪 Elke Female Warm",
        "de-DE-TanjaNeural":"🇩🇪 Tanja Female Calm",
        "pt-BR-ManuelaNeural":"🇧🇷 Manuela Female Warm","pt-BR-YaraNeural":"🇧🇷 Yara Female Calm",
        "it-IT-IrmaNeural":"🇮🇹 Irma Female Calm",
        "ja-JP-NanamiNeural":"🇯🇵 Nanami Female Calm","zh-CN-XiaoruiNeural":"🇨🇳 Xiaorui Female Calm",
    },
    "👔 Maduro / Autoritario": {
        "en-US-ElizabethNeural":"🇺🇸 Elizabeth Female Mature","en-US-RogerNeural":"🇺🇸 Roger Male Mature",
        "en-GB-ElliotNeural":"🇬🇧 Elliot Male Formal",
        "es-ES-DarioNeural":"🇪🇸 Darío Male Maduro","es-MX-CecilioNeural":"🇲🇽 Cecilio Male Formal",
        "es-MX-RenataNeural":"🇲🇽 Renata Female Madura",
        "fr-FR-AlainNeural":"🇫🇷 Alain Male Formal","fr-FR-ClaudeNeural":"🇫🇷 Claude Male Mature",
        "de-DE-GiselaNeural":"🇩🇪 Gisela Female Mature","de-DE-KlausNeural":"🇩🇪 Klaus Male Pro",
        "pt-BR-NicolauNeural":"🇧🇷 Nicolau Male Formal",
        "it-IT-BenignoNeural":"🇮🇹 Benigno Male Formal","it-IT-RinaldoNeural":"🇮🇹 Rinaldo Male Narrator",
        "zh-CN-YunzeNeural":"🇨🇳 Yunze Male Mature",
    },
    "🌍 Multilingüe / Premium": {
        "en-US-AvaNeural":"🇺🇸 Ava Female Premium",
        "en-US-AndrewMultilingualNeural":"🇺🇸 Andrew Male Multi",
        "en-US-AvaMultilingualNeural":"🇺🇸 Ava Female Multi",
        "en-US-EmmaMultilingualNeural":"🇺🇸 Emma Female Multi",
        "en-US-BrianMultilingualNeural":"🇺🇸 Brian Male Multi",
        "fr-FR-VivienneMultilingualNeural":"🇫🇷 Vivienne Female Multi",
        "fr-FR-RemyMultilingualNeural":"🇫🇷 Rémy Male Multi",
        "de-DE-SeraphinaMultilingualNeural":"🇩🇪 Seraphina Female Multi",
        "de-DE-FlorianMultilingualNeural":"🇩🇪 Florian Male Multi",
        "pt-BR-ThalitaMultilingualNeural":"🇧🇷 Thalita Female Multi",
        "it-IT-GiuseppeNeural":"🇮🇹 Giuseppe Male Multi",
        "ja-JP-MasaruMultilingualNeural":"🇯🇵 Masaru Male Multi",
        "ko-KR-HyunsuNeural":"🇰🇷 Hyunsu Male Multi",
    },
}

EXTRA = {
    "🇪🇸 ES":{"es-ES-ElviraNeural":"F","es-ES-LaiaNeural":"F","es-ES-TeoNeural":"M","es-ES-XimenaNeural":"F"},
    "🇲🇽 MX":{"es-MX-DaliaNeural":"F","es-MX-MarinaNeural":"F","es-MX-NuriaNeural":"F"},
    "🇦🇷 AR":{"es-AR-ElenaNeural":"F","es-AR-TomasNeural":"M"},
    "🇨🇴 CO":{"es-CO-GonzaloNeural":"M","es-CO-SalomeNeural":"F"},
    "🇨🇱 CL":{"es-CL-CatalinaNeural":"F","es-CL-LorenzoNeural":"M"},
    "🇵🇪 PE":{"es-PE-AlexNeural":"M","es-PE-CamilaNeural":"F"},
    "🇻🇪 VE":{"es-VE-PaolaNeural":"F","es-VE-SebastianNeural":"M"},
    "🇬🇧 UK":{"en-GB-MaisieNeural":"F","en-GB-NoahNeural":"M"},
    "🇦🇺 AU":{"en-AU-NatashaNeural":"F","en-AU-WilliamNeural":"M"},
    "🇮🇳 IN":{"en-IN-NeerjaNeural":"F","en-IN-PrabhatNeural":"M","hi-IN-SwaraNeural":"F","hi-IN-MadhurNeural":"M"},
    "🇫🇷 FR":{"fr-FR-DeniseNeural":"F","fr-FR-JeromeNeural":"M","fr-FR-JosephineNeural":"F"},
    "🇩🇪 DE":{"de-DE-KatjaNeural":"F","de-DE-ChristophNeural":"M","de-DE-LouisaNeural":"F","de-DE-MajaNeural":"F"},
    "🇧🇷 BR":{"pt-BR-FranciscaNeural":"F","pt-BR-ElzaNeural":"F","pt-BR-JulioNeural":"M","pt-BR-ValerioNeural":"M","pt-BR-LeilaNeural":"F"},
    "🇮🇹 IT":{"it-IT-ElsaNeural":"F","it-IT-CataldoNeural":"M","it-IT-FabiolaNeural":"F","it-IT-GianniNeural":"M",
               "it-IT-ImeldaNeural":"F","it-IT-PalmiraNeural":"F","it-IT-LisandroNeural":"M","it-IT-FiammaNeural":"F"},
    "🇯🇵 JP":{"ja-JP-AoiNeural":"F","ja-JP-MayuNeural":"F","ja-JP-NaokiNeural":"M","ja-JP-ShioriNeural":"F"},
    "🇰🇷 KR":{"ko-KR-SunHiNeural":"F","ko-KR-BongJinNeural":"M","ko-KR-GookMinNeural":"M",
               "ko-KR-JiMinNeural":"F","ko-KR-SeoHyeonNeural":"F","ko-KR-SoonBokNeural":"F"},
    "🇨🇳 CN":{"zh-CN-XiaoxiaoNeural":"F","zh-CN-YunxiNeural":"M","zh-CN-XiaoqiuNeural":"F",
               "zh-CN-YunfengNeural":"M","zh-CN-YunhaoNeural":"M","zh-CN-YunxiaNeural":"M"},
    "🇷🇺 RU":{"ru-RU-SvetlanaNeural":"F"},
    "🇸🇦 AR2":{"ar-SA-ZariyahNeural":"F","ar-EG-SalmaNeural":"F","ar-EG-ShakirNeural":"M"},
    "🇹🇷 TR":{"tr-TR-EmelNeural":"F","tr-TR-AhmetNeural":"M"},
    "🇳🇱 NL":{"nl-NL-ColetteNeural":"F","nl-NL-MaartenNeural":"M"},
    "🇵🇱 PL":{"pl-PL-AgnieszkaNeural":"F","pl-PL-MarekNeural":"M"},
    "🇸🇪 SE":{"sv-SE-SofieNeural":"F","sv-SE-MattiasNeural":"M"},
    "🇳🇴 NO":{"nb-NO-PernilleNeural":"F","nb-NO-FinnNeural":"M"},
    "🇩🇰 DK":{"da-DK-ChristelNeural":"F","da-DK-JeppeNeural":"M"},
    "🇫🇮 FI":{"fi-FI-NooraNeural":"F","fi-FI-HarriNeural":"M"},
    "🇬🇷 GR":{"el-GR-AthinaNeural":"F","el-GR-NestorasNeural":"M"},
    "🇨🇿 CZ":{"cs-CZ-VlastaNeural":"F","cs-CZ-AntoninNeural":"M"},
    "🇷🇴 RO":{"ro-RO-AlinaNeural":"F","ro-RO-EmilNeural":"M"},
    "🇭🇺 HU":{"hu-HU-NoemiNeural":"F","hu-HU-TamasNeural":"M"},
    "🇺🇦 UA":{"uk-UA-PolinaNeural":"F","uk-UA-OstapNeural":"M"},
    "🇻🇳 VN":{"vi-VN-HoaiMyNeural":"F","vi-VN-NamMinhNeural":"M"},
    "🇹🇭 TH":{"th-TH-PremwadeeNeural":"F","th-TH-NiwatNeural":"M"},
    "🇮🇩 ID":{"id-ID-GadisNeural":"F","id-ID-ArdiNeural":"M"},
    "🇵🇭 PH":{"fil-PH-BlessicaNeural":"F","fil-PH-AngeloNeural":"M"},
    "🇮🇱 IL":{"he-IL-HilaNeural":"F","he-IL-AvriNeural":"M"},
    "🏴 CA":{"ca-ES-JoanaNeural":"F","ca-ES-EnricNeural":"M"},
    "🏴 GL":{"gl-ES-SabelaNeural":"F","gl-ES-RoiNeural":"M"},
    "🏴 EU":{"eu-ES-AinhoaNeural":"F","eu-ES-AnderNeural":"M"},
    "🇮🇷 IR":{"fa-IR-DilaraNeural":"F","fa-IR-FaridNeural":"M"},
    "🇧🇩 BD":{"bn-BD-NabanitaNeural":"F","bn-BD-PradeepNeural":"M"},
    "🇵🇰 PK":{"ur-PK-UzmaNeural":"F","ur-PK-AsadNeural":"M"},
    "🇰🇪 KE":{"sw-KE-ZuriNeural":"F","sw-KE-RafikiNeural":"M"},
    "🇿🇦 ZA":{"af-ZA-AdriNeural":"F","af-ZA-WillemNeural":"M"},
}

def bsv():
    v=[]
    for s,d in VSTYLES.items():
        for i,desc in d.items(): v.append(f"{i} | {desc} | {s}")
    return v
def bav():
    v=[]
    for r,d in EXTRA.items():
        for i,g in d.items(): v.append(f"{i} | {g} | {r}")
    return v
SV=bsv(); AV=bav()
seen=set(); CMB=[]
for v in SV+AV:
    k=v.split("|")[0].strip()
    if k not in seen: seen.add(k); CMB.append(v)
TV=len(CMB)

def gvid(d): return d.split("|")[0].strip() if "|" in d else d.strip()

LANGS=["Afrikaans (af)","Arabic (ar)","Bengali (bn)","Bulgarian (bg)","Catalan (ca)",
"Chinese (zh)","Croatian (hr)","Czech (cs)","Danish (da)","Dutch (nl)","English (en)",
"Estonian (et)","Filipino (fil)","Finnish (fi)","French (fr)","Galician (gl)","German (de)",
"Greek (el)","Hebrew (he)","Hindi (hi)","Hungarian (hu)","Icelandic (is)","Indonesian (id)",
"Italian (it)","Japanese (ja)","Kazakh (kk)","Korean (ko)","Latvian (lv)","Lithuanian (lt)",
"Malay (ms)","Norwegian (nb)","Persian (fa)","Polish (pl)","Portuguese (pt)","Romanian (ro)",
"Russian (ru)","Serbian (sr)","Slovak (sk)","Slovenian (sl)","Spanish (es)","Swahili (sw)",
"Swedish (sv)","Tamil (ta)","Thai (th)","Turkish (tr)","Ukrainian (uk)","Urdu (ur)",
"Vietnamese (vi)","Welsh (cy)"]

def glc(d): return d.split("(")[-1].rstrip(")") if "(" in d else d

# ── QUEUE ───────────────────────────────────────────────────────
class VQ:
    def __init__(self):
        self.q=deque(maxlen=MAX_QUEUE);self.h=deque(maxlen=50);self.lk=Lock();self.cur=None;self.busy=False
    def add(self,d):
        j={"id":str(uuid.uuid4())[:8],"at":datetime.now().strftime("%H:%M:%S"),"p":0,**d}
        with self.lk:
            if len(self.q)>=self.q.maxlen: return None
            self.q.append(j)
        return j["id"]
    def nxt(self):
        with self.lk: return self.q.popleft() if self.q else None
    def st(self):
        with self.lk:
            l=["| # | ID | Estado | Info |","|---|---|---|---|"]
            if self.cur:
                j=self.cur; l.append(f"| ▶ | `{j['id']}` | 🔄 {j.get('p',0):.0%} | {j.get('fn','?')[:25]} → {j.get('td','')} |")
            for i,j in enumerate(self.q):
                l.append(f"| {i+1} | `{j['id']}` | ⏳ | {j.get('fn','?')[:25]} → {j.get('td','')} |")
            if not self.cur and not self.q: l.append("| - | - | 📭 Vacía | - |")
            return "\n".join(l)
    def hi(self):
        if not self.h: return "*Sin historial*"
        l=["| ID | ✓ | Tiempo |","|---|---|---|"]
        for j in reversed(list(self.h)):
            l.append(f"| `{j['id']}` | {'✅' if j.get('rv') else '❌'} | {j.get('el','?')} |")
        return "\n".join(l)
    def done(self,j,v,s,el):
        j["rv"]=v;j["rs"]=s;j["el"]=el
        with self.lk: self.h.append(j);self.cur=None
vq=VQ()

# ── UTILS ───────────────────────────────────────────────────────
def exa(vp,out=None,sr=16000):
    out=out or tempfile.mktemp(suffix=".wav")
    subprocess.run(['ffmpeg','-y','-i',vp,'-vn','-acodec','pcm_s16le','-ar',str(sr),'-ac','1',out],capture_output=True,check=True,timeout=300)
    return out

def exs(vp,out=None):
    out=out or tempfile.mktemp(suffix=".wav")
    subprocess.run(['ffmpeg','-y','-i',vp,'-vn','-acodec','pcm_s16le','-ar','44100','-ac','2',out],capture_output=True,check=True,timeout=300)
    return out

def gd(p):
    try: return float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',p],capture_output=True,text=True,check=True).stdout.strip())
    except: return 0.0

def ft(s):
    h,m,sc=int(s//3600),int((s%3600)//60),int(s%60)
    return f"{h:02d}:{m:02d}:{sc:02d}" if h else f"{m:02d}:{sc:02d}"

def sts(s):
    return f"{int(s//3600):02d}:{int((s%3600)//60):02d}:{int(s%60):02d},{int((s%1)*1000):03d}"

def sepvoc(ap,od=None):
    import soundfile as sf, librosa
    od=od or tempfile.mkdtemp(prefix="sep_")
    vp,bp=os.path.join(od,"v.wav"),os.path.join(od,"b.wav")
    try:
        y,sr=librosa.load(ap,sr=44100,mono=False)
        if y.ndim==1:
            S=librosa.stft(y,n_fft=2048,hop_length=512); Sm,Sp=np.abs(S),np.angle(S)
            Sh,_=librosa.decompose.hpss(Sm,margin=3.0)
            fq=librosa.fft_frequencies(sr=sr,n_fft=2048)
            mk=np.zeros_like(Sm)
            for i,f in enumerate(fq):
                if 100<=f<=8000: mk[i,:]=1.0
            vS=Sh*mk; bS=np.maximum(Sm-vS,0)
            sf.write(vp,librosa.istft(vS*np.exp(1j*Sp),hop_length=512),sr)
            sf.write(bp,librosa.istft(bS*np.exp(1j*Sp),hop_length=512),sr)
        else:
            c=(y[0]+y[1])/2.0
            S=librosa.stft(c,n_fft=2048,hop_length=512); Sm,Sp=np.abs(S),np.angle(S)
            fq=librosa.fft_frequencies(sr=sr,n_fft=2048)
            for i,f in enumerate(fq):
                if f<80 or f>10000: Sm[i,:]*=0.1
            va=librosa.istft(Sm*np.exp(1j*Sp),hop_length=512)
            ba=c-va[:len(c)] if len(va)>=len(c) else c
            if len(ba)<len(c): ba=np.pad(ba,(0,len(c)-len(ba)))
            sf.write(vp,va,sr); sf.write(bp,ba[:len(c)],sr)
        return vp,bp
    except Exception as e:
        logger.warning(f"Sep: {e}"); shutil.copy2(ap,vp)
        try:
            y2,sr2=sf.read(ap)
            if y2.ndim>1: y2=y2.mean(axis=1)
            sf.write(bp,np.zeros_like(y2),sr2)
        except: subprocess.run(['ffmpeg','-y','-f','lavfi','-i','anullsrc=r=44100:cl=mono','-t','1',bp],capture_output=True)
        return vp,bp

def clonev(ref,tgt,out):
    import soundfile as sf, librosa
    try:
        ry,rsr=librosa.load(ref,sr=22050); rf=librosa.yin(ry,fmin=60,fmax=500,sr=rsr)
        rv=rf[rf>0]; rp=np.median(rv) if len(rv)>0 else 200
        ty,tsr=librosa.load(tgt,sr=22050); tf=librosa.yin(ty,fmin=60,fmax=500,sr=tsr)
        tv=tf[tf>0]; tp=np.median(tv) if len(tv)>0 else 200
        sh=np.clip(12*np.log2(rp/tp),-6,6) if rp>0 and tp>0 else 0
        if abs(sh)>0.5:
            try:
                import pyrubberband as pyrb
                sf.write(out,pyrb.pitch_shift(ty,sr=tsr,n_steps=float(sh)),tsr); return out
            except:
                f=2**(sh/12)
                subprocess.run(['ffmpeg','-y','-i',tgt,'-af',f'asetrate={tsr}*{f:.4f},aresample={tsr}',out],capture_output=True,check=True)
                return out
        shutil.copy2(tgt,out); return out
    except: shutil.copy2(tgt,out); return out

def dotrans(ap,ms="base",sl=None,pcb=None):
    from faster_whisper import WhisperModel
    m=WhisperModel(ms,device="cpu",compute_type="int8")
    kw={"beam_size":3,"vad_filter":True,"vad_parameters":dict(min_silence_duration_ms=500),"word_timestamps":True}
    if sl and sl!="auto": kw["language"]=sl
    sg,info=m.transcribe(ap,**kw)
    segs=[]
    for i,s in enumerate(sg):
        d={"id":i,"start":s.start,"end":s.end,"text":s.text.strip(),"dur":s.end-s.start}
        segs.append(d)
        if pcb: pcb(min(s.end/max(info.duration,1),1.0))
    del m; gc.collect()
    return segs, info.language

def dotransl(segs,src="auto",tgt="en",pcb=None):
    from deep_translator import GoogleTranslator
    if src==tgt: return segs
    res=[]
    for i,s in enumerate(segs):
        try:
            t=GoogleTranslator(source=src,target=tgt).translate(s["text"])
            ns=s.copy(); ns["orig"]=s["text"]; ns["text"]=t or s["text"]; res.append(ns)
        except: res.append(s.copy())
        if pcb: pcb((i+1)/len(segs))
    return res

async def etg(t,v,p,r="+0%",pi="+0Hz"):
    import edge_tts; await edge_tts.Communicate(text=t,voice=v,rate=r,pitch=pi).save(p)

def getrate(m,cv=0):
    if "Adaptativa" in m: return "+0%",True
    elif "Lenta" in m: return "-20%",False
    elif "Normal" in m: return "+0%",False
    elif "Rápida" in m and "Muy" not in m: return "+15%",False
    elif "Muy" in m: return "+30%",False
    elif "Personal" in m: return (f"+{int(cv)}%" if cv>=0 else f"{int(cv)}%"),False
    return "+0%",False

def atc(sp):
    fs=[];r=sp
    while r>2: fs.append("atempo=2.0");r/=2
    while r<0.5: fs.append("atempo=0.5");r/=0.5
    fs.append(f"atempo={r:.4f}");return ",".join(fs)

def dotts(text,voice,out,eng="edge_tts",lang="en",rate="+0%",pitch="+0Hz",ref=None,adp=False,odur=0):
    try:
        if eng=="clone" and ref:
            bv=voice or "en-US-GuyNeural"
            t1=out.replace(".wav","_b.mp3"); asyncio.run(etg(text,bv,t1,rate,pitch))
            t2=out.replace(".wav","_b.wav")
            subprocess.run(['ffmpeg','-y','-i',t1,'-acodec','pcm_s16le','-ar','24000','-ac','1',t2],capture_output=True,check=True)
            clonev(ref,t2,out)
            for f in[t1,t2]:
                if os.path.exists(f): os.remove(f)
        elif eng=="edge_tts":
            mp=out.replace(".wav",".mp3"); asyncio.run(etg(text,voice,mp,rate,pitch))
            subprocess.run(['ffmpeg','-y','-i',mp,'-acodec','pcm_s16le','-ar','24000','-ac','1',out],capture_output=True,check=True)
            if os.path.exists(mp): os.remove(mp)
        elif eng=="gtts":
            from gtts import gTTS; mp=out.replace(".wav",".mp3")
            gTTS(text=text,lang=lang).save(mp)
            subprocess.run(['ffmpeg','-y','-i',mp,'-acodec','pcm_s16le','-ar','24000','-ac','1',out],capture_output=True,check=True)
            if os.path.exists(mp): os.remove(mp)
        if adp and odur>0 and os.path.exists(out):
            td=gd(out)
            if td>0:
                r=td/odur
                if r>1.1:
                    nr=f"+{min(int((r-1)*100),50)}%"
                    if eng in("edge_tts","clone"):
                        v2=voice or "en-US-GuyNeural"; mp=out.replace(".wav","_a.mp3")
                        asyncio.run(etg(text,v2,mp,nr,pitch))
                        subprocess.run(['ffmpeg','-y','-i',mp,'-acodec','pcm_s16le','-ar','24000','-ac','1',out],capture_output=True,check=True)
                        if os.path.exists(mp): os.remove(mp)
                        if eng=="clone" and ref:
                            tmp=out.replace(".wav","_c.wav"); shutil.copy2(out,tmp); clonev(ref,tmp,out)
                            if os.path.exists(tmp): os.remove(tmp)
                fd=gd(out)
                if fd>0 and abs(fd-odur)/odur>.15:
                    st=out.replace(".wav","_s.wav"); tempo=max(.5,min(2,fd/odur))
                    try:
                        subprocess.run(['ffmpeg','-y','-i',out,'-filter:a',atc(tempo),st],capture_output=True,check=True)
                        shutil.move(st,out)
                    except: pass
        return out
    except Exception as e: logger.error(f"TTS: {e}"); return None

def mksrt(segs):
    l=[]
    for i,s in enumerate(segs,1): l+=[str(i),f"{sts(s['start'])} --> {sts(s['end'])}",s["text"],""]
    return "\n".join(l)

# ── PIPELINE ────────────────────────────────────────────────────
def pipeline(job,progress=None):
    t0=time.time()
    try:
        vp=job.get("vp")
        if not vp or not os.path.exists(vp): return None,None,"❌ No video"
        dur=gd(vp)
        if dur<=0: return None,None,"❌ Can't read"
        if dur>MAX_DURATION: return None,None,f"❌ Too long ({ft(dur)})"

        vm=job.get("vm","keep_bg"); ref=job.get("ref"); sm=job.get("sm","🚶 Normal (0%)")
        cs=job.get("cs",0); rs,adp=getrate(sm,cs)
        tp=job.get("tp",0); ps=f"+{int(tp)}Hz" if tp>=0 else f"{int(tp)}Hz"
        ec=job.get("te",TTS_ENGINES[0])
        eng="edge_tts"
        if "gTTS" in ec: eng="gtts"
        elif "Clonar" in ec: eng="clone"

        if progress: progress(0.05,desc=f"🎵 [{job['id']}] Audio...")
        bp=None
        if vm=="keep_bg":
            if progress: progress(0.08,desc=f"🎼 [{job['id']}] Separando...")
            sa=exs(vp); _,bp=sepvoc(sa)
        atx=exa(vp)

        if progress: progress(0.15,desc=f"📝 [{job['id']}] Whisper...")
        sc=glc(job["sl"]) if job["sl"]!="Auto Detect" else None
        def p1(p):
            if progress: progress(0.15+p*.30,desc=f"📝 [{job['id']}] {p:.0%}")
        segs,dl=dotrans(atx,job.get("wm","base"),sc,p1)
        if not segs: return None,None,"❌ No speech"

        if progress: progress(0.47,desc=f"🌐 [{job['id']}] Traduciendo...")
        tc=glc(job["tl"])
        def p2(p):
            if progress: progress(0.47+p*.13,desc=f"🌐 [{job['id']}] {p:.0%}")
        tr=dotransl(segs,dl or "auto",tc,p2)
        srt=mksrt(tr)

        if progress: progress(0.60,desc=f"🗣️ [{job['id']}] TTS...")
        td=tempfile.mkdtemp(prefix="tts_"); vid=gvid(job.get("tv","en-US-GuyNeural")); nt=len(tr)
        for i,seg in enumerate(tr):
            txt=seg.get("text","").strip()
            if not txt: seg["ap"]=None; continue
            op=os.path.join(td,f"s_{i:04d}.wav")
            seg["ap"]=dotts(txt,vid,op,eng,tc,rs,ps,ref,adp,seg.get("dur",0))
            if progress: progress(0.60+((i+1)/nt)*.22,desc=f"🗣️ [{job['id']}] {i+1}/{nt}")

        if progress: progress(0.84,desc=f"🔊 [{job['id']}] Merge...")
        import soundfile as sf
        sr=24000; ns_=int(dur*sr); tl=np.zeros(ns_,dtype=np.float32)
        for seg in tr:
            ap=seg.get("ap")
            if not ap or not os.path.exists(ap): continue
            try:
                a,asr=sf.read(ap)
                if a.ndim>1: a=a.mean(axis=1)
                if asr!=sr:
                    import librosa; a=librosa.resample(a,orig_sr=asr,target_sr=sr)
                ss=int(seg["start"]*sr)
                if ss>=ns_: continue
                e=min(ss+len(a),ns_); tl[ss:e]+=a[:e-ss].astype(np.float32)
            except: pass
        mx=np.max(np.abs(tl))
        if mx>0: tl=tl/mx*.92
        mg=tempfile.mktemp(suffix=".wav"); sf.write(mg,tl,sr)

        if progress: progress(0.90,desc=f"🎬 [{job['id']}] Video...")
        out=os.path.join(str(OUTPUT_DIR),f"tr_{job['id']}_{int(time.time())}.mp4")
        if vm=="keep_bg" and bp and os.path.exists(bp):
            bv=job.get("bv",25)/100
            cmd=['ffmpeg','-y','-i',vp,'-i',mg,'-i',bp,'-filter_complex',
                 f'[1:a]volume=1.0[t];[2:a]volume={bv}[b];[t][b]amix=inputs=2:duration=first[a]',
                 '-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-shortest',out]
        elif vm=="replace_all":
            cmd=['ffmpeg','-y','-i',vp,'-i',mg,'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-shortest',out]
        else:
            bv=job.get("bv",15)/100
            cmd=['ffmpeg','-y','-i',vp,'-i',mg,'-filter_complex',
                 f'[0:a]volume={bv}[o];[1:a]volume=1.0[t];[o][t]amix=inputs=2:duration=first[a]',
                 '-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-shortest',out]
        subprocess.run(cmd,capture_output=True,check=True,timeout=600)
        el=ft(time.time()-t0)
        st=f"✅ **`{job['id']}`** en {el}\n\n| | |\n|---|---|\n| 📊 | {ft(dur)} |\n| 🔤 | {dl} |\n| 🎯 | {job['tl']} |\n| 📝 | {len(segs)} segs |\n| 🎤 | `{vid}` |\n| ⚡ | {sm} |"
        return out,srt,st
    except Exception as e:
        logger.error(f"Err: {e}",exc_info=True); return None,None,f"❌ {e}"

# ── HANDLERS ────────────────────────────────────────────────────
def addq(v,yt,sl,tl,wm,te,tv,sm,cs,tp,vm,bv,ra):
    vp,fn=None,"?"
    if v: vp=v;fn=Path(v).name[:20] if isinstance(v,str) else "upload"
    elif yt and yt.strip():
        try:
            dd=tempfile.mkdtemp(prefix="yt_")
            subprocess.run(['yt-dlp','--format','best[height<=480]','--merge-output-format','mp4',
                           '--output',os.path.join(dd,'%(title).40s.%(ext)s'),'--no-playlist',yt.strip()],
                          capture_output=True,check=True,timeout=180)
            for f in os.listdir(dd):
                if f.endswith('.mp4'): vp=os.path.join(dd,f);fn=f[:20];break
            if not vp: return "❌ YT fail",vq.st()
        except Exception as e: return f"❌ {e}",vq.st()
    else: return "❌ Need video",vq.st()
    jid=vq.add({"vp":vp,"fn":fn,"sl":sl,"tl":tl,"td":tl,"wm":wm,"te":te,"tv":tv,"sm":sm,"cs":cs,"tp":tp,"vm":vm,"bv":bv,"ref":ra})
    if not jid: return f"❌ Full ({MAX_QUEUE})",vq.st()
    return f"✅ **{jid}** — {fn}",vq.st()

def procq(progress=gr.Progress(track_tqdm=True)):
    if vq.busy: return None,None,"⚠️ Busy",vq.st(),vq.hi()
    vq.busy=True;lv=ls=None;ast=[]
    try:
        n,tt=0,len(vq.q)
        while True:
            j=vq.nxt()
            if not j: break
            n+=1;vq.cur=j
            progress(0,desc=f"📦 {n}/{tt}: {j['id']}")
            def jp(p,d=""): j["p"]=p;progress(p,desc=d)
            t0=time.time();v,s,st=pipeline(j,jp);el=ft(time.time()-t0)
            vq.done(j,v,s,el)
            if v: lv,ls=v,s
            ast.append(st);gc.collect()
        fs="\n\n---\n\n".join(ast) if ast else "📭 Empty"
    except Exception as e: fs=f"❌ {e}"
    finally: vq.busy=False;vq.cur=None
    return lv,ls,fs,vq.st(),vq.hi()

def pv(text,eng,voice,rate,pitch,ref):
    try:
        text=text or "Hello, voice preview test."
        out=tempfile.mktemp(suffix=".wav"); v=gvid(voice) if voice else "en-US-GuyNeural"
        rs=f"+{int(rate)}%" if rate>=0 else f"{int(rate)}%"
        ps=f"+{int(pitch)}Hz" if pitch>=0 else f"{int(pitch)}Hz"
        e="edge_tts"
        if "Clonar" in(eng or ""): e="clone"
        elif "gTTS" in(eng or""): e="gtts"
        return dotts(text,v,out,e,"en",rs,ps,ref)
    except: return None

def filt(s):
    if not s or not s.strip(): return gr.update(choices=CMB,value=CMB[0] if CMB else "")
    f=[v for v in CMB if s.lower() in v.lower()]
    return gr.update(choices=f or["Nothing"],value=f[0] if f else "Nothing")

def byst(st):
    if "Todos" in st: v=CMB
    else:
        v=[]
        for sn,svs in VSTYLES.items():
            if sn==st: v=[f"{vid} | {desc} | {sn}" for vid,desc in svs.items()];break
        if not v: v=CMB
    return gr.update(choices=v,value=v[0] if v else "")

# ── CSS ─────────────────────────────────────────────────────────
CSS="""
:root{--p:#6366f1;--g:linear-gradient(135deg,#6366f1,#8b5cf6,#0ea5e9);--b1:#0f172a;--b2:#1e293b;--b3:#334155;--t1:#f1f5f9;--t2:#94a3b8;--br:#475569;--r:12px}
.gradio-container{max-width:100%!important;background:linear-gradient(180deg,#0f172a,#1e293b)!important;font-family:'Inter',system-ui,sans-serif!important}
.hdr{background:var(--g)!important;padding:clamp(1rem,4vw,2rem)!important;border-radius:0 0 24px 24px!important;text-align:center!important;margin-bottom:1.5rem!important;box-shadow:0 10px 25px rgba(0,0,0,.4)!important}
.hdr h1{color:white!important;font-size:clamp(1.3rem,5vw,2.2rem)!important;font-weight:800!important;margin:0!important}
.hdr p{color:rgba(255,255,255,.9)!important;font-size:clamp(.7rem,2.5vw,1rem)!important;margin-top:.4rem!important}
.badge{display:inline-block;background:rgba(255,255,255,.2);padding:2px 10px;border-radius:20px;font-weight:600}
.panel{background:var(--b2)!important;border:1px solid var(--br)!important;border-radius:var(--r)!important;padding:clamp(.7rem,2vw,1.2rem)!important;margin:.4rem 0!important}
.panel:hover{border-color:var(--p)!important}
.tab-nav{background:var(--b2)!important;border-radius:16px!important;padding:5px!important;border:1px solid var(--br)!important;flex-wrap:wrap!important;gap:3px!important;justify-content:center!important}
.tab-nav button{background:transparent!important;border:none!important;color:var(--t2)!important;padding:9px 14px!important;border-radius:11px!important;font-weight:600!important;font-size:clamp(.7rem,2vw,.88rem)!important;flex:1 1 auto!important}
.tab-nav button.selected{background:var(--g)!important;color:white!important;box-shadow:0 4px 12px rgba(99,102,241,.4)!important}
.pb{background:var(--g)!important;color:white!important;border:none!important;border-radius:12px!important;padding:13px 24px!important;font-weight:700!important;min-height:48px!important;width:100%!important}
.qb{background:linear-gradient(135deg,#10b981,#059669)!important;color:white!important;border:none!important;border-radius:12px!important;min-height:48px!important;width:100%!important;font-weight:700!important}
.db{background:linear-gradient(135deg,#ef4444,#dc2626)!important;color:white!important;border:none!important;border-radius:10px!important}
.gradio-container input,.gradio-container textarea,.gradio-container select{background:var(--b3)!important;border:1px solid var(--br)!important;color:var(--t1)!important;border-radius:10px!important}
.gradio-container label{color:var(--t1)!important;font-weight:600!important}
.gradio-container video,.gradio-container audio{border-radius:var(--r)!important;width:100%!important}
.st{color:var(--p)!important;font-weight:700!important;border-left:3px solid var(--p);padding-left:.7rem;margin:.8rem 0 .4rem}
@media(max-width:767px){.tab-nav button{flex:1 1 calc(50% - 4px)!important}.gradio-container .gr-row{flex-direction:column!important}.gradio-container .gr-column{min-width:100%!important}input,textarea,select{font-size:16px!important}}
@media(hover:none)and(pointer:coarse){.pb,.qb,button{min-height:48px!important}input,textarea,select{min-height:44px!important}}
"""

# ── UI ──────────────────────────────────────────────────────────
with gr.Blocks(css=CSS,title="SoniTranslate Pro",theme=gr.themes.Soft(
    primary_hue=gr.themes.colors.indigo,secondary_hue=gr.themes.colors.blue,
    neutral_hue=gr.themes.colors.slate,font=[gr.themes.GoogleFont("Inter"),"system-ui","sans-serif"])) as demo:

    gr.HTML(f'<div class="hdr"><h1>🎬 SoniTranslate Pro</h1><p>Doblaje IA • <span class="badge">{TV}+ Voces</span> • Clonación • Sep. Vocal • Vel. Adaptativa</p></div>')

    with gr.Tabs():
        with gr.Tab("🎬 Traducir"):
            with gr.Row(equal_height=False):
                with gr.Column(scale=1,min_width=320):
                    gr.Markdown('<div class="st">① Video</div>')
                    with gr.Group(elem_classes="panel"):
                        vi=gr.Video(label="Video",sources=["upload"],height=200)
                        yu=gr.Textbox(label="YouTube",placeholder="https://...",info=f"Máx {MAX_DURATION//60}min")
                    gr.Markdown('<div class="st">② Idiomas</div>')
                    with gr.Group(elem_classes="panel"):
                        with gr.Row():
                            sl=gr.Dropdown(label="Origen",choices=["Auto Detect"]+LANGS,value="Auto Detect",scale=1)
                            tl=gr.Dropdown(label="Destino",choices=LANGS,value="English (en)",scale=1)
                        wm=gr.Dropdown(label="Whisper",choices=WHISPER_MODELS,value="base")
                    gr.Markdown('<div class="st">③ Audio</div>')
                    with gr.Group(elem_classes="panel"):
                        vm=gr.Radio(label="Modo",choices=[("🎼 Separar voz, mantener música","keep_bg"),("🔇 Reemplazar todo","replace_all"),("🔊 Mezclar con original","mix")],value="keep_bg")
                        bv=gr.Slider(label="Vol. fondo %",minimum=0,maximum=100,value=25,step=5)
                with gr.Column(scale=1,min_width=320):
                    gr.Markdown('<div class="st">④ Voz</div>')
                    with gr.Group(elem_classes="panel"):
                        te=gr.Dropdown(label="Motor",choices=TTS_ENGINES,value=TTS_ENGINES[0])
                        ra=gr.Audio(label="🎙️ Ref. clonar",type="filepath",visible=False)
                        ns=gr.Dropdown(label="🎭 Estilo",choices=NARR_STYLES,value="📰 Narrador / Noticias")
                        vs=gr.Textbox(label="🔍 Buscar",placeholder="Spanish Female...")
                        tv=gr.Dropdown(label="Voz",choices=SV,value=SV[0] if SV else "",filterable=True)
                    gr.Markdown('<div class="st">⑤ Velocidad</div>')
                    with gr.Group(elem_classes="panel"):
                        sm=gr.Dropdown(label="⚡ Velocidad",choices=SPEED_MODES,value="🔄 Adaptativa (sync original)")
                        cs=gr.Slider(label="Manual %",minimum=-50,maximum=50,value=0,step=5,visible=False)
                        tp=gr.Slider(label="🎵 Tono Hz",minimum=-20,maximum=20,value=0,step=1)
                    with gr.Accordion("🔊 Preview",open=False):
                        pt=gr.Textbox(label="Texto",value="Hello, voice preview test.",lines=2)
                        pb_=gr.Button("🔊 Play",size="sm")
                        pa=gr.Audio(label="Preview",type="filepath")
            tb=gr.Button("🚀 Traducir",variant="primary",elem_classes="pb")
            gr.Markdown('<div class="st">📤 Resultado</div>')
            with gr.Row(equal_height=False):
                with gr.Column(scale=1,min_width=320): ov=gr.Video(label="Doblado",height=350)
                with gr.Column(scale=1,min_width=320):
                    os2=gr.Markdown("*Sube un video...*")
                    ot=gr.Textbox(label="SRT",lines=10,interactive=False)

        with gr.Tab("📦 Cola"):
            with gr.Row(equal_height=False):
                with gr.Column(scale=1,min_width=320):
                    with gr.Group(elem_classes="panel"):
                        qv=gr.Video(label="Video",sources=["upload"],height=180)
                        qy=gr.Textbox(label="YouTube",placeholder="https://...")
                    with gr.Group(elem_classes="panel"):
                        with gr.Row():
                            qs=gr.Dropdown(label="Origen",choices=["Auto Detect"]+LANGS,value="Auto Detect",scale=1)
                            qt=gr.Dropdown(label="Destino",choices=LANGS,value="English (en)",scale=1)
                        qw=gr.Dropdown(label="Whisper",choices=WHISPER_MODELS,value="base")
                        qe=gr.Dropdown(label="Motor",choices=TTS_ENGINES,value=TTS_ENGINES[0])
                        qn=gr.Dropdown(label="Estilo",choices=NARR_STYLES,value="📰 Narrador / Noticias")
                        qq=gr.Dropdown(label="Voz",choices=SV,value=SV[0] if SV else "",filterable=True)
                        qm=gr.Dropdown(label="Velocidad",choices=SPEED_MODES,value="🔄 Adaptativa (sync original)")
                        qp=gr.Slider(label="Tono",minimum=-20,maximum=20,value=0,step=1)
                        qvm=gr.Radio(label="Audio",choices=[("🎼 Fondo","keep_bg"),("🔇 Replace","replace_all")],value="keep_bg")
                        qbv=gr.Slider(label="Vol%",minimum=0,maximum=100,value=25,step=5)
                        qra=gr.Audio(label="Ref",type="filepath",visible=False)
                    qa=gr.Button("➕ Añadir",elem_classes="qb")
                    qas=gr.Markdown("*Listo*")
                with gr.Column(scale=1,min_width=320):
                    qtb=gr.Markdown(value=vq.st(),elem_classes="panel")
                    with gr.Row():
                        qp2=gr.Button("🚀 Procesar",variant="primary",elem_classes="pb",scale=3)
                        qr=gr.Button("🔄",scale=1,size="sm")
                        qc=gr.Button("🗑️",elem_classes="db",scale=1,size="sm")
                    qh=gr.Markdown(value=vq.hi(),elem_classes="panel")
                    qov=gr.Video(label="Resultado",height=280)
                    qost=gr.Markdown()
                    qos=gr.Textbox(label="SRT",lines=8,interactive=False)

        with gr.Tab("🎙️ Voces"):
            with gr.Row(equal_height=False):
                with gr.Column(scale=1,min_width=320):
                    vest=gr.Dropdown(label="🎭 Estilo",choices=NARR_STYLES,value="📰 Narrador / Noticias")
                    vesc=gr.Textbox(label="🔍",placeholder="Spanish Male...")
                    vev=gr.Dropdown(label="Voz",choices=SV,value=SV[0] if SV else "",filterable=True)
                    vet=gr.Textbox(label="Texto",value="Welcome to SoniTranslate Pro.",lines=3)
                    with gr.Row():
                        ver=gr.Slider(label="Vel",minimum=-50,maximum=50,value=0,step=5)
                        vep=gr.Slider(label="Tono",minimum=-20,maximum=20,value=0,step=1)
                    veb=gr.Button("🔊 Play",variant="primary",elem_classes="pb")
                with gr.Column(scale=1,min_width=320):
                    vea=gr.Audio(label="Preview",type="filepath")
                    gr.Markdown(f"**{TV}+ voces** en 7 estilos narrativos")

        with gr.Tab("ℹ️ Info"):
            gr.Markdown(f"## SoniTranslate Pro\n\n{TV}+ voces | 7 estilos | Sep. vocal | Clonación | Vel. adaptativa | Cola {MAX_QUEUE} videos | CPU gratis")

    # Events
    ns.change(fn=byst,inputs=[ns],outputs=[tv])
    vest.change(fn=byst,inputs=[vest],outputs=[vev])
    qn.change(fn=byst,inputs=[qn],outputs=[qq])
    vs.change(fn=filt,inputs=[vs],outputs=[tv])
    vesc.change(fn=filt,inputs=[vesc],outputs=[vev])
    sm.change(fn=lambda m:gr.update(visible="Personal" in m),inputs=[sm],outputs=[cs])
    te.change(fn=lambda e:gr.update(visible="Clonar" in e),inputs=[te],outputs=[ra])
    qe.change(fn=lambda e:gr.update(visible="Clonar" in e),inputs=[qe],outputs=[qra])
    vm.change(fn=lambda m:gr.update(visible=m!="replace_all"),inputs=[vm],outputs=[bv])
    pb_.click(fn=pv,inputs=[pt,te,tv,cs,tp,ra],outputs=[pa])
    veb.click(fn=pv,inputs=[vet,gr.State(TTS_ENGINES[0]),vev,ver,vep,gr.State(None)],outputs=[vea])
    tb.click(fn=lambda v,y,s,t,w,e,vo,sp,c,p,m,b,r,progress=gr.Progress(track_tqdm=True):pipeline(
        {"id":str(uuid.uuid4())[:6],"vp":v,"fn":"direct","sl":s,"tl":t,"wm":w,"te":e,"tv":vo,"sm":sp,"cs":c,"tp":p,"vm":m,"bv":b,"ref":r},progress),
        inputs=[vi,yu,sl,tl,wm,te,tv,sm,cs,tp,vm,bv,ra],outputs=[ov,ot,os2])
    qa.click(fn=addq,inputs=[qv,qy,qs,qt,qw,qe,qq,qm,gr.State(0),qp,qvm,qbv,qra],outputs=[qas,qtb])
    qp2.click(fn=procq,outputs=[qov,qos,qost,qtb,qh])
    qr.click(fn=lambda:(vq.st(),vq.hi()),outputs=[qtb,qh])
    qc.click(fn=lambda:(vq.q.clear(),"🗑️",vq.st())[-2:],outputs=[qas,qtb])

if __name__=="__main__":
    demo.queue(max_size=20,default_concurrency_limit=2)
    demo.launch(server_name="0.0.0.0",server_port=7860,show_error=True)
APPEOF

echo "✅ app.py creado ($(wc -l < app.py) líneas)"
