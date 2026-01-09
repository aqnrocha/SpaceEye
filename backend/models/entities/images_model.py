from models.database import Database as db
from psycopg2.extras import RealDictCursor

class Images:
    
    def get_images():
        with db().conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM images
                """)
                rows = cur.fetchall()
                return rows
