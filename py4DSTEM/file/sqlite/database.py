import sqlite3
from sqlite3 import Error

class SingletonInstane:
  __instance = None

  @classmethod
  def __getInstance(cls):
    return cls.__instance

  @classmethod
  def instance(cls, *args, **kargs):
    cls.__instance = cls(*args, **kargs)
    cls.instance = cls.__getInstance
    return cls.__instance


class DBFileList(SingletonInstane):
    def __init__(self):
        pass

    def _create_connection(self):
        self.maxCount = 5
        self.conn = None
        self.db_file = r"pythonsqlite.db"
        try:
            self.conn = sqlite3.connect(self.db_file)
        except Error as e:
            print(e)

    def _create_table_OpenedFileList(self):
        sql_create_OpenedFileList_table = """ CREATE TABLE IF NOT EXISTS OpenedFileList (
        id integer PRIMARY KEY,
        filePath text NOT NULL, 
        dataType text
        );
        """
        if self.conn is not None:
            self.c = self.conn.cursor()
            self.c.execute(sql_create_OpenedFileList_table)
        else :
            print("Error! cannot create the database connection.")

    def _insert(self, filePath, dataType):
        sql = " INSERT INTO OpenedFileList(filePath, dataType) VALUES(?,?) "
        self.c.execute(sql, (filePath,dataType))

    def _deleteByFilePath(self, filePath, dataType):
        sql = " DELETE FROM OpenedFileList WHERE filePath = ? AND dataType = ?"
        self.c.execute(sql, (filePath, dataType))

    def _getOpenedFileList(self):
        sql = " SELECT * FROM OpenedFileList "
        self.c.execute(sql)
        # self.conn.commit()
        self.c:sqlite3.Cursor
        rs = self.c.fetchall()
        return rs

    def _close_connection(self):
        try:
            self.conn.close()
        except Error as e:
            print(e)

    def insertOpenFileList(self, filePath, dataType):
        self._create_connection()
        self._create_table_OpenedFileList()
        self._deleteByFilePath(filePath, dataType)
        self._insert(filePath, dataType)
        self._delete()
        self.conn.commit()
        self._close_connection()

    def getOpenFileList(self):
        self._create_connection()
        self._create_table_OpenedFileList()
        rs = self._getOpenedFileList()
        self._close_connection()
        return rs

    def _countList(self):
        sql = "SELECT COUNT(*) FROM OpenedFileList"
        exe = self.c.execute(sql)
        rs = exe.fetchall()
        n = rs[0][0]
        return n

    def _delete(self):

        n = self._countList()
        if n > self.maxCount:
            sql = " DELETE FROM OpenedFileList WHERE id IN " \
                  "(SELECT id FROM OpenedFileList DESC LIMIT " + str(n-self.maxCount) + ")"
            self.c.execute(sql)

if __name__ == '__main__':
    db = DBFileList()
    db.insertOpenFileList("testFilePath", "TEST dddd")
    print(db.getOpenFileList())