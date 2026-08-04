import csv

db_pwd = "postgresql://postgres:[YOUR-PASSWORD]@db.qnxsiaxmcexhzdvaobqy.supabase.co:5432/postgres";

with open("DW_CATALOG_USE", "r") as f:
    rows = list(csv.DictReader(f, delimiter=';'))
for row in rows:
    embedding = embedContent(row["Descrizione Estesa"]);
    