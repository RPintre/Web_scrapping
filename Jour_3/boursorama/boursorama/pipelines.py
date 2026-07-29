# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import sqlite3

from itemadapter import ItemAdapter

DDL = """CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    libelle TEXT NOT NULL,
    cours REAL,
    variation REAL,
    volume INTEGER,
    isin TEXT UNIQUE,
    scraped_at TEXT DEFAULT CURRENT_TIMESTAMP
)"""


class SQLitePipeline:
    def open_spider(self, spider):
        self.cx = sqlite3.connect("bourse.db")
        self.cx.execute(DDL)
        self.cx.commit()

    def process_item(self, item, spider):
        a = ItemAdapter(item)
        try:
            self.cx.execute(
                "INSERT OR IGNORE INTO actions (libelle, cours, variation, volume, isin) "
                "VALUES (:libelle, :cours, :variation, :volume, :isin)",
                dict(a),
            )
            self.cx.commit()
        except sqlite3.Error as e:
            spider.logger.error(f"SQLite: {e}")
        return item

    def close_spider(self, spider):
        n = self.cx.execute("SELECT COUNT(*) FROM actions").fetchone()[0]
        spider.logger.info(f"BDD : {n} actions en base")
        self.cx.close()
