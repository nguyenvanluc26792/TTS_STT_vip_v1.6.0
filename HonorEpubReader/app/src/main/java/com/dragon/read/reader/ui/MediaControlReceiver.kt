package com.dragon.read.reader.ui

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

class MediaControlReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action ?: return
        Log.i("MediaControlReceiver", "BroadcastReceiver onReceive: $action")
        ReaderMediaService.handleMediaAction(context, action, intent)
    }
}
