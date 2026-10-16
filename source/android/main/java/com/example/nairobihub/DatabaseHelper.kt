package com.example.nairobihub

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import org.json.JSONObject
import java.util.UUID

class DatabaseHelper(context: Context) : SQLiteOpenHelper(context, DATABASE_NAME, null, DATABASE_VERSION) {

    companion object {
        private const val DATABASE_NAME = "client_servers.db"
        private const val DATABASE_VERSION = 2
    }

    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL("""
            CREATE TABLE IF NOT EXISTS connected_servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_name TEXT UNIQUE NOT NULL,
                url TEXT NOT NULL,
                server_key TEXT,
                session_token TEXT
            )
        """)
        db.execSQL("""
            CREATE TABLE IF NOT EXISTS client_config (
                client_id TEXT PRIMARY KEY,
                username TEXT,
                dob TEXT DEFAULT '2000-01-01'
            )
        """)
        db.execSQL("""
            CREATE TABLE IF NOT EXISTS app_settings (
                "key" TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        db.execSQL("""
            CREATE TABLE IF NOT EXISTS favorite_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_name TEXT NOT NULL,
                link_id INTEGER NOT NULL,
                title TEXT,
                url TEXT,
                item_type TEXT,
                UNIQUE(server_name, link_id)
            )
        """)
        db.execSQL("""
            CREATE TABLE IF NOT EXISTS offline_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_name TEXT NOT NULL,
                link_id INTEGER NOT NULL,
                title TEXT,
                url TEXT,
                item_type TEXT,
                is_public INTEGER,
                username TEXT,
                UNIQUE(server_name, link_id)
            )
        """)

        val cursor = db.rawQuery("SELECT client_id FROM client_config", null)
        if (!cursor.moveToFirst()) {
            val cId = "user_" + UUID.randomUUID().toString().take(8)
            val values = ContentValues().apply {
                put("client_id", cId)
                put("username", "User_${cId.takeLast(5)}")
                put("dob", "2000-01-01")
            }
            db.insert("client_config", null, values)
        }
        cursor.close()
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        db.execSQL("DROP TABLE IF EXISTS connected_servers")
        db.execSQL("DROP TABLE IF EXISTS client_config")
        db.execSQL("DROP TABLE IF EXISTS app_settings")
        db.execSQL("DROP TABLE IF EXISTS favorite_resources")
        db.execSQL("DROP TABLE IF EXISTS offline_resources")
        onCreate(db)
    }

    fun getClientInfo(): Triple<String, String, String> {
        val db = readableDatabase
        val cursor = db.rawQuery("SELECT client_id, username, dob FROM client_config", null)
        var clientId = "user_default"
        var username = "User_Default"
        var dob = "2000-01-01"
        if (cursor.moveToFirst()) {
            clientId = cursor.getString(0) ?: clientId
            username = cursor.getString(1) ?: username
            dob = cursor.getString(2) ?: dob
        }
        cursor.close()
        return Triple(clientId, username, dob)
    }

    fun updateClientProfile(newUsername: String, newDob: String) {
        val db = writableDatabase
        val values = ContentValues().apply {
            put("username", newUsername)
            put("dob", newDob)
        }
        val clientId = getClientInfo().first
        db.update("client_config", values, "client_id = ?", arrayOf(clientId))
    }

    fun saveSetting(key: String, value: String) {
        val db = writableDatabase
        val values = ContentValues().apply {
            put("key", key)
            put("value", value)
        }
        db.insertWithOnConflict("app_settings", null, values, SQLiteDatabase.CONFLICT_REPLACE)
    }

    fun getSetting(key: String, defaultVal: String): String {
        val db = readableDatabase
        val cursor = db.rawQuery("SELECT value FROM app_settings WHERE \"key\" = ?", arrayOf(key))
        var res = defaultVal
        if (cursor.moveToFirst()) {
            res = cursor.getString(0) ?: defaultVal
        }
        cursor.close()
        return res
    }

    fun resetAllSettings() {
        val db = writableDatabase
        db.execSQL("DELETE FROM app_settings")
    }

    fun getConnectedServers(): List<Map<String, String>> {
        val db = readableDatabase
        val cursor = db.rawQuery("SELECT server_name, url, server_key, session_token FROM connected_servers", null)
        val list = mutableListOf<Map<String, String>>()
        while (cursor.moveToNext()) {
            list.add(mapOf(
                "server_name" to (cursor.getString(0) ?: ""),
                "url" to (cursor.getString(1) ?: ""),
                "server_key" to (cursor.getString(2) ?: ""),
                "session_token" to (cursor.getString(3) ?: "")
            ))
        }
        cursor.close()
        return list
    }

    fun addConnectedServer(name: String, url: String, key: String, token: String) {
        val db = writableDatabase
        val values = ContentValues().apply {
            put("server_name", name)
            put("url", url)
            put("server_key", key)
            put("session_token", token)
        }
        db.insertWithOnConflict("connected_servers", null, values, SQLiteDatabase.CONFLICT_REPLACE)
    }

    fun removeConnectedServer(name: String) {
        val db = writableDatabase
        db.delete("connected_servers", "server_name = ?", arrayOf(name))
    }

    fun clearCache() {
        val db = writableDatabase
        db.delete("offline_resources", null, null)
        db.delete("favorite_resources", null, null)
    }

    fun addOfflineResource(file: JSONObject) {
        val db = writableDatabase
        val values = ContentValues().apply {
            put("server_name", file.optString("origin_server", "unknown"))
            put("link_id", file.optInt("id", 0))
            put("title", file.optString("title", ""))
            put("url", file.optString("url", ""))
            put("item_type", file.optString("item_type", "folder"))
            put("is_public", if (file.optBoolean("is_public", true)) 1 else 0)
            put("username", file.optString("username", ""))
        }
        db.insertWithOnConflict("offline_resources", null, values, SQLiteDatabase.CONFLICT_REPLACE)
    }

    fun getOfflineResources(): List<Map<String, Any>> {
        val db = readableDatabase
        val cursor = db.rawQuery("SELECT server_name, link_id, title, url, item_type, is_public, username FROM offline_resources", null)
        val list = mutableListOf<Map<String, Any>>()
        while (cursor.moveToNext()) {
            list.add(mapOf(
                "origin_server" to (cursor.getString(0) ?: ""),
                "id" to cursor.getInt(1),
                "title" to (cursor.getString(2) ?: ""),
                "url" to (cursor.getString(3) ?: ""),
                "item_type" to (cursor.getString(4) ?: "folder"),
                "is_public" to (cursor.getInt(5) == 1),
                "username" to (cursor.getString(6) ?: "")
            ))
        }
        cursor.close()
        return list
    }

    fun removeOfflineResource(serverName: String, linkId: Int) {
        val db = writableDatabase
        db.delete("offline_resources", "server_name = ? AND link_id = ?", arrayOf(serverName, linkId.toString()))
    }

    fun addFavoriteResource(serverName: String, linkId: Int, title: String, url: String, itemType: String) {
        val db = writableDatabase
        val values = ContentValues().apply {
            put("server_name", serverName)
            put("link_id", linkId)
            put("title", title)
            put("url", url)
            put("item_type", itemType)
        }
        db.insertWithOnConflict("favorite_resources", null, values, SQLiteDatabase.CONFLICT_REPLACE)
    }

    fun removeFavoriteResource(serverName: String, linkId: Int) {
        val db = writableDatabase
        db.delete("favorite_resources", "server_name = ? AND link_id = ?", arrayOf(serverName, linkId.toString()))
    }

    fun getFavoriteResources(): List<Map<String, Any>> {
        val db = readableDatabase
        val cursor = db.rawQuery("SELECT server_name, link_id, title, url, item_type FROM favorite_resources", null)
        val list = mutableListOf<Map<String, Any>>()
        while (cursor.moveToNext()) {
            list.add(mapOf(
                "server_name" to (cursor.getString(0) ?: ""),
                "link_id" to cursor.getInt(1),
                "title" to (cursor.getString(2) ?: ""),
                "url" to (cursor.getString(3) ?: ""),
                "item_type" to (cursor.getString(4) ?: "folder")
            ))
        }
        cursor.close()
        return list
    }
}