""" Quick code to check duplicate rows in gurmukhi_text column ... there are a lot"""
from paathguide.models import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Raw SQL query to find duplicates
query = text("""
    SELECT gurmukhi_text, COUNT(*) as count 
    FROM verses 
    GROUP BY gurmukhi_text 
    HAVING COUNT(*) > 1
    ORDER BY count DESC
""")

result = db.execute(query)
for row in result:
    print(f"'{row.gurmukhi_text}' appears {row.count} times")

db.close()