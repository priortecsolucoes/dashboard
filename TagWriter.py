from fastapi import FastAPI
import psycopg2
from pydantic import BaseModel

app = FastAPI()


class WriteTagRequest(BaseModel):
    tag_name: str
    string_value: str
    int_value: int
    double_value: float


def get_db_connection():
    return psycopg2.connect(
        host="roundhouse.proxy.rlwy.net",
        database="railway",
        user="postgres",
        password="XWhTqAztzzYuAqvUcgWCUJUJmnEJliDK",
        port=28938
    )


@app.put("/update-tag")
def write_tag(request: WriteTagRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    update_query = """
    UPDATE tag_value
    SET string_value = %s, int_value = %s, double_value = %s
    WHERE tag_id = (
        SELECT id FROM tag WHERE name = %s
    ) AND %s = 'string'
    """

    cursor.execute(update_query, (request.string_value,
                   request.int_value, request.double_value, request.tag_name))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Tag atualizada com sucesso"}
