import sqlite3

from itemadapter import ItemAdapter

DDL = '''CREATE TABLE IF NOT EXISTS mentions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL,
    url TEXT UNIQUE,
    source TEXT,
    date_publi TEXT,
    resume TEXT,
    score_alerte INTEGER DEFAULT 0,
    scraped_at TEXT DEFAULT CURRENT_TIMESTAMP
)'''


class CleanPipeline:
    def process_item(self, item, spider):
        a = ItemAdapter(item)
        a["titre"] = a.get("titre", "").strip()
        a["resume"] = a.get("resume", "").strip()[:300]
        return item


class SQLitePipeline:
    def open_spider(self, spider):
        self.cx = sqlite3.connect("veille.db")
        self.cx.execute(DDL)
        self.cx.commit()

    def process_item(self, item, spider):
        a = ItemAdapter(item)
        try:
            self.cx.execute(
                "INSERT OR IGNORE INTO mentions "
                "(titre,url,source,date_publi,resume,score_alerte) "
                "VALUES(?,?,?,?,?,?)",
                (a["titre"], a.get("url", ""), a.get("source", ""),
                 a.get("date_publi", ""), a.get("resume", ""), a.get("score_alerte", 0)))
            self.cx.commit()
        except sqlite3.Error as e:
            spider.logger.error(f"SQLite: {e}")
        return item

    def close_spider(self, spider):
        n = self.cx.execute("SELECT COUNT(*) FROM mentions").fetchone()[0]
        spider.logger.info(f"[OSINT] {n} mentions en base")
        self.cx.close()
