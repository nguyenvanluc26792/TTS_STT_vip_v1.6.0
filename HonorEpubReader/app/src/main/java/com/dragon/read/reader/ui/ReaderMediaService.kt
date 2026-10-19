package com.dragon.read.reader.ui

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.graphics.BitmapFactory
import android.media.MediaMetadata
import android.media.session.MediaSession
import android.media.session.PlaybackState
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.util.Log
import com.hihonor.dz.reader.R

class ReaderMediaService : Service() {

    companion object {
        private const val TAG = "ReaderMediaService"
        const val CHANNEL_ID = "reader_media_channel"
        const val NOTIFICATION_ID = 2026

        const val ACTION_PLAY = "com.dragon.read.action.PLAY"
        const val ACTION_PAUSE = "com.dragon.read.action.PAUSE"
        const val ACTION_PREV = "com.dragon.read.action.PREV"
        const val ACTION_NEXT = "com.dragon.read.action.NEXT"
        const val ACTION_STOP = "com.dragon.read.action.STOP"

        var actionListener: MediaActionListener? = null

        fun startOrUpdate(context: Context, title: String, artist: String, isPlaying: Boolean, album: String) {
            try {
                val intent = Intent(context, ReaderMediaService::class.java).apply {
                    putExtra("title", title)
                    putExtra("artist", artist)
                    putExtra("isPlaying", isPlaying)
                    putExtra("album", album)
                }
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    context.startForegroundService(intent)
                } else {
                    context.startService(intent)
                }
            } catch (e: Throwable) {
                Log.e(TAG, "Lỗi startOrUpdate ReaderMediaService: ${e.message}")
            }
        }

        fun stop(context: Context) {
            try {
                val intent = Intent(context, ReaderMediaService::class.java).apply {
                    action = ACTION_STOP
                }
                context.startService(intent)
            } catch (e: Throwable) {
                Log.e(TAG, "Lỗi stop ReaderMediaService: ${e.message}")
            }
        }
    }

    private var mediaSession: MediaSession? = null
    private var wakeLock: PowerManager.WakeLock? = null
    private var notificationManager: NotificationManager? = null

    private var currentTitle = "Đang đọc sách"
    private var currentArtist = "Trình Đọc Truyện AI"
    private var currentAlbum = ""
    private var isPlaying = false

    override fun onCreate() {
        super.onCreate()
        notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        createNotificationChannel()

        try {
            val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
            wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "HonorReader:MediaWakeLock")
        } catch (e: Throwable) {
            Log.w(TAG, "Không thể tạo WakeLock: ${e.message}")
        }

        initMediaSession()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Trình Đọc Truyện AI",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Điều khiển đọc sách và phát âm thanh nền"
                setShowBadge(false)
                lockscreenVisibility = Notification.VISIBILITY_PUBLIC
            }
            notificationManager?.createNotificationChannel(channel)
        }
    }

    private fun initMediaSession() {
        try {
            mediaSession = MediaSession(this, "HonorReaderMediaSession").apply {
                setFlags(MediaSession.FLAG_HANDLES_MEDIA_BUTTONS or MediaSession.FLAG_HANDLES_TRANSPORT_CONTROLS)
                setCallback(object : MediaSession.Callback() {
                    override fun onPlay() {
                        actionListener?.onPlay()
                        updatePlaybackStateAndNotify(true)
                    }

                    override fun onPause() {
                        actionListener?.onPause()
                        updatePlaybackStateAndNotify(false)
                    }

                    override fun onSkipToNext() {
                        actionListener?.onNext()
                    }

                    override fun onSkipToPrevious() {
                        actionListener?.onPrevious()
                    }

                    override fun onStop() {
                        actionListener?.onStop()
                        stopForegroundService()
                    }
                })
                isActive = true
            }
        } catch (e: Throwable) {
            Log.e(TAG, "Lỗi initMediaSession: ${e.message}")
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val action = intent?.action
        when (action) {
            ACTION_STOP -> {
                stopForegroundService()
                return START_NOT_STICKY
            }
            ACTION_PLAY -> {
                actionListener?.onPlay()
                updatePlaybackStateAndNotify(true)
                return START_STICKY
            }
            ACTION_PAUSE -> {
                actionListener?.onPause()
                updatePlaybackStateAndNotify(false)
                return START_STICKY
            }
            ACTION_PREV -> {
                actionListener?.onPrevious()
                return START_STICKY
            }
            ACTION_NEXT -> {
                actionListener?.onNext()
                return START_STICKY
            }
        }

        if (intent != null) {
            val t = intent.getStringExtra("title")
            if (!t.isNullOrEmpty()) currentTitle = t
            val a = intent.getStringExtra("artist")
            if (!a.isNullOrEmpty()) currentArtist = a
            val alb = intent.getStringExtra("album")
            if (alb != null) currentAlbum = alb
            if (intent.hasExtra("isPlaying")) {
                isPlaying = intent.getBooleanExtra("isPlaying", isPlaying)
            }
        }

        manageWakeLock(isPlaying)
        updateSessionAndNotification()
        return START_STICKY
    }

    private fun updatePlaybackStateAndNotify(playing: Boolean) {
        isPlaying = playing
        manageWakeLock(playing)
        updateSessionAndNotification()
    }

    private fun manageWakeLock(acquire: Boolean) {
        try {
            if (acquire) {
                if (wakeLock?.isHeld == false) {
                    wakeLock?.acquire(12 * 60 * 60 * 1000L) // Giữ tối đa 12 tiếng phát nền
                }
            } else {
                if (wakeLock?.isHeld == true) {
                    wakeLock?.release()
                }
            }
        } catch (e: Throwable) {
            Log.w(TAG, "Lỗi quản lý WakeLock: ${e.message}")
        }
    }

    private fun updateSessionAndNotification() {
        try {
            // 1. Cập nhật MediaMetadata cho MediaSession (hiển thị lên thanh Media Android & MagicOS)
            val metaBuilder = MediaMetadata.Builder()
                .putString(MediaMetadata.METADATA_KEY_TITLE, currentTitle)
                .putString(MediaMetadata.METADATA_KEY_ARTIST, currentArtist)
                .putString(MediaMetadata.METADATA_KEY_ALBUM, currentAlbum)

            try {
                val iconBmp = BitmapFactory.decodeResource(resources, R.mipmap.ic_launcher)
                if (iconBmp != null) {
                    metaBuilder.putBitmap(MediaMetadata.METADATA_KEY_ALBUM_ART, iconBmp)
                    metaBuilder.putBitmap(MediaMetadata.METADATA_KEY_ART, iconBmp)
                }
            } catch (e: Throwable) {}

            mediaSession?.setMetadata(metaBuilder.build())

            // 2. Cập nhật PlaybackState cho MediaSession
            val stateInt = if (isPlaying) PlaybackState.STATE_PLAYING else PlaybackState.STATE_PAUSED
            val playbackState = PlaybackState.Builder()
                .setState(stateInt, PlaybackState.PLAYBACK_POSITION_UNKNOWN, 1.0f)
                .setActions(
                    PlaybackState.ACTION_PLAY or
                    PlaybackState.ACTION_PAUSE or
                    PlaybackState.ACTION_PLAY_PAUSE or
                    PlaybackState.ACTION_SKIP_TO_NEXT or
                    PlaybackState.ACTION_SKIP_TO_PREVIOUS or
                    PlaybackState.ACTION_STOP
                )
                .build()
            mediaSession?.setPlaybackState(playbackState)

            // 3. Xây dựng Notification
            val notification = buildNotification()

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                startForeground(
                    NOTIFICATION_ID,
                    notification,
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK
                )
            } else {
                startForeground(NOTIFICATION_ID, notification)
            }
        } catch (e: Throwable) {
            Log.e(TAG, "Lỗi updateSessionAndNotification: ${e.message}")
        }
    }

    private fun buildNotification(): Notification {
        val contentIntent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, ReaderActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
            },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val prevIntent = PendingIntent.getService(
            this,
            1,
            Intent(this, ReaderMediaService::class.java).apply { action = ACTION_PREV },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val playPauseIntent = PendingIntent.getService(
            this,
            2,
            Intent(this, ReaderMediaService::class.java).apply {
                action = if (isPlaying) ACTION_PAUSE else ACTION_PLAY
            },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val nextIntent = PendingIntent.getService(
            this,
            3,
            Intent(this, ReaderMediaService::class.java).apply { action = ACTION_NEXT },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val mediaStyle = Notification.MediaStyle()
        mediaSession?.let {
            mediaStyle.setMediaSession(it.sessionToken)
        }
        mediaStyle.setShowActionsInCompactView(0, 1, 2)

        val playIcon = if (isPlaying) android.R.drawable.ic_media_pause else android.R.drawable.ic_media_play
        val playText = if (isPlaying) "Tạm dừng" else "Tiếp tục"

        val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Notification.Builder(this, CHANNEL_ID)
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this)
        }

        builder
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentTitle(currentTitle)
            .setContentText(currentArtist)
            .setSubText(if (currentAlbum.isNotEmpty()) currentAlbum else null)
            .setContentIntent(contentIntent)
            .setVisibility(Notification.VISIBILITY_PUBLIC)
            .setOngoing(isPlaying)
            .setStyle(mediaStyle)
            .addAction(android.R.drawable.ic_media_previous, "Trước", prevIntent)
            .addAction(playIcon, playText, playPauseIntent)
            .addAction(android.R.drawable.ic_media_next, "Tiếp", nextIntent)

        return builder.build()
    }

    private fun stopForegroundService() {
        manageWakeLock(false)
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                stopForeground(STOP_FOREGROUND_REMOVE)
            } else {
                @Suppress("DEPRECATION")
                stopForeground(true)
            }
        } catch (e: Throwable) {}
        stopSelf()
    }

    override fun onDestroy() {
        super.onDestroy()
        manageWakeLock(false)
        try {
            mediaSession?.isActive = false
            mediaSession?.release()
            mediaSession = null
        } catch (e: Throwable) {}
    }

    override fun onBind(intent: Intent?): IBinder? = null
}

interface MediaActionListener {
    fun onPlay()
    fun onPause()
    fun onNext()
    fun onPrevious()
    fun onStop()
}
