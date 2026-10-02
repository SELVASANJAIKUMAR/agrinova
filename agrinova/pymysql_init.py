"""PyMySQL compatibility shim for Django MySQL backend."""
import pymysql

pymysql.install_as_MySQLdb()
