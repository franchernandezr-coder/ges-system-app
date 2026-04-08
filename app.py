import streamlit as st
import pandas as pd
from datetime import date
import unicodedata
from io import BytesIO
from thefuzz import process, fuzz

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
st.set_page_config(
    page_title="Sistema GES Clínico | UC Christus",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)
# =====================================================
# DISEÑO INTELIGENTE ADAPTATIVO (VERSIÓN FINAL PRO)
# =====================================================
st.markdown("""
<style>
    /* 1. TARJETAS DE MÉTRICAS CON EFECTO HOVER */
    div[data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.05) !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        border-radius: 15px !important;
        padding: 20px !important;
        transition: all 0.3s ease-in-out !important;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px) !important;
        background-color: rgba(15, 58, 95, 0.1) !important;
        border-color: #0f3a5f !important;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1) !important;
    }

    /* 2. GRÁFICOS TRANSPARENTES */
    .js-plotly-plot, .plot-container {
        background-color: transparent !important;
    }

    /* 3. SIDEBAR INSTITUCIONAL UC CHRISTUS */
    [data-testid="stSidebar"] {
        background-color: #0f3a5f !important;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }

    /* 4. BOTÓN INSTITUCIONAL (CUERPO PRINCIPAL) */
    .stButton > button {
        background-color: #0f3a5f !important; /* Azul original UC */
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        display: block !important;
        margin: 20px auto !important;
        width: 320px !important;
        height: 3.2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important; /* Transición suave */
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    .stButton > button:hover {
        background-color: #28a745 !important; /* Verde éxito (Success) */
        color: white !important;
        box-shadow: 0 6px 15px rgba(40, 167, 69, 0.3) !important; /* Sombra verde sutil */
        transform: translateY(-2px) !important; /* Pequeño salto hacia arriba */
    }

    /* 5. BOTÓN DE REINICIAR (SIDEBAR) - CORRECCIÓN DE DESBORDE */
    section[data-testid="stSidebar"] .stButton {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }

    section[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;      /* Ocupa todo el ancho disponible */
        min-width: 200px !important; /* Evita que se encoja demasiado */
        margin: 0 auto !important;
        background-color: rgba(255, 75, 75, 0.15) !important;
        border: 1px solid rgba(255, 75, 75, 0.4) !important;
        height: 3rem !important;     /* Un poco más alto para que quepa el texto */
        font-size: 0.95rem !important;
        white-space: nowrap !important; /* FUERZA A QUE EL TEXTO SE QUEDE EN UNA LÍNEA */
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 10px !important;        /* Espacio entre icono y texto */
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(255, 75, 75, 0.3) !important;
        border-color: #ff4b4b !important;
    }

    /* 6. TABLAS Y DATAFRAMES */
    .stDataFrame {
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

def normalizar(texto: str) -> str:
    if not texto:
        return ""
    texto = str(texto).lower()
    
    # --- CORRECCIÓN DE TERMINOLOGÍA ESPECÍFICA ---
    correcciones = {
        "ots": "otoesclerosis",
        "iam": "infarto",
        "bipolat": "bipolar",
        "displacia": "displasia",
        "ca ": "cancer ",
        "bp de mama": "cancer mama",
        "tumorectomia": "cancer mama"
    }
    for mal, bien in correcciones.items():
        texto = texto.replace(mal, bien)

    import unicodedata
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return texto.strip()

CATALOGO_GES = [
    {"codigo": i+1, "patologia": p}
    for i, p in enumerate([
        "Enfermedad renal crónica etapa 4 y 5",
        "Cardiopatías congénitas operables",
        "Cáncer cervicouterino en personas de 15 años y más",
        "Alivio del dolor y cuidados paliativos por cáncer",
        "Infarto agudo del miocardio",
        "Diabetes mellitus tipo 1",
        "Diabetes mellitus tipo 2",
        "Cáncer de mama en personas de 15 años y más",
        "Disrafias espinales",
        "Tratamiento quirúrgico de escoliosis en personas menores de 25 años",
        "Tratamiento quirúrgico de cataratas",
        "Endoprótesis total de cadera en personas de 65 años y más",
        "Fisura labiopalatina",
        "Cáncer en personas menores de 15 años",
        "Esquizofrenia",
        "Cáncer de testículo en personas de 15 años y más",
        "Linfomas en personas de 15 años y más",
        "VIH/SIDA",
        "Infección respiratoria aguda en menores de 5 años",
        "Neumonía en mayores de 65 años",
        "Hipertensión arterial",
        "Epilepsia en menores de 15 años",
        "Salud oral 6 años",
        "Prevención parto prematuro",
        "Marcapasos",
        "Colecistectomía preventiva",
        "Cáncer gástrico",
        "Cáncer de próstata",
        "Vicios de refracción",
        "Estrabismo",
        "Retinopatía diabética",                 
        "Desprendimiento de retina",
        "Hemofilia",
        "Depresión",
        "Hiperplasia prostática",
        "Ayudas técnicas adulto mayor",
        "ACV isquémico",
        "EPOC",
        "Asma infantil",
        "Dificultad respiratoria RN",
        "Artrosis cadera/rodilla",
        "Hemorragia subaracnoidea",
        "Tumores SNC",
        "Hernia núcleo pulposo",
        "Leucemia",
        "Urgencia odontológica",
        "Salud oral 60 años",
        "Politraumatizado grave",
        "TEC moderado/grave",
        "Trauma ocular",
        "Fibrosis quística",
        "Artritis reumatoidea",
        "Consumo alcohol/drogas",
        "Analgesia parto",
        "Gran quemado",
        "Hipoacusia adulto mayor",
        "Retinopatía prematuro",
        "Displasia broncopulmonar",
        "Hipoacusia prematuro",
        "Epilepsia adulto",
        "Asma adulto",
        "Parkinson",
        "Artritis juvenil",
        "Prevención ERC terminal",
        "Displasia cadera",
        "Salud gestante",
        "Esclerosis múltiple",
        "Hepatitis B",
        "Hepatitis C",
        "Cáncer colorrectal",
        "Cáncer ovario",
        "Cáncer vesical",
        "Osteosarcoma",
        "Válvula aórtica",
        "Trastorno bipolar",
        "Hipotiroidismo",
        "Hipoacusia infantil",
        "Lupus",
        "Válvulas mitral/tricúspide",
        "Helicobacter pylori",
        "Cáncer pulmón",
        "Cáncer tiroides",
        "Cáncer renal",
        "Mieloma múltiple",
        "Alzheimer",
        "Agresión sexual",
        "Rehabilitación COVID",
        "Cirrosis hepática",
        "Depresión grave hospitalaria",
        "Cesación tabaco"
    ])
]

df_catalogo_ges = pd.DataFrame(CATALOGO_GES)

# --- TRADUCTOR DE CÓDIGOS A NOMBRES OFICIALES ---
MAPEO_POR_ID = {
    1: "Enfermedad renal crónica etapa 4 y 5",
    3: "Cáncer cervicouterino en personas de 15 años y más",
    4: "Alivio del dolor y cuidados paliativos por cáncer",
    5: "Infarto agudo del miocardio",
    8: "Cáncer de mama en personas de 15 años y más",
    13: "Fisura labiopalatina",
    27: "Cáncer gástrico",
    31: "Retinopatía diabética",
    34: "Depresión",
    36: "Ayudas técnicas adulto mayor",
    41: "Artrosis cadera/rodilla",
    42: "Hemorragia subaracnoidea",
    46: "Urgencia odontológica",
    49: "TEC moderado/grave",
    52: "Artritis reumatoidea",
    60: "Epilepsia adulto",
    65: "Displasia cadera",
    67: "Esclerosis múltiple",
    70: "Cáncer colorrectal",
    75: "Trastorno bipolar",
    79: "Válvulas mitral/tricúspide",
    81: "Cáncer pulmón"
}

SINONIMOS_GES = {
    1: ["enfermedad renal cronica", "erc etapa 4", "erc etapa 5", "dialisis", "hemodialisis"],
    2: ["cardiopatia cogenita operables", "cardiopatia cogenita", "tetralogia de fallot", "comunicacion interventricular"],
    3: ["cancer cervicouterino en personas de 15 años y mas", "cancer cervicouturino", "cancer de cervix", "neoplasia cervical", "neoplasia" ],
    4: ["alivio del dolor y cuidados paliativos por cancer","cuidados paliativos", "manejo paliativo oncologico", "dolor oncologico", "oncologico cancer"],
    5: ["infarto", "iam", "stemi", "nstemi", "sindrome coronario", "scasest"],
    6: ["diabetes melitus tipo 1", "diabetes melitus tipo 1 insulinodepentiente", "insulinodependiente 1 ", "insulinodepentiende", "dm1"],
    7: ["diabetes melitus tipo 2", "dm2", "hiperglicemia", "diabetico"],
    8: ["cancer de mama en personas de 15 años y mas", "cancer de mama", "neoplasia maligna de mama ", "ca de mama", "nodulo mamario", "neoplasia mama"],
    9: ["disrafias espinales", "disrafia espinal", "espina bifida ", "mielomeningocele", "espinal", "meningocele","siringomielia", "medula anclada", "defectos tubo neural"],
    10: ["Tratamiento quirurgico de escoliosis en personas menores de 25 años", "escoliosis severa", "cirugia de escoliosis ", "escoliosis", "desviacion columna", "curvatura columna"],
    11: ["Tratamiento quirurgico de cataratas", "cataratas senil", "cirugia de catarata", "opacidad cristalino"],
    12: ["Endoprótesis total de cadera en personas de 65 años y más con artrosis de cadera con limitación funcional severa", "endoprotesis total cadera", "protesis total de cadera", "fractura de cuello de femoral","artrosis cadera", "cadera""endoprotesis total de cadera", "ptc", "protesis cadera"],
    13: ["fisura labiopalatina", "labio leporino", "fisura palatina", "fisura labial", "paladar hendido"],
    14: ["cancer en menores de 15 años", "ca infantil", "tumor infantil", "oncologia pediatrica", "leucemia pediatrica"],
    15: ["esquizofrenia", "trastorno esquizofrenico", "episodio psicotico", "esquizofreniforme", "psicosis"],
    16: ["cancer de testiculo en personas de 15 años y mas","cancer de testiculo", "ca de testiculo", "tumor testicular", "seminoma", "orquiectomia"],
    17: ["linfomas en personas de 15 años y mas","linfomas", "linfoma de hodgkin", "linfoma no hodgkin", "adenopatias neoplasicas"],
    18: ["sindrome de la inmunodeficencia adquirida vhi sida","vih", "sida", "vhs", "inmunodeficiencia adquirida", "tarp", "paciente vih positivo"],
    19: ["infeccion respiratoria aguda (ira) de manejo ambulatorio en personas de 65 años y mas","infeccion respiratoria aguda", "ira", "bronquiolitis", "obstruccion bronquial aguda", "vrs"],
    20: ["neumenoia adquirida en la comunidad de manejo ambulatorio en personas de 65 años y mas","neumonia", "neunomio", "nace", "pulmonia", "foco pulmonar", "neumonitis", "consolidacion","neumonia adquirida en la comunidad"],
    21: ["hipertension arterial primaria o esencial en personas de 15 años y mas","hta", "hipertension", "presion alta","hipertension arterial","hipertension primaria"],
    22: ["epilepsia en personas desde 1 año y menores de 15 años","epilepsia en menores de 15 años", "convulsiones pediatrica", "crisis convulsiva", "status epileptico", "epilepsia infantil"],
    23: ["salud oral integral para niños y niñas de 6 años","salud oral 6 años", "dental 6 años", "caries dental infantil", "odontopediatria"],
    24: ["prevencion parto prematuro", "spp", "app", "amenaza parto prematuro", "sintoma parto prematuro", "cuello corto"],
    25: ["trastornos de generacion del impulso y conduccion en personas de 15 años y mas requieren marcapasos","marcapaso", "marcapasos", "generador", "cambio generador", "bradicardia"],
    26: ["colecistectomia preventiva del cancer de vesicula en personas de 35 a 49 años","colecistitis", "colelap", "vesicula", "biliar", "colecistectomia"],
    27: ["cancer gastrico","ca gastrico", "cancer gastrico", "gastrico", "adenocarcinoma","neoplasia maligna gastrica"],
    28: ["cancer de prostata en personas de 15 años y mas","cancer de prostata", "ca de prostata", "tumor prostatico", "adenocarcinoma de prostata", "prostatectomia","neoplasia prostatica"],
    29: ["Vicios de refracción en personas de 65 años y mas","vicios de refraccion", "astigmatismo", "miopia", "hipermetropia", "presbicia", "vicio refraccion"],
    30: ["estrabismo en personas menores de 9 años","estrabismo", "ojo desviado", "correccion estrabismo"],
    31: ["retinopatia diabetica","retinopatia", "fondo de ojo", "diabetica","retinopatia dm"],
    32: ["desprendimiento de retina regmatogeno no traumatico","desprendimiento de retina", "dr", "desgarro retinal", "vitrectomia"],
    33: ["hemofilia", "deficiencia factor viii", "deficiencia factor ix", "trastorno coagulacion"],
    34: ["depresion en personas de 15 años y mas","depresion", "depre", "trastorno depresivo","episodio depresivo"],
    35: ["tratamiento de la hiperplasia benigna de la prostata en personas sintomaticas","hiperplasia prostatica", "hbp", "crecimiento prostatico", "uropatia obstructiva baja", "prostatismo"],
    36: ["ayudas tecnicas para personas de 65 años y mas","ayudas tecnicas", "bastones", "silla de ruedas", "ortesis","andador"],
    37: ["ataque cerebrovascular isquemico en personas de 15 años y más","acv", "ictus", "stroke", "isquemico","ictis isquemico"],
    38: ["enfermedad pulmonar obstructiva cronica de tratamiento ambulatorio","epoc", "limitacion cronica flujo aereo", "enfisema", "bronquitis cronica","exacerbacion de epoc", "enfermedad pulmonar obstructiva"],
    39: ["asma bronquial moderada y grave en personas menores de 15 años","asma", "asma adulto", "crisis asmatica", "obstruccion bronquial"],
    40: ["sindrome de dificultad respiratoria en el recien nacido","dificultad respiratoria", "sdr", "membrana hilina", "obstruccion respiratoria nacido"],
    41: ["tratamiento médico en personas de 55 años y más con artrosis de cadera y/o rodilla, leve o moderada","artrosis", "artrosis rodilla", "artrosis cadera"],
    42: ["hemorragia subaracnoidea secundaria a ruptura de uno o más aneurismas cerebrales","hsa", "hemorragia subaracnoidea", "aneurisma","aneurisma cerebral"],
    43: ["tumores primarios del sistema nervioso central en personas de 15 años y mas","hsa", "tumor cerebral", "tumor snc","neoplasia cerebral"],
    44: ["tratamiento quirurgico de hernia del nucleo pulposo lumbar", "hernia discal", "lumbar","hernia","hernia nucleo pulposo"],
    45: ["leucemia en personas de 15 años y mas","leucemia", "lma", "lpa", "leucemia linfoide","leucemia aguda","leucemia miloide","leucemia linfoblastica"],
    46: ["urgencia odontologica", "dental", "dolor muela", "absceso dental", "odonto", "amigdalectomia"],
    47: ["salud oral integral de personas de 60 años", "salud oral 60", "dolor muela 60 años", "absceso dental 60", "odonto dolor"],
    48: ["politraumatizado grave", "politraumatizado grave", "trauma multisistemico",],
    49: ["traumatismo cráneo encefálico moderado o grave","tec", "tce", "traumatismo craneoencefalico grave"],
    50: ["trauma ocular", "golpe ojo", "herida ocular"],
    51: ["fibrosis quistica", "fq", "mucoviscidosis", "test del sudor", "fibrosis quistica pancreas"],
    52: ["artritis reumatoide", "ar", "artritis reumatoidea", "poliartritis cronica", "factor reumatoide"],
    53: ["Consumo perjudicial o dependencia de riesgo bajo a moderado de alcohol y drogas en personas menores de 20 años","consumo alcohol drogas", "dependencia alcohol", "abuso sustancias", "drogadiccion", "menores de 20 años"],
    54: ["analgesia del parto", "analgesia parto", "anestesia parto", "peridural parto", "alivio dolor parto","bloque peridural"],
    55: ["gran quemado", "quemadura grave", "quemado critico", "quemadura tipo b", "quemadura tipo c"],
    56: ["Hipoacusia bilateral en personas de 65 años y mas que requieren uso de audífono","hipoacusia adulto mayor", "sordera 65 años", "audifonos mayor", "presbiacusia", "hipoacusia bilateral"],
    57: ["retinopatia del prematuro", "rop", "retinopatia prematuro", "desprendimiento retina prematuro"],
    58: ["displasia broncopulmonar", "dbp", "displasia broncopulmonar prematuro", "enfermedad pulmonar cronica"],
    59: ["hipoacusia neurosensorial bilateral del prematuro","hipoacusia prematuro", "sordera prematuro", "hipoacusia neurosensorial", "hipoacusia neurosensorial bilateral"],
    60: ["epilepsia en personas de 15 años y mas","epilepsia adulto", "crisis convulsiva adulto", "status epileptico", "epilepsia no refractaria"],
    61: ["asma bronquial en personas de 15 año y mas","asma adulto", "crisis asmatica adulto", "obstruccion bronquial", "asma bronquial moderada"],
    62: ["parkinson", "mal de parkinson", "enfermedad de parkinson", "temblor esencial"],
    63: ["enfermedad de parkinson","artritis juvenil", "artritis idiopatica juvenil", "aij", "artritis cronica juvenil"],
    64: ["prevención secundaria enfermedad renal crónica terminal","prevencion erc terminal", "pre-dialisis", "nefropatia cronica", "prevencion enfermedad renal"],
    65: ["displasia luxante de caderas","displasia cadera", "displacia", "luxacion cadera", "subluxacion cadera", "displacia de cadera"],
    66: ["salud oral integral de la persona gestante","emb", "embarazo", "cesarea", "induccion", "parto"],
    67: ["esclerosis múltiple remitente recurrente","esclerosis multiple", "em", "esclerosis multiple remitente", "esclerosis"],
    68: ["hepatitis cronica por virus hepatitis b","hepatitis b", "vhb", "hepatitis viral b", "antigeno superficie"],
    69: ["hepatitis cronica por virus hepatitis c","hepatitis c", "vhc", "hepatitis viral c", "antivirus c"],
    70: ["Cancer colorrectal en personas de 15 años y mas","cancer colorrectal", "ca de colon", "ca de recto", "adenocarcinoma colon", "colon", "recto"],
    71: ["cancer de ovario epitelial","cancer de ovario", "ca ovario", "tumor ovarico", "neoplasia ovario", "ovario"],
    72: ["Cancer vesical en personas de 15 años y más","cancer de vejiga", "ca vejiga", "tumor vesical", "carcinoma urotelial", "vejiga"],
    73: ["Osteosarcoma en personas de 15 años y mas","osteosarcoma", "tumor oseo", "sarcoma de ewing", "neoplasia osea"],
    74: ["tratamiento quirúrgico de lesiones cronicas de la válvula aortica en personas de 15 años y mas","valvula aortica", "estenosis aortica", "recambio valvular", "aortica", "estenosis aortica severa"],
    75: ["trastorno bipolar en personas de 15 años y mas","trastorno bipolar", "bipolat", "tab", "ciclotimia", "bipolaridad", "episodio maniaco"],
    76: ["hipotiroidismo en personas de 15 años y más","hipotiroidismo", "hipotiroisidmo", "levotiroxina", "tsh alta", "hipotiroidismo primario"],
    77: ["hipoacusia moderada, severa y profunda en personas menores de 4 años","hipoacusia infantil", "hipoacusia neurosensorial infantil", "sordera niños", "implante coclear"],
    78: ["Lupus eritematoso sistemico","lupus", "les", "lupus eritematoso sistemico", "lupus eritematoso"],
    79: ["Tratamiento quirúrgico de lesiones cronicas de las válvulas mitral y tricúspide en personas de 15 años y más","valvulas mitral tricuspide", "protesis mitral", "insuficiencia mitral", "valvula tricuspide", "estenosis mitral"],
    80: ["Tratamiento de erradicación de Helicobacter pylori","helicobacter pylori", "h pylori", "erradicacion helicobacter", "pylori"],
    81: ["Cancer de pulmón en personas de 15 años y mas","cancer pulmon", "ca de pulmon", "ca pulmonar", "tumor pulmon", "pulmon", "nodulo pulmonar"],
    82: ["Cancer de tiroides en personas de 15 años y más","cancer tiroides", "ca tiroides", "nodulo tiroideo", "tiroidectomia", "tiroides"],
    83: ["Cancer renal en personas de 15 años y más","cancer renal", "ca renal", "tumor renal", "adenocarcinoma renal", "nefrectomia", "renal"],
    84: ["Mieloma múltiple en personas de 15 años y mas","mieloma multiple", "mieloma", "kahler", "enfermedad de kahler", "plasmocitoma"],
    85: ["Enfermedad de Alzheimer y otras demencias","alzheimer", "demencia senil", "deterioro cognitivo", "demencia", "enfermedad de alzheimer"],
    86: ["Atención integral de salud en agresión sexual aguda","agresion sexual", "abuso sexual", "violacion", "atencion sause"],
    87: ["Rehabilitación SARS-CoV-2","rehabilitacion covid", "post covid", "secuela covid", "covid", "sars cov 2"],
    88: ["Tratamiento farmacologico tras alta hospitalaria por cirrosis hepatica","cirrosis hepatica", "cirrosis", "falla hepatica cronica", "dhc", "daño hepatico cronico"],
    89: ["Tratamiento hospitalario para personas menores de 15 años con depresión grave refractaria o psicótica con riesgo suicida","depresion grave", "episodio depresivo grave", "hospitalizacion psiquiatrica", "depresion hospitalaria"],
    90: ["Cesación del consumo de tabaco en personas de 25 años y más","cesacion tabaco", "tabaquismo", "dejar de fumar", "dependencia nicotina","fumador","cesacion tabaquica"]
}

df_catalogo_ges = pd.DataFrame(CATALOGO_GES)

# =====================================================
# BUSCADOR INTELIGENTE
# =====================================================
def buscar_ges(input_usuario):
    if not input_usuario:
        return []

    texto = normalizar(input_usuario)
    
    if texto.isdigit():
        cod_num = int(texto)
        match_directo = df_catalogo_ges[df_catalogo_ges["codigo"] == cod_num]
        if not match_directo.empty:
            return [match_directo.iloc[0]]

    resultados = []
    for _, row in df_catalogo_ges.iterrows():
        codigo = row["codigo"]
        patologia = normalizar(row["patologia"])
    return resultados
def sugerir_patologias(diagnostico_usuario: str):
    texto = normalizar(diagnostico_usuario)
    if not texto: return []
    
    # Capa Pro: Mapeo Directo
    MAPEO_CLINICO = {
        "otoesclerosis": 79, "fimosis": 13, "mama": 8, "cervicouterino": 3,
        "gastrico": 27, "pulmon": 81, "bipolar": 75, "displasia": 65,
        "infarto": 5, "paliativos": 4, "renal": 1, "tec": 49,
        "amigdalectomia": 46, "depresion": 34, "epilepsia": 60,
        "subaracnoidea": 42, "cadera": 41, "ayudas tecnicas": 36
    }
    for k, v in MAPEO_CLINICO.items():
        if k in texto:
            match = df_catalogo_ges[df_catalogo_ges["codigo"] == v]
            if not match.empty:
                return [{"patologia": match["patologia"].iloc[0], "prioridad": 1, "match": "Mapeo Clínico"}]

    # Capa Fuzzy
    resultados = []
    for regla in REGLAS_GES:
        mejor_kw, score = process.extractOne(texto, regla["keywords"], scorer=fuzz.partial_ratio)
        if score >= 75:
            resultados.append({"patologia": regla["patologia"], "prioridad": regla.get("prioridad", 99), "match": f"Fuzzy ({score}%)"})
    return sorted(resultados, key=lambda x: x["prioridad"])

# =====================================================
# REGLAS CLÍNICAS CON PRIORIDAD
# =====================================================
REGLAS_GES = [
    {"patologia": "Accidente cerebrovascular isquémico", "keywords": ["acv", "ictus", "stroke", "isquemico", "infarto cerebral"], "prioridad": 1},
    {"patologia": "Infarto agudo del miocardio", "keywords": ["iam", "infarto", "stemi", "nstemi", "coronariografia", "scasest"], "prioridad": 2},
    {"patologia": "Hemorragia subaracnoidea", "keywords": ["hsa", "hemorragia subaracnoidea", "aneurisma cerebral"], "prioridad": 3},
    {"patologia": "Traumatismo cráneo encefálico moderado o grave", "keywords": ["tec", "tce", "traumatismo craneoencefalico", "contusion cerebral"], "prioridad": 4},
    {"patologia": "Politraumatizado grave", "keywords": ["politraumatizado", "trauma multisistemico", "gran trauma"], "prioridad": 5},
    {"patologia": "Cáncer gástrico", "keywords": ["cancer gastrico", "ca gastrico", "gastrico", "adenocarcinoma gastrico"], "prioridad": 6},
    {"patologia": "Marcapasos", "keywords": ["marcapazo", "marcapasos", "generador", "cambio generador", "bradicardia"], "prioridad": 7},
    {"patologia": "Colecistectomía preventiva (Vesícula)", "keywords": ["colelap", "colecistitis", "vesicula", "biliar", "colecistectomia"], "prioridad": 8},
    {"patologia": "Cáncer de mama", "keywords": ["ca de mama", "ca mama", "cancer de mama", "neoplasia mama", "tumor mama"], "prioridad": 9},
    {"patologia": "Cáncer cervicouterino", "keywords": ["ca cervicouterino", "cancer cervico", "cacue", "neoplasia cervical"], "prioridad": 10},
    {"patologia": "Cáncer de próstata", "keywords": ["ca de prostata", "cancer prostata", "prostatectomia", "neoplasia prostatica"], "prioridad": 11},
    {"patologia": "Cáncer colorrectal", "keywords": ["ca de colon", "ca colorrectal", "adenocarcinoma colon", "colon", "recto"], "prioridad": 12},
    {"patologia": "Salud gestante (Parto/Cesárea)", "keywords": ["emb", "embarazo", "cesarea", "induccion", "parto", "puerperio", "gestante"], "prioridad": 16},
    {"patologia": "Prevención parto prematuro", "keywords": ["spp", "app", "amenaza parto", "parto prematuro", "cuello corto"], "prioridad": 17},
    {"patologia": "Displasia de cadera", "keywords": ["displasia", "displacia", "luxacion cadera", "subluxacion cadera", "cadera"], "prioridad": 18},
    {"patologia": "Dificultad respiratoria RN", "keywords": ["sdr", "membrana hialina", "dificultad respiratoria nacido"], "prioridad": 19},
    {"patologia": "Diabetes mellitus tipo 2", "keywords": ["dm2", "diabetes", "diabetico", "hiperglicemia"], "prioridad": 26},
    {"patologia": "Hipertensión arterial", "keywords": ["hta", "hipertension", "presion alta"], "prioridad": 27},
    {"patologia": "Trastorno bipolar", "keywords": ["bipolar", "bipolat", "tab", "episodio maniaco"], "prioridad": 28},
    {"patologia": "Depresión", "keywords": ["depresion", "depre", "episodio depresivo"], "prioridad": 29},
    {"patologia": "Hipotiroidismo", "keywords": ["hipotiroidismo", "hipotiroisidmo", "levotiroxina", "tsh alta"], "prioridad": 30},
    {"patologia": "Artritis Reumatoide / Juvenil", "keywords": ["artritis", "ar", "aij", "reumatoide"], "prioridad": 31},
    {"patologia": "Endoprótesis total de cadera", "keywords": ["ptc", "protesis cadera", "fractura cadera", "artrosis cadera"], "prioridad": 32},
    {"patologia": "Urgencia Odontológica", "keywords": ["dental", "odonto", "caries", "dolor muela", "amigdalectomia"], "prioridad": 41},
    {"patologia": "Neumonía / EPOC", "keywords": ["neumonia", "nace", "pulmonia", "epoc", "enfisema"], "prioridad": 42},
    {"patologia": "Mieloma múltiple / Linfoma", "keywords": ["mieloma", "linfoma", "kahler", "hodgkin"], "prioridad": 43},
    {"patologia": "Ayudas técnicas", "keywords": ["ayudas tecnicas", "bastones", "silla de ruedas", "ortesis"], "prioridad": 44},
    {"patologia": "Hernia Nucleo Pulposo", "keywords": ["hnp", "hernia discal", "hernia lumbar", "nucleo pulposo"], "prioridad": 45}
]

SEMÁFORO_GES = {
    "Accidente cerebrovascular isquémico": "🔴 Alta",
    "Infarto agudo del miocardio": "🔴 Alta",
    "Traumatismo cráneo encefálico moderado o grave": "🟡 Media",
    "Diabetes mellitus tipo 2": "🟢 Baja",
    "Hipertensión arterial": "🟢 Baja",
    "Cáncer gástrico": "🟡 Media",
}

def sugerir_patologias(diagnostico_usuario: str):
    texto = normalizar(diagnostico_usuario)
    if not texto:
        return []
    
    palabras_negativas = ["no ", "descarta", " descartar", " descartado", "sin evidencia", "estudio de", "negativo"]
    if any(neg in texto for neg in palabras_negativas):
        return [] 

    resultados = []
    
    if texto.isdigit():
        cod_buscado = int(texto)
        match_cod = df_catalogo_ges[df_catalogo_ges["codigo"] == cod_buscado]
        if not match_cod.empty:
            return [{"patologia": match_cod["patologia"].iloc[0], "prioridad": 0, "match": "Código Exacto"}]

    for cod_ges, lista_s in SINONIMOS_GES.items():
        if any(normalizar(s) in texto for s in lista_s):
            pat = df_catalogo_ges[df_catalogo_ges["codigo"] == cod_ges]["patologia"].iloc[0]
            resultados.append({"patologia": pat, "prioridad": 1, "match": "Sinónimo"})

    for regla in REGLAS_GES:
        match_rapido = any(normalizar(kw) in texto for kw in regla["keywords"])
        
        if match_rapido:
            resultados.append({
                "patologia": regla["patologia"], 
                "prioridad": regla.get("prioridad", 99), 
                "match": "Exacto"
            })
            continue

        mejor_kw, score = process.extractOne(texto, regla["keywords"], scorer=fuzz.partial_ratio)

        if score >= 70:
            resultados.append({
                "patologia": regla["patologia"],
                "prioridad": regla.get("prioridad", 99),
                "match": f"Aprox ({score}%)"
            })

    return sorted(resultados, key=lambda x: x["prioridad"])

# =====================================================
# SESSION STATE
# =====================================================
COLUMNAS_BASE = [
    "RUT", "Nombre", "Fecha admisión", "Diagnóstico clínico",
    "Código GES", "Patología GES", "Semáforo GES", "Clasificación",
    "Estado de Notificación", 
]

if "admisiones" not in st.session_state:
    st.session_state.admisiones = pd.DataFrame(columns=COLUMNAS_BASE)

if "ingresos_manuales" not in st.session_state:
    st.session_state.ingresos_manuales = pd.DataFrame(columns=COLUMNAS_BASE)

# =====================================================
# HEADER
# =====================================================
st.title("🩺 Sistema GES Clínico")
st.caption("Unidad de Gestión GES – Clínica UC Christus")
st.divider()

# =====================================================
# MENÚ
# =====================================================
menu = st.sidebar.radio(
    "Menú",
    ["📊 Dashboard", "📥 Carga Excel", "✍️ Ingreso Manual", "📄 Tabla Operativa", "📤 Exportar"]
)

st.sidebar.divider()
if st.sidebar.button("🗑️ Reiniciar Datos"):
    st.session_state.admisiones = pd.DataFrame(columns=COLUMNAS_BASE)
    st.session_state.ingresos_manuales = pd.DataFrame(columns=COLUMNAS_BASE)
    st.success("Datos limpiados")
    st.rerun()

# =====================================================
# DASHBOARD - CÁLCULO INTELIGENTE (META 80%+)
# =====================================================
if menu == "📊 Dashboard":
    import plotly.express as px
    st.subheader("📊 Panel de Control y Cumplimiento GES")
    
    tablas = []
    if not st.session_state.admisiones.empty: 
        tablas.append(st.session_state.admisiones)
    if not st.session_state.ingresos_manuales.empty: 
        tablas.append(st.session_state.ingresos_manuales)

    if tablas:
        df_dash_raw = pd.concat(tablas, ignore_index=True)
        
        # --- FILTRO DE CENTROS ---
        col_centro = next((c for c in df_dash_raw.columns if "atencion" in normalizar(str(c)) or "centro" in normalizar(str(c))), None)
        if col_centro:
            with st.expander("🔍 Filtros Avanzados de Dashboard"):
                opciones_centro = df_dash_raw[col_centro].unique().tolist()
                centros_sel = st.multiselect("Filtrar Dashboard por Centro:", opciones_centro, default=opciones_centro)
                df_dash = df_dash_raw[df_dash_raw[col_centro].isin(centros_sel)].copy()
        else:
            df_dash = df_dash_raw.copy()

        # --- LÓGICA DE CÁLCULO INTELIGENTE ---
        total_pacientes = len(df_dash)
        df_ges = df_dash[df_dash["Patología GES"] != "NO GES"].copy()
        
        # Función mejorada: Notificado (True), Pendiente (False), No Aplica (EXCLUIR)
        def es_notificado_inteligente(row):
            estado = normalizar(str(row["Estado de Notificación"]))
            if "notificado" in estado and "sin" not in estado:
                return "SI"
            if "no aplica" in estado:
                return "EXCLUIR"
            return "NO"

        # Aplicamos la lógica al universo GES
        df_ges["Resultado_Notif"] = df_ges.apply(es_notificado_inteligente, axis=1)
        
        # Universo real para el cálculo (excluyendo "No Aplica")
        df_universo_cumplimiento = df_ges[df_ges["Resultado_Notif"] != "EXCLUIR"]
        
        n_ges_notificados = (df_ges["Resultado_Notif"] == "SI").sum()
        total_a_notificar = len(df_universo_cumplimiento)
        n_ges_no_notificados = total_a_notificar - n_ges_notificados
        
        # Cálculo de cumplimiento final
        cumplimiento = (n_ges_notificados / total_a_notificar * 100) if total_a_notificar > 0 else 0

        # --- TARJETAS DE MÉTRICAS ---
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Pacientes", total_pacientes)
        col2.metric("Total Casos GES", total_a_notificar, help="Excluye casos 'No Aplica'")
        col3.metric("Notificados", n_ges_notificados)
        col4.metric("Pendientes", n_ges_no_notificados)
        
        meta = 80.0
        diff = cumplimiento - meta
        color_delta = "normal" if cumplimiento >= meta else "inverse"
        col5.metric("Cumplimiento", f"{cumplimiento:.1f}%", delta=f"{diff:.1f}% vs Meta", delta_color=color_delta)

        st.divider()
        col_izq, col_der = st.columns([1, 1])

        with col_izq:
            st.markdown("### 🥧 Distribución de Notificación")
            if total_a_notificar > 0:
                fig_data = pd.DataFrame({
                    "Estado": ["Notificados", "No Notificados"], 
                    "Cantidad": [n_ges_notificados, n_ges_no_notificados]
                })
                fig = px.pie(fig_data, values='Cantidad', names='Estado', hole=0.4, 
                             color='Estado', color_discrete_map={'Notificados':'#28a745', 'No Notificados':'#dc3545'})
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                  margin=dict(t=10, b=10, l=10, r=10), height=350, 
                                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig, width='stretch') 
            else:
                st.info("Sin casos GES que requieran notificación.")

        with col_der:
            st.markdown("### 👨‍⚕️ Médicos con Pendientes")
            # Solo mostramos como pendientes los que NO son notificados y NO son "excluidos"
            pendientes = df_universo_cumplimiento[df_universo_cumplimiento["Resultado_Notif"] == "NO"]
            
            if not pendientes.empty:
                conteo_medicos = pendientes.groupby("Medico Notificador").size().reset_index(name="Casos")
                st.dataframe(conteo_medicos.sort_values(by="Casos", ascending=False), width='stretch')
                if st.checkbox("Ver detalle de diagnósticos pendientes"):
                    st.table(pendientes[["Medico Notificador", "Diagnostico clinico", "RUT"]].head(10))
            else:
                st.success("🎉 ¡Meta cumplida! No hay notificaciones pendientes.")

        st.divider()
        with st.expander("🔍 Ver Base de Datos Consolidada"):
            st.dataframe(df_dash.astype(str), width='stretch')
    else:
        st.warning("⚠️ El sistema no tiene datos.")
# =====================================================

# =====================================================
# CARGA EXCEL - VERSIÓN MOTOR HÍBRIDO (PRO)
# =====================================================
elif menu == "📥 Carga Excel":
    st.subheader("📥 Carga de archivo Excel GES")
    archivo = st.file_uploader("Seleccione archivo Excel", type=["xlsx"])

    if archivo:
        try:
            df_raw = pd.read_excel(archivo, sheet_name="Hoja1")
            
            # 1. Mapeo y Limpieza Dinámica
            mapeo = {}
            col_centro = None
            for col in df_raw.columns:
                c_norm = normalizar(str(col))
                if "rut" in c_norm: mapeo[col] = "RUT"
                elif "nombre" in c_norm: mapeo[col] = "Nombre"
                elif "atencion" in c_norm or "centro" in c_norm: col_centro = col
                elif "fecha" in c_norm or "admision" in c_norm: mapeo[col] = "Fecha admision"
                elif any(x in c_norm for x in ["diagnostico", "dx"]): mapeo[col] = "Diagnostico clinico"
                elif "medico" in c_norm: mapeo[col] = "Medico Notificador"
                elif "estado" in c_norm: mapeo[col] = "Estado de Notificación"
            
            df_raw = df_raw.rename(columns=mapeo)
            df_raw = df_raw.dropna(subset=["RUT"])

            # 2. Filtro Multiselección
            if col_centro:
                st.markdown(f"### 🔍 Filtro por {col_centro}")
                opciones = df_raw[col_centro].unique().tolist()
                default_val = ["CACSCA"] if "CACSCA" in opciones else opciones
                seleccion = st.multiselect("Seleccione Centros:", opciones, default=default_val)
                df_procesar = df_raw[df_raw[col_centro].isin(seleccion)].copy()
            else:
                df_procesar = df_raw.copy()

            st.dataframe(df_procesar, width='stretch', height=300)

            # 3. Botón de Incorporación con MOTOR HÍBRIDO
            if st.button("🚀 Finalizar e Incorporar al Sistema"):
                with st.spinner("🩺 Ejecutando Motor Híbrido (Números + Palabras)..."):
                    df_final = df_procesar.copy()
                    
                    # Preparar columnas de salida
                    df_final["Patología GES"] = "PENDIENTE"
                    df_final["Código GES"] = "—"
                    df_final["Semáforo GES"] = "⚪ N/A"
                    df_final["Clasificación"] = "SISTEMA"
                    
                    if "Medico Notificador" not in df_final.columns: df_final["Medico Notificador"] = "Sin Dato"
                    if "Estado de Notificación" not in df_final.columns: df_final["Estado de Notificación"] = "Sin Dato"

                    # --- INICIO DEL MOTOR HÍBRIDO ---
                    for idx, row in df_final.iterrows():
                        diagnostico_texto = str(row["Diagnostico clinico"])
                        id_excel = row.get("N GES") # Extraemos el número del Excel

                        pat_detectada = None
                        cod_final = "—"

                        # PASO A: PRIORIDAD AL NÚMERO (Si el administrativo ya puso 1, 5, 49, etc.)
                        try:
                            if pd.notna(id_excel) and int(float(id_excel)) > 0:
                                id_num = int(float(id_excel))
                                if id_num in MAPEO_POR_ID:
                                    pat_detectada = MAPEO_POR_ID[id_num]
                                    cod_final = str(id_num)
                        except:
                            pass

                        # PASO B: SI NO HAY NÚMERO (O ES 0), USAR BUSCADOR INTELIGENTE POR TEXTO
                        if not pat_detectada:
                            sug = sugerir_patologias(diagnostico_texto)
                            if sug:
                                pat_detectada = sug[0]["patologia"]
                                # Buscamos el código en el catálogo oficial para completar la celda
                                match_cat = df_catalogo_ges[df_catalogo_ges["patologia"].str.lower() == pat_detectada.lower()]
                                if not match_cat.empty:
                                    cod_final = str(match_cat["codigo"].iloc[0])

                        # ASIGNACIÓN FINAL DE RESULTADOS
                        if pat_detectada:
                            df_final.at[idx, "Patología GES"] = pat_detectada
                            df_final.at[idx, "Código GES"] = cod_final
                            df_final.at[idx, "Semáforo GES"] = SEMÁFORO_GES.get(pat_detectada, "🟡 Media")
                            df_final.at[idx, "Clasificación"] = "DETECCIÓN HÍBRIDA"
                        else:
                            df_final.at[idx, "Patología GES"] = "NO GES"
                            df_final.at[idx, "Código GES"] = "—"
                            df_final.at[idx, "Semáforo GES"] = "⚪ N/A"

                    # GUARDAR EN SESSION STATE PARA EL DASHBOARD
                    st.session_state.admisiones = df_final
                    st.success(f"✅ Se han procesado {len(df_final)} registros. ¡Cumplimiento actualizado!")
                    st.balloons()
                    
        except Exception as e:
            st.error(f"❌ Error crítico en el motor: {e}")

elif menu == "✍️ Ingreso Manual":
    st.subheader("✍️ Ingreso Manual de Paciente GES")
    col1, col2 = st.columns(2)
    with col1:
        busqueda_ges = st.text_input("🔎 Buscar Patología o Código GES", placeholder="Ej: 5, infarto...")
    resultados_busqueda = buscar_ges(busqueda_ges) if busqueda_ges else []
    patologia = None
    codigo = None
    clasificacion = "MANUAL"
    with col2:
        if resultados_busqueda:
            df_resultados = pd.DataFrame(resultados_busqueda)
            opciones = [f"{row['codigo']} - {row['patologia']}" for _, row in df_resultados.iterrows()]
            seleccion = st.selectbox("Resultado búsqueda GES", opciones)
            codigo = int(seleccion.split(" - ")[0])
            patologia = seleccion.split(" - ")[1]
            st.success(f"✔ Seleccionado: {patologia}")
    st.divider()
    diagnostico = st.text_input("Diagnóstico clínico", placeholder="Ej: IAM, ACV...")
    if not patologia and diagnostico:
        sugerencias = sugerir_patologias(diagnostico)
        if len(sugerencias) == 1:
            patologia = sugerencias[0]["patologia"]
            clasificacion = "AUTOMÁTICA"
            st.success(f"✔ Detectado: {patologia}")
        elif len(sugerencias) > 1:
            opciones = [s["patologia"] for s in sugerencias]
            patologia = st.selectbox("Patología sugerida", opciones)
    if not patologia:
        patologia = st.selectbox("Seleccionar manualmente", df_catalogo_ges["patologia"])
    if codigo is None and patologia:
        match = df_catalogo_ges[df_catalogo_ges["patologia"] == patologia]
        if not match.empty:
            codigo = match["codigo"].iloc[0]
    st.caption(f"Código GES: {codigo if codigo else '—'}")
    st.divider()
    with st.form("form_manual"):
        rut = st.text_input("RUT")
        nombre = st.text_input("Nombre")
        fecha = st.date_input("Fecha de admisión", value=date.today())
        submit = st.form_submit_button("➕ Agregar paciente")
        if submit:
            nuevo = {"RUT": rut, "Nombre": nombre, "Fecha admisión": fecha, "Diagnóstico clínico": diagnostico, "Código GES": codigo, "Patología GES": patologia, "Semáforo GES": SEMÁFORO_GES.get(patologia, "⚪"), "Clasificación": clasificacion, "Origen": "Manual"}
            st.session_state.ingresos_manuales = pd.concat([st.session_state.ingresos_manuales, pd.DataFrame([nuevo])], ignore_index=True)
            st.success("✅ Paciente agregado")

elif menu == "📄 Tabla Operativa":
    tablas = []
    if not st.session_state.admisiones.empty: tablas.append(st.session_state.admisiones)
    if not st.session_state.ingresos_manuales.empty: tablas.append(st.session_state.ingresos_manuales)
    if tablas:
        df_total = pd.concat(tablas, ignore_index=True)
        def resaltar_pendientes(row):
            condicion_ges = row["Patología GES"] != "NO GES"
            notificado = "notificado" in str(row["Estado de Notificación"]).lower()
            if condicion_ges and not notificado:
                return ['background-color: rgba(255, 75, 75, 0.1)'] * len(row)
            return [''] * len(row)
        st.subheader("📋 Gestión de Casos Detectados")
        st.dataframe(df_total.style.apply(resaltar_pendientes, axis=1), width='stretch', height=600)
    else:
        st.info("No hay registros.")

elif menu == "📤 Exportar":
    tablas = []
    if not st.session_state.admisiones.empty: tablas.append(st.session_state.admisiones)
    if not st.session_state.ingresos_manuales.empty: tablas.append(st.session_state.ingresos_manuales)
    if not tablas:
        st.warning("No hay datos")
        st.stop()
    df_export = pd.concat(tablas, ignore_index=True)
    buffer = BytesIO()
    df_export.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button("⬇️ Descargar Excel", data=buffer, file_name="GES_consolidado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")