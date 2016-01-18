#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb, sys


class Init_Base(object):
    '''
        所有类的基类
    '''
    __instance   = None
    __host       = None
    __user       = None
    __password   = None
    __database   = None
    __session    = None
    __connection = None

    def __init__(self,db_server_info):
        #self.init_server_info = init_server_info
        self.__db_user = db_server_info['db_host_user']
        self.__db_host = db_server_info['db_host_ip']
        self.__db_port = int(db_server_info['db_host_port'])
        self.__db_pass = db_server_info['db_host_password']
        self.__db_name = db_server_info['db_dbname']
        self.charset = "utf8"

    def __new__(cls, *args, **kwargs):
        if not cls.__instance or not cls.__database:
             cls.__instance = super(Init_Base, cls).__new__(cls,*args,**kwargs)
        return cls.__instance
    ## End def __new__

    def __open(self):
        try:
            cnx = MySQLdb.connect(host = self.__db_host, user = self.__db_user, passwd = self.__db_pass, db = self.__db_name, port = self.__db_port,charset = self.charset)
            self.__connection = cnx
            self.__session    = cnx.cursor()
        except MySQLdb.Error as e:
            print "Error %d: %s" % (e.args[0],e.args[1])
            sys.exit(1)
    ## End def __open


    def __open_for_desc(self):
        try:
            cnx = MySQLdb.connect(host = self.__db_host, user = self.__db_user, passwd = self.__db_pass, db = self.__db_name, port = self.__db_port,charset = self.charset,cursorclass=MySQLdb.cursors.DictCursor)
            self.__connection = cnx
            self.__session    = cnx.cursor()
        except MySQLdb.Error as e:
            print "Error %d: %s" % (e.args[0],e.args[1])
            sys.exit(1)


    def __close(self):
        self.__session.close()
        self.__connection.close()
    ## End def __close

    def select(self, table, where=None, *args, **kwargs):
        result = None
        query = 'SELECT '
        keys = args
        values = tuple(kwargs.values())
        
        l = len(keys) - 1

        for i, key in enumerate(keys):
            query += "`"+key+"`"+" "
            if i < l:
                query += ","
        ## End for keys

        query += 'FROM %s' % table

        if where:
            query += " WHERE %s" % where

        #print query,values
        ## End if where
        self.__open()
        self.__session.execute("SET NAMES utf8");
        self.__session.execute(query, values)
        number_rows = self.__session.rowcount
        number_columns = len(self.__session.description)

        if number_rows >= 1 and number_columns > 1:
            result = [item for item in self.__session.fetchall()]
        else:
            result = [item[0] for item in self.__session.fetchall()]
        self.__close()
        return result
    ## End def select

    def update(self, table, where=None, *args, **kwargs):
        #import sys
        query  = "UPDATE %s SET " % table
        keys   = kwargs.keys()
        values = tuple(kwargs.values()) + tuple(args)

        # print tuple(args)
        # sys.exit()
        l = len(keys) - 1
        for i, key in enumerate(keys):
            query += "`"+key+"` = %s"
            if i < l:
                query += ","
            ## End if i less than 1
        ## End for keys
        query += " WHERE %s" % where

        self.__open()
        self.__session.execute("SET NAMES utf8");
        self.__session.execute(query, values)
        self.__connection.commit()

        # Obtain rows affected
        update_rows = self.__session.rowcount
        self.__close()

        return update_rows
    ## End function update

    def insert(self, table, *args, **kwargs):
        values = None
        query = "INSERT INTO %s " % table
        #print query
        if kwargs:
            keys = kwargs.keys()
            values = tuple(kwargs.values())
            query += "(" + ",".join(["`%s`"] * len(keys)) %  tuple (keys) + ") VALUES (" + ",".join(["%s"]*len(values)) + ")"
        elif args:
            values = args
            query += " VALUES(" + ",".join(["%s"]*len(values)) + ")"

        self.__open()
        self.__session.execute("SET NAMES utf8");
        self.__session.execute(query, values)
        self.__connection.commit()
        self.__close()
        return self.__session.lastrowid
    ## End def insert

    def delete(self, table, where=None, *args):
        query = "DELETE FROM %s" % table
        if where:
            query += ' WHERE %s' % where

        values = tuple(args)

        self.__open()
        self.__session.execute(query, values)
        self.__connection.commit()

        # Obtain rows affected
        delete_rows = self.__session.rowcount
        self.__close()

        return delete_rows
    ## End def delete

    def select_advanced(self, sql, *args):
        query = sql % args
        #print query
        self.__open()
        self.__session.execute(query)
        number_rows = self.__session.rowcount
        number_columns = len(self.__session.description)

        if number_rows >= 1 and number_columns > 1:
            result = [item for item in self.__session.fetchall()]
        else:
            result = [item[0] for item in self.__session.fetchall()]

        self.__close()
        return result


    def select_with_desc(self, sql, *args):
        #print args
        #print sql
        query = sql % args
        #print query
        self.__open_for_desc()
        self.__session.execute(query)
        number_rows = self.__session.rowcount
        number_columns = len(self.__session.description)

        if number_rows >= 1 and number_columns > 1:
            result = [item for item in self.__session.fetchall()]
        else:
            result = [item[0] for item in self.__session.fetchall()]

        self.__close()
        return result

    def update_advanced(self, sql, *args):
        #import sys
        #print sql,args
        query = sql % args
        self.__open()
        self.__session.execute("SET NAMES utf8");
        self.__session.execute(query)
        self.__connection.commit()

        # Obtain rows affected
        update_rows = self.__session.rowcount
        self.__close()

        return update_rows
    ## End function update

    def insert_advanced(self, sql, *args):
        query = sql % args
        #print query
        self.__open()
        self.__session.execute("SET NAMES utf8");
        self.__session.execute(query)
        self.__connection.commit()
        self.__close()
        return self.__session.lastrowid
    ## End def insert

    def delete(self,sql,*args):
        query = sql  % args
        #print query
        self.__open()
        self.__session.execute("SET NAMES utf8");
        self.__session.execute(query)
        self.__connection.commit()

        # Obtain rows affected
        delete_rows = self.__session.rowcount
        self.__close()

        return delete_rows

        
