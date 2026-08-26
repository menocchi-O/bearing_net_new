from pydantic import BaseModel
from matcher.normalize import TRANSFORM_STEPS

class ProcessRequest(BaseModel):
    id: int
    email: str
class ProcessedRequest(BaseModel):
    id: int
    azienda: str
    paese: str
    email: str
    contatto: str
    fax: str
    telefono: str
    articolo: str
    marca: str
    qta: str
    note: str
class InnerCodeRequest(BaseModel):
    id: int
    articolo: str
class EmbeddingRequest(BaseModel):
    id: int
    description: str
class SaveRequest(BaseModel):
    id:int
    original_email: str
    web_email: str
    required_code: str
    supplier_code: str
    inner_code: str
    required_brand: str
    email_response: str
    reply_address: str
# services/session.py

class MatchingSession:
    #the object will be instantiated like this: session = MatchingSession(supplier_df, company_df)
    #df stands for data frame
    def __init__(self, items_df):
        # Store dataframes
        self.items_map = {}
        self.items_df = items_df
        self.items_cols = list(items_df.columns)
        company_items = (
            self.items_df[["AppellativoCS", "IDArticolo", "Descrizione"]]
            .fillna("")
            .astype(str)
            .to_dict(orient="records")
            )

        for step_name, transform in TRANSFORM_STEPS:
        #at each step we apply a different formatting rule to the whole supplier set
            for item in company_items:
             key = transform(item["AppellativoCS"])
             self.items_map[key] = item
            

    