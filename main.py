# This is supposed to be a change applying only to demo_BearingNet branch
from plistlib import UID
from sys import deactivate_stack_trampoline

from pydantic_core.core_schema import DateSchema
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import Request
from fastapi import FastAPI
from fastapi.responses import JSONResponse
### FLOW VARIABLES ###
from services.matching_services import process_manual
import json
from services.classes import ProcessRequest, ProcessedRequest, SaveRequest, InnerCodeRequest, MatchingSession, EmbeddingRequest
import spacy
import json
import re
import csv
import unicodedata
import pyodbc
import pandas as pd
from spacy.matcher import Matcher
from asyncio.windows_events import NULL
from datetime import datetime
from logging import config
from operator import is_not
from ssl import SSLSession
import unicodedata
### DB CONNECTION ###
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from urllib.parse import quote_plus
import psycopg
from psycopg.rows import dict_row
### AI REQUEST ###
from openai import OpenAI
### SEND REPLY ###
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

### API VARIABLES ###
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
### FLOW VARIABLES ###
with open("appsettings.json", "r") as f:
    config = json.load(f)

CSV_FILE = config["CSV_FILE"]
CSV_FILE_DEMO = config["CSV_FILE_DEMO"]
CSV_ITEMS = config["CSV_ITEMS"]
DB_PASSWORD = config["DB_PASSWORD"]
EMAIL_PASSWORD = config["EMAIL_PASSWORD"]
PWD_ODBC = config["PWD_ODBC"]
OUTLOOK_EMAIL = config["OUTLOOK_EMAIL"]
OUTLOOK_PWD = config["OUTLOOK_PWD"]
SMTP_SERVER = config["SMTP_SERVER"]
SMTP_PORT = config["SMTP_PORT"]
df_articoli = None
session = None
### DB CONNECTION ###
encode_pwd = quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql://postgres.yfqqftigvcuhfjcgpber:{encode_pwd}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"
engine = create_engine(
    DATABASE_URL,
    connect_args = {"sslmode": "require"}
    )
### CATALOG CONNECTION ###
catalog_db = (f"postgresql://postgres.qnxsiaxmcexhzdvaobqy:{encode_pwd}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres")
conn = psycopg.connect(catalog_db)
### ODBC CONNECTION ###
odbc_pwd = quote_plus(PWD_ODBC)
conn_odbc = pyodbc.connect(
    f"DRIVER={config['DRIVER_ODBC']};"
    f"SERVER={config['SERVER_ODBC']};"
    f"DATABASE={config['DB_ODBC']};"
    f"UID={config['UID_ODBC']};"
    f"PWD={PWD_ODBC};"
)
cursor = conn_odbc.cursor()

nlp = spacy.load("it_core_news_sm")
matcher = Matcher(nlp.vocab)
client = OpenAI()
# adding values to the Matcher
matcher.add("AZIENDA", [[{"LOWER": {"IN": ["azienda", "firm", "company"]}}]])
matcher.add("PAESE", [[{"LOWER": {"IN": ["paese", "country", "pays", "nation"]}}]])
matcher.add("EMAIL", [[{"LOWER": {"IN": ["email", "e-mail", "mail"]}}]])
matcher.add("CONTATTO", [[{"LOWER": {"IN": ["contatto", "contact", "riferimento"]}}]])
matcher.add("TELEFONO", [[{"LOWER": {"IN": ["telefono", "telephone", "phone", "portable"]}}]])
matcher.add("ARTICOLO", [[{"LOWER": {"IN": ["codice", "cod", "code", "article", "articolo", "item"]}}]])
matcher.add("MARCA", [[{"LOWER": {"IN": ["brand", "marca", "marque"]}}]])
matcher.add("QTA", [[{"LOWER": {"IN": ["quantita", "qta", "quantity", "qt"]}}]])
matcher.add("NOTE", [[{"LOWER": {"IN": ["note", "notes"]}}]])
# define keywords
SIGNATURE_PATTERNS = [
    "tel", "phone", "fax", "mob", "cell",
    "email", "@",
    "via", "street", "address", "rue",
    "www", "http", "piva", "partita iva",
    "v.le", "PEC", "srl", "s.r.l.",
    "contatto", "azienda", "bearingnet",
    "contact", "company", "society",
    "paese", "country"
]
SALUTATION_PATTERN = [
    "distinti", "saluti",
    "kind regards", "rergards",
    "cordialmente", "buona giornata",
    "informativa", "warning"
]

### AI REQUEST ###
@app.post("/websearch")
def web_search(req: ProcessRequest):
    prompt = build_prompt(req.email)
    llm_output = call_llm(prompt)

    return {
            "id": req.id,
            "prompt": prompt,
            "llm_response": llm_output
    }
def build_prompt(email_text: str) -> str:
    return f"""
    You are a product information extraction assistant.

    Your task is to analyze a customer email and extract all requested products.

    Return ONLY valid JSON with this structure:

    {{
        "items": [
        {{
            "item_code": "",
            "brand": "",
            "quantity": "",
            "description": "",
            "description_source": "email",
            "notes": ""
        }}
    ]
    }}

    Rules:

    - Extract the product code only if it is explicitly present in the email.
    - Never invent or guess product codes.
    - Extract the brand only if explicitly mentioned.
    - Extract quantity only if explicitly mentioned.
    - The description field must contain a concise technical description of the requested product.

    Important fallback rule:
    - If you cannot identify either a product code OR a meaningful product description, put the complete email body in the "description" field.
    - Do not summarize or modify the email in this fallback case.
    - Preserve the original text so that another process can optimize it later.

    Ignore:
    - greetings,
    - signatures,
    - delivery addresses,
    - prices,
    - commercial discussions,
    unless they contain information useful for identifying the product.

    If multiple products are requested, return multiple objects in the items array.

    Email:
    \"\"\"{email_text}\"\"\"
    """
def call_llm(prompt: str):
    response = client.chat.completions.create(
        model = "gpt-4.1-mini",
        messages = [{"role": "user", "content": prompt}],
        temperature = 0
    )
    return response.choices[0].message.content

### AI REQUEST EXTRACT DESCRIPTION ###
@app.post("/extractDescription")
def extractDescription(req: ProcessRequest):
    prompt = reduceDescription(req.email)
    llm_output = call_llm(prompt)
    return {
        "id": req.id,
        "prompt": prompt,
        "llm_response": llm_output
    }
def reduceDescription(email_text: str):
    return f"""
        You are a product search query optimizer.

        Your task is to transform customer emails into concise technical search descriptions that will be used to find matching products in a catalog.

        Extract and keep only information useful for identifying the requested product:
        - product type
        - technical characteristics
        - dimensions
        - materials
        - standards
        - brands or manufacturers
        - application context if it helps identify the product

        Remove:
        - greetings and polite expressions
        - customer names
        - delivery information
        - prices
        - urgency requests
        - commercial discussions
        - unrelated context

        Do not invent information.
        Do not guess product codes.
        Do not identify the exact product.
        Do not add specifications that are not present in the email.

        If the email does not contain enough information to describe a product, return an empty string.

        Return ONLY valid JSON matching this schema:

    {{
        "items": [
        {{
            "item_code": "",
            "brand": "",
            "quantity": "",
            "description": "",
            "description-source": "full text",
            "notes": ""
        }}
    ]
    }}
        
        Email:
        \"\"\"{email_text}\"\"\"
    """
### DATA EXTRACTION FROM EMAIL TEXT ###
@app.post("/extract")
def email_parser(req: ProcessRequest):
    norm_em = normalize(req.email)
    inquiry_field = parse_email(norm_em)
    if not any(inquiry_field.values()):
       inquiry_field = apply_matcher(norm_em)
    
    proReq = ProcessedRequest(
       
        id=req.id,
        azienda=inquiry_field.get("azienda", ""),
        paese=inquiry_field.get("paese", ""),
        email=inquiry_field.get("email", ""),
        contatto=inquiry_field.get("contatto", ""),
        fax=inquiry_field.get("fax", ""),
        telefono=inquiry_field.get("telefono", ""),
        articolo=inquiry_field.get("articolo", ""),
        marca=inquiry_field.get("marca", ""),
        qta=inquiry_field.get("qta", ""),
        note=inquiry_field.get("note", "")
    )
    # populate window for web-search prompt
    return proReq
def normalize(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
        ).lower()
def parse_email(email):
    results = {}

    LABELS = {
        "azienda": ["azienda"],
        "paese": ["paese", "country"],
        "email": ["email", "e-mail"],
        "contatto": ["contatto", "contact"],
        "telefono": ["telefono", "phone"],
        "articolo": ["articolo", "article", "item"],
        "marca": ["marca", "brand"],
        "qta": ["qta", "qt", "quantita", "quantity"],
        "note": ["note"]
    }
    lines = email.split("\n")

    for line in lines:
        clean_line = line.strip().lower()

        for field, keywords in LABELS.items():
            for key in keywords:
                if clean_line.startswith(key):
                    
                    # split on first colon
                    parts = line.split(":", 1)

                    if len(parts) > 1:
                        value = parts[1].strip()
                        results[field] = value

    return results
def apply_matcher(email):
    doc = nlp(email)
    matches = matcher(doc)

    results = {}

    for match_id, start, end in matches:
        label_name = nlp.vocab.strings[match_id]
        for token in doc[end:end+50]:
            if not token.is_punct and not token.is_space:
                value = token.text
                # store using match_id as key
                results[label_name.lower()] = token.text
                break
    return results

### CLEAN EMAIL TEXT ###
@app.post("/clean")
def clean_email(req: ProcessRequest):
    body = req.email
     # ---------------- CLEANING ----------------
     # normalize newlines
    body = re.sub(r"\r\n|\r", "\n", body)
    body = re.sub(r"^(from|to|subject|cc|da|a):.*$", "", body, flags=re.MULTILINE | re.I)
        # normallize unicode
    body = normalize_text(body)
    
    lines = [l.strip() for l in body.split("\n") if l.strip()]

    body_sentences = []

    # ---------------- FILTERING ----------------   
    for line in lines:
        is_end = is_ending_sentence(line)
        if is_end:
           break
        is_noise = is_noise_sentence(line)
        if is_noise:
           continue
        else:
           body_sentences.append(line)
        # fallback if everything removed
        if not body_sentences:
           body_sentences = lines[:5]
    return {"body" : "\n".join(body_sentences)}
def is_noise_sentence(sentence):
    s = sentence.lower()
    if any(p in s for p in SIGNATURE_PATTERNS):
        return True
    return False
def is_ending_sentence(sentence):
    s = sentence.lower()
    if any(w in s for w in SALUTATION_PATTERN):
        return True
    return False

### MARK AS READ - SAVE TO DB ###
@app.post("/save")
def save_email(req: SaveRequest):
    record = {
        "id": req.id,
        "original_email": req.original_email,
        "web_email": req.web_email,
        "llm_response": req.llm_response,
        "required_code": req.required_code,
        "supplier_code": req.supplier_code,
        "inner_code": req.inner_code,
        "required_brand": req.required_brand,
        "email_response": req.email_response,
        "reply_address": req.reply_address
    }
    save_example(record)
    send_reply(record)
    mark_as_processed(req.id, req.original_email)
    return {"status": "saved"}

### SKIP ###
@app.post("/skip")
async def skip_email(req: ProcessRequest):
    mark_as_processed(req.id, req.email)
    return {"status": "skipped"}

### FIND INNER CODE ###
@app.get("/search_code")
def search_item(q: str):
    with conn.cursor(row_factory=dict_row) as cur:

            cur.execute(
                """
                SELECT
                    id_interno,
                    codice,
                    descrizione_estesa,
                    similarity(codice, %s) AS score
                FROM products_new
                WHERE codice %% %s
                ORDER BY score DESC
                LIMIT 10
                """,
                (q, q)
            )

            rows = cur.fetchall()
            scored = [
                {
                    "status": "review",
                    "candidate": row["codice"],
                    "inner_code": row["id_interno"],
                    "required_code": row["codice"],   # or another field if you have one
                    "description": row["descrizione_estesa"],
                    "score": row["score"],
                }
            for row in rows
            ]
    return scored;

### FIND EMBEDDINGS ###
@app.post("/find_embeddings")
def find_embeddings(req: EmbeddingRequest):

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=req.description
    )

    embedding = response.data[0].embedding

    with psycopg.connect(catalog_db) as conn:
        with conn.cursor(row_factory=dict_row) as cur:

            cur.execute(
                """
                SELECT
                    id_interno,
                    codice,
                    descrizione_estesa,
                    1 - (embedding <=> %s::vector) AS score
                FROM products_new
                ORDER BY embedding <=> %s::vector
                LIMIT 10
                """,
                (embedding, embedding)
            )

            rows = [
                r for r in cur.fetchall()
            ]


    return [
        {
            "status": "review",
            "candidate": row["codice"],
            "inner_code": row["id_interno"],
            "required_code": row["codice"],
            "description": row["descrizione_estesa"],
            "score": row["score"],
        }
        for row in rows
    ]
### FIND ERP DETAILS ###
@app.get("/get_details")
def get_details(codmat: str):
    ### qta ord for - qta ricevuta - qta spedita ###
    ### VERZOLLA ###
    cursor.execute("""
        SELECT SUM(QTYSTU_0) - SUM(RCPQTYSTU_0)
        FROM TEST.PORDERQ
        WHERE ITMREF_0 = ? AND PRHFCY_0='V10S1'
    """, (codmat,))
    row = cursor.fetchone()[0]
    if row:
        qtaOrdForVrz = row
    else:
        qtaOrdForVrz= 0
    ### AMATI ###
    cursor.execute("""
        SELECT SUM(QTYSTU_0) - SUM(RCPQTYSTU_0)
        FROM TEST.PORDERQ
        WHERE ITMREF_0 = ? AND PRHFCY_0='V20S1'
    """, (codmat,))
    row = cursor.fetchone()[0]
    if row:
        qtaOrdForAma = row
    else:
        qtaOrdForAma = 0
    ### ORLA COMO ###
    cursor.execute("""
        SELECT SUM(QTYSTU_0) - SUM(RCPQTYSTU_0)
        FROM TEST.PORDERQ
        WHERE ITMREF_0 = ? AND PRHFCY_0='V30S1'
    """, (codmat,))
    row = cursor.fetchone()[0]
    if row:
        qtaOrdForCo = row
    else:
        qtaOrdForCo = 0
    ### ORLA CIVATE ###
    cursor.execute("""
        SELECT SUM(QTYSTU_0) - SUM(RCPQTYSTU_0)
        FROM TEST.PORDERQ
        WHERE ITMREF_0 = ? AND PRHFCY_0='V30S2'
    """, (codmat,))
    row = cursor.fetchone()[0]
    if row:
        qtaOrdForCv = row
    else:
        qtaOrdForCv = 0
    #################################################
    ### giacenza - qta allocata interna - qta allocata globale - qta ord cli ###
    ### VERZOLLA ###
    cursor.execute("""
        SELECT PHYSTO_0, PHYALL_0, GLOALL_0, SALSTO_0
        FROM TEST.ITMMVT
        WHERE ITMREF_0 = ? AND STOFCY_0 = 'V10S1'
    """, (codmat,))
    row = cursor.fetchone()
    if row:
        giacVrz, allIntVrz, allGloVrz, ordCliVrz = row
    else:
        giacVrz, allIntVrz, allGloVrz, ordCliVrz = 0
    ### AMATI ###
    cursor.execute("""
        SELECT PHYSTO_0, PHYALL_0, GLOALL_0, SALSTO_0
        FROM TEST.ITMMVT
        WHERE ITMREF_0 = ? AND STOFCY_0 = 'V20S1'
    """, (codmat,))
    row = cursor.fetchone()
    if row:
        giacAma, allIntAma, allGloAma, ordCliAma = row
    else:
        giacAma, allIntAma, allGloAma, ordCliAma = 0
    ### ORLA COMO ###
    cursor.execute("""
        SELECT PHYSTO_0, PHYALL_0, GLOALL_0, SALSTO_0
        FROM TEST.ITMMVT
        WHERE ITMREF_0 = ? AND STOFCY_0 = 'V30S1'
    """, (codmat,))
    row = cursor.fetchone()
    if row:
        giacCo, allIntCo, allGloCo, ordCliCo = row
    else:
        giacCo, allIntCo, allGloCo, ordCliCo = 0
    ### ORLA CIVATE ###
    cursor.execute("""
        SELECT PHYSTO_0, PHYALL_0, GLOALL_0, SALSTO_0
        FROM TEST.ITMMVT
        WHERE ITMREF_0 = ? AND STOFCY_0 = 'V30S2'
    """, (codmat,))
    row = cursor.fetchone()
    if row:
        giacCv, allIntCv, allGloCv, ordCliCv = row
    else:
        giacCv, allIntCv, allGloCv, ordCliCv = 0
    #################################################
    ### qta disponibile ###
    ### VERZOLLA ###
    cursor.execute("""
     SELECT SUM(PHYSTO_0 - SALSTO_0)
     FROM TEST.ITMMVT
     WHERE ITMREF_0 = ? AND STOFCY_0 = 'V10S1'
    """, (codmat,))
    qtaDispoVrz = cursor.fetchone()[0]
    ### AMATI ###
    cursor.execute("""
     SELECT SUM(PHYSTO_0 - SALSTO_0)
     FROM TEST.ITMMVT
     WHERE ITMREF_0 = ? AND STOFCY_0 = 'V20S1'
    """, (codmat,))
    qtaDispoAma = cursor.fetchone()[0]
    ### ORLA COMO ###
    cursor.execute("""
     SELECT SUM(PHYSTO_0 - SALSTO_0)
     FROM TEST.ITMMVT
     WHERE ITMREF_0 = ? AND STOFCY_0 = 'V30S1'
    """, (codmat,))
    qtaDispoCo = cursor.fetchone()[0]
    ### ORLA CIVATE ###
    cursor.execute("""
     SELECT SUM(PHYSTO_0 - SALSTO_0)
     FROM TEST.ITMMVT
     WHERE ITMREF_0 = ? AND STOFCY_0 = 'V30S2'
    """, (codmat,))
    qtaDispoCv = cursor.fetchone()[0]
    #################################################
    ### pzo lordo ###
    cursor.execute("""
        SELECT PRI_0
        FROM TEST.SPRICLIST
        WHERE PLI_0='40LORD' AND PLICRI3_0 = ?;
     """, (codmat,))
    row = cursor.fetchone()
    pzoLordo = row[0] if row else None
    ### pzo netto/aum - sco1 - sco2 - sco3 - aum1 - aum2 ###
    cursor.execute("""
        DECLARE @SCO1 FLOAT, @SCO2 FLOAT, @SCO3 FLOAT, @PZO FLOAT, @NETTO FLOAT, @AUM1 FLOAT, @AUM2 FLOAT;
        -- SCONTI PROMO
         -- 30PROM VALIDITY
            DECLARE @VALID_30PROM BIT, @STRDATE_30PROM DATETIME, @ENDDATE_30PROM DATETIME;

            SELECT @STRDATE_30PROM = PLISTRDAT_0, 
	               @ENDDATE_30PROM = PLIENDDAT_0
            FROM TEST.SPRICLIST
            WHERE PLI_0 = '30PROM' AND PLICRI3_0= ?

            IF GETDATE() < @STRDATE_30PROM  OR GETDATE() > @ENDDATE_30PROM
	            BEGIN
		            SET @VALID_30PROM=0
	            END;
            ELSE
	            BEGIN
		            SET @VALID_30PROM=1
	            END;
            IF @VALID_30PROM = 1
                BEGIN    
                    SELECT TOP (1)
                        @SCO1 = DCGVAL_0,
                        @SCO2 = DCGVAL_1,
                        @SCO3 = DCGVAL_2
                    FROM TEST.SPRICLIST
                    WHERE PLI_0 = '30PROM'
                      AND PLICRI1_0 = ?;
                END;

        -- SCONTO INDISTINTO
        IF @SCO1 IS NULL AND @SCO2 IS NULL AND @SCO3 IS NULL
        BEGIN
            -- 51IND VALIDITY
            DECLARE @VALID_51IND BIT, @STRDATE_51IND DATETIME, @ENDDATE_51IND DATETIME;
            SELECT @STRDATE_51IND = PLISTRDAT_0, 
	               @ENDDATE_51IND = PLIENDDAT_0
            FROM TEST.SPRICLIST
            WHERE PLI_0 = '51IND' AND PLICRI1_0 = (
                                SELECT TCLCOD_0
                                FROM TEST.ITMMASTER
                                WHERE ITMREF_0 = ?
                    );

            IF GETDATE() < @STRDATE_51IND  OR GETDATE() > @ENDDATE_51IND
	            BEGIN
		            SET @VALID_51IND = 0
	            END;
            ELSE
	            BEGIN
		            SET @VALID_51IND = 1
	            END

            IF @VALID_51IND = 1
                BEGIN
                    SELECT @SCO1 = DCGVAL_0
                    FROM TEST.SPRICLIST
                    WHERE PLI_0 = '51IND' AND PLICRI1_0 = (
                                SELECT TCLCOD_0
                                FROM TEST.ITMMASTER
                                WHERE ITMREF_0 = ?
                    );
                    SET @SCO2 = 0;
                    SET @SCO3 = 0;
                END
            ELSE
                BEGIN
                    SET @SCO1 = 0;
                    SET @SCO2 = 0;
                    SET @SCO3 = 0;
                END;

        END
        -- VALIDITY 40LORD
        DECLARE @VALID_40LORD BIT, @STRDATE_40LORD DATETIME, @ENDDATE_40LORD DATETIME;
            SELECT @STRDATE_40LORD = PLISTRDAT_0, 
	               @ENDDATE_40LORD = PLIENDDAT_0
            FROM TEST.SPRICLIST
            WHERE PLI_0 = '40LORD' AND PLICRI3_0 = ?;

            IF GETDATE() < @STRDATE_40LORD  OR GETDATE() > @ENDDATE_40LORD
	            BEGIN
		            SET @VALID_40LORD = 0
	            END;
            ELSE
	            BEGIN
		            SET @VALID_40LORD = 1
	            END

            IF @VALID_40LORD = 1
                -- CALCOLO PREZZO LORDO
                BEGIN
                    SELECT @PZO = PRI_0, 
                           @AUM1 = DCGVAL_7,
                           @AUM2 = DCGVAL_8
                    FROM TEST.SPRICLIST
                    WHERE PLI_0 = '40LORD' AND PLICRI3_0 = ?;
                    -- CALCOLO PREZZO NETTO
                    SELECT @NETTO =
                                    @PZO
                                    * (1 - (ISNULL(@SCO1, 0) / 100.0))
                                    * (1 - (ISNULL(@SCO2, 0) / 100.0))
                                    * (1 - (ISNULL(@SCO3, 0) / 100.0))
                                    * (1 + (ISNULL(@AUM1, 0) / 100.0))
                                    * (1 + (ISNULL(@AUM2, 0) / 100.0));

                END
                
            SELECT @NETTO AS pzoNetto,
                   @SCO1 AS SCO1,
                   @SCO2 AS SCO2,
                   @SCO3 AS SCO3,
                   @AUM1 AS AUM1,
                   @AUM2 AS AUM2;
                   """, (codmat,codmat,codmat,codmat,codmat,codmat,));
    row = cursor.fetchone()
    if row:
        pzoNetto, SCO1, SCO2, SCO3, AUM1, AUM2 = row
    else:
        pzoNetto, SCO1, SCO2, SCO3, AUM1, AUM2 = None
     ### desc1 - desc2 - desc3 - grpscoven ###
    ### desc1 - desc2 - desc3 - grpscoven ###
    cursor.execute("""
        SELECT ITMDES1_0, ITMDES2_0, ITMDES3_0, YGRPCUS_0
        FROM TEST.ITMMASTER
        WHERE ITMREF_0 = ?
     """, (codmat,))
    row = cursor.fetchone()
    if row:
        desc1, desc2, desc3, grpscoven = row
    else:
        desc1, desc2, desc3, grpscoven = None

    return {
        "qtaOrdForVrz" : qtaOrdForVrz,
        "qtaOrdForAma" : qtaOrdForAma,
        "qtaOrdForCo" : qtaOrdForCo,
        "qtaOrdForCv" : qtaOrdForCv,
        "qtaDispoVrz": qtaDispoVrz,
        "qtaDispoAma": qtaDispoAma,
        "qtaDispoCo": qtaDispoCo,
        "qtaDispoCv": qtaDispoCv,
        "giacAma": giacAma,
        "giacVrz": giacVrz,
        "giacCo": giacCo,
        "giacCv": giacCv,
        "allIntVrz": allIntVrz,
        "allIntAma": allIntAma,
        "allIntCo": allIntCo,
        "allIntCv": allIntCv,
        "allGloVrz": allGloVrz,
        "allGloAma": allGloAma,
        "allGloCo": allGloCo,
        "allGloCv": allGloCv,
        "ordCliVrz": ordCliVrz,
        "ordCliAma": ordCliAma,
        "ordCliCo": ordCliCo,
        "ordCliCv": ordCliCv,
        "pzoLordo": pzoLordo,
        "pzoNetto": pzoNetto,
        "SCO1": SCO1,
        "SCO2": SCO2,
        "SCO3": SCO3,
        "AUM1": AUM1,
        "AUM2": AUM2,
        "desc1": desc1,
        "desc2": desc2,
        "desc3": desc3,
        "grpscoven": grpscoven
    }
@app.get("/get_details_demo")
def get_details_demo(innerCode: str):
    with conn.cursor(row_factory=dict_row) as cur:
        sito = cur.execute(
            """
            SELECT sito
            FROM DW_CATALOG_USE
            WHERE id_interno = innerCode
            """
        )


    return  {
                f"ordFor{sito}" : f"""
                    SELECT ord_for
                    FROM DW_CATALOG_USE
                    WHERE id_interno={innerCode} AND sito={sito}
                """,
                f"qtaDispo{sito}" : f"""
                    SELECT dispo_ven
                    FROM DW_CATALOG_USE
                    WHERE id_interno={innerCode} AND sito={sito}
                """,
                f"giac{sito}" : f"""
                    SELECT giac
                    FROM DW_CATALOG_USE
                    WHERE id_interno={innerCode} AND sito={sito}
                """,
                f"allInt{sito}" : f"""
                    SELECT all_int
                    FROM DW_CATALOG_USE
                    WHERE id_interno={innerCode} AND sito={sito}
                """,
                f"allGlo{sito}" : f"""
                    SELECT all_glo
                    FROM DW_CATALOG_USE
                    WHERE id_interno={innerCode} AND sito={sito}
                """,
                f"ordCli{sito}" : f"""
                    SELECT ord_cli
                    FROM DW_CATALOG_USE
                    WHERE id_interno={innerCode} AND sito={sito}
                """,
                f"pzoLordo{sito}" : f"""
                    SELECT lordo
                    FROM DW_CATALOG_USE
                    WHERE id_interno={innerCode} AND sito={sito}
                """,
                f"pzoNetto{sito}" : f"""
                    SELECT netto
                    FROM DW_CATALOG_USE
                    WHERE id_interno={innerCode} AND sito={sito}
                """,
                f"SCO1" : f"""
                    SELECT sco1
                    FROM DW_CATALOG_USE
                    WHERE id_interno={innerCode} AND sito={sito}
                """,
                f"SCO2" : f"""
                    SELECT sco2
                    FROM DW_CATALOG_USE
                    WHERE id_interno={innerCode} AND sito={sito}
                """,
                f"SCO3" : f"""
                    SELECT sco3
                    FROM DW_CATALOG_USE
                    WHERE id_interno={innerCode} AND sito={sito}
                """,
                f"AUM1" : f"""
                    SELECT aum1
                    FROM DW_CATALOG_USE
                    WHERE id_interno={innerCode} AND sito={sito}
                """,
                f"AUM2" : f"""
                    SELECT aum2
                    FROM DW_CATALOG_USE
                    WHERE id_interno={innerCode} AND sito={sito}
                """,
                f"desc" : f"""
                    SELECT descrizione_breve
                    FROM DW_CATALOG_USE
                    WHERE id_interno={innerCode} AND sito={sito}
                """,
                "grpscoven": ""

        }       
    

### SEND REPLY ###
def send_reply(record):
    subject = "Request processed successfully"

    body = f"""
        Hello,

        Your request has been processed successfully.

        Collected data:

        Item: {record.get("required_code")}
        Timestamp: {record.get("timestamp")}

        Best regards
    """

    msg = MIMEMultipart()
    msg["From"] = OUTLOOK_EMAIL
    msg["To"] = record.get("replyAddress")
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(OUTLOOK_EMAIL, OUTLOOK_PWD)
        server.send_message(msg)



### UTILITIES ###
def html_to_text(html):
    soup = BeautifulSoup(html, "html.parser")
    # remove scripts/style
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    return text
def decode_body(body):
    if isinstance(body, str):
        return body
    detected = chardet.detect(body)
    encoding = detected["encoding"] or "utf-8"
    try:
        return body.decode(encoding)
    except:
        return body.decode("utf-8", errors="ignore")
def normalize_text(text):
    text = unicodedata.normalize("NFKC",text)
    return text
def get_sender_email(msg):
    
    # 2. headers
    headers = msg.transport_headers
    if headers:
        headers = decode_body(headers)

        # try multiple patterns
        patterns = [
            r"From:.*<(.+?)>",
            r"From:\s*([^\s]+@[^\s]+)"    
        ]
        for p in patterns:
            m = re.search(p, headers)
            if m:
                return m.group(1)

    #  3. fallback
    return msg.sender_name or ""
def get_sender_tokens(sender):
    sender = sender.lower()
    tokens = set()

    # split email
    if "@" in sender:
        name_part, domain = sender.split("@")
        # name tokens
        tokens.update(re.split(r"[._\-]", name_part))
        # full name
        tokens.add(name_part)
        # domain/company
        company = domain.split(".")[0]
        tokens.add(company)
    else:
        # fallback: split name
        tokens.update(sender.split())
    # remove very short tokens
    tokens = {t for t in tokens if len(t) >= 3}

    return tokens
def get_next_email():
    with open(CSV_FILE_DEMO, newline='') as f:
        reader = list(csv.DictReader(f, delimiter=','))
    for row in reader:
        if row["Processed"] == "":
            return row
    return None
def mark_as_processed(email_id, email_body):
    with open(CSV_FILE_DEMO, newline='') as f:
        rows = list(csv.DictReader(f, delimiter=','))

    for row in rows:
        if row["ID"] == str(email_id):
            row["Processed"] = "true"
            if email_body == "skip":
                row["Status"] = "skipped"
            else:
                row["Status"] = "saved"
    with open(CSV_FILE_DEMO, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
def save_example(data):
    llm_response = data["llm_response"]

    if isinstance(llm_response, str):
        try:
            llm_response = json.loads(llm_response)
        except :
            llm_response = {}

    with engine.connect() as conn:
        conn.execute(
            text("""
            INSERT INTO output (
                id, 
                timestamp,
                original_email,
                web_email,
                llm_response,
                required_code,
                supplier_code,
                inner_code,
                required_brand,
                email_response
            )
            VALUES (
                    :id, 
                    :timestamp, 
                    :original_email, 
                    :web_email,
                    :llm_response,
                    :required_code,
                    :supplier_code,
                    :inner_code,
                    :required_brand,
                    :email_response
                    )
            """),
            {
                "id": data["id"],
                "timestamp": datetime.now().isoformat(),
                "original_email": data["original_email"],
                "web_email": data["web_email"],
                "llm_response": json.dumps(data["llm_response"]),
                "required_code": data["required_code"],
                "supplier_code": data["supplier_code"],
                "inner_code": data["inner_code"],
                "required_brand": data["required_brand"],
                "email_response": data["email_response"]
            }
        )
        conn.commit()
### DASHBOARD ###
@app.get("/")
def index():
    return FileResponse("static/index.html")
@app.on_event("startup")
def startup_event():
    # Global dataframe
    global df_articoli
    df_articoli = pd.read_csv(CSV_ITEMS, dtype=str, sep=";").fillna("");
    app.state.session = MatchingSession(df_articoli);
    print (
        f"Loaded rows: {len(df_articoli)}"   
    )
@app.get("/next")
def get_next():
    row = get_next_email()

    if not row:
        return {"status": "done"}

    return {
        "id": row["ID"],
        "email": row["InquiryBody"]
    }
