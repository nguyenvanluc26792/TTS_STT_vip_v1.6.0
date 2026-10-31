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
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioTrack
import android.media.MediaMetadata
import android.media.session.MediaSession
import android.media.session.PlaybackState
import android.net.wifi.WifiManager
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.PowerManager
import android.util.Log
import android.view.KeyEvent
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
        var instance: ReaderMediaService? = null

        fun handleMediaAction(context: Context, action: String, intent: Intent? = null) {
            Log.i(TAG, "handleMediaAction: $action")
            when (action) {
                ACTION_PLAY -> {
                    try {
                        val am = context.getSystemService(Context.AUDIO_SERVICE) as? AudioManager
                        am?.requestAudioFocus(null, AudioManager.STREAM_MUSIC, AudioManager.AUDIOFOCUS_GAIN)
                    } catch (_: Exception) {}
                    actionListener?.onPlay()
                    instance?.updatePlaybackStateAndNotify(true)
                }
                ACTION_PAUSE -> {
                    try {
                        val am = context.getSystemService(Context.AUDIO_SERVICE) as? AudioManager
                        am?.abandonAudioFocus(null)
                    } catch (_: Exception) {}
                    actionListener?.onPause()
                    instance?.updatePlaybackStateAndNotify(false)
                }
                ACTION_PREV -> {
                    actionListener?.onPrevious()
                }
                ACTION_NEXT -> {
                    actionListener?.onNext()
                }
                ACTION_STOP -> {
                    try {
                        val am = context.getSystemService(Context.AUDIO_SERVICE) as? AudioManager
                        am?.abandonAudioFocus(null)
                    } catch (_: Exception) {}
                    actionListener?.onStop()
                    instance?.stopForegroundService()
                }
                Intent.ACTION_MEDIA_BUTTON -> {
                    val keyEvent = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        intent?.getParcelableExtra(Intent.EXTRA_KEY_EVENT, KeyEvent::class.java)
                    } else {
                        @Suppress("DEPRECATION")
                        intent?.getParcelableExtra(Intent.EXTRA_KEY_EVENT)
                    }
                    if (keyEvent != null && keyEvent.action == KeyEvent.ACTION_DOWN) {
                        when (keyEvent.keyCode) {
                            KeyEvent.KEYCODE_MEDIA_PAUSE -> handleMediaAction(context, ACTION_PAUSE)
                            KeyEvent.KEYCODE_MEDIA_PLAY -> handleMediaAction(context, ACTION_PLAY)
                            KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE, KeyEvent.KEYCODE_HEADSETHOOK -> {
                                val isCurrentlyPlaying = instance?.isPlaying ?: false
                                if (isCurrentlyPlaying) {
                                    handleMediaAction(context, ACTION_PAUSE)
                                } else {
                                    handleMediaAction(context, ACTION_PLAY)
                                }
                            }
                            KeyEvent.KEYCODE_MEDIA_NEXT -> handleMediaAction(context, ACTION_NEXT)
                            KeyEvent.KEYCODE_MEDIA_PREVIOUS -> handleMediaAction(context, ACTION_PREV)
                            KeyEvent.KEYCODE_MEDIA_STOP -> handleMediaAction(context, ACTION_STOP)
                        }
                    }
                }
            }
        }

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
    private var wifiLock: WifiManager.WifiLock? = null
    private var notificationManager: NotificationManager? = null


    private var currentTitle = "Đang đọc sách"
    private var currentArtist = "Trình Đọc Truyện AI"
    private var currentAlbum = ""
    private var isPlaying = false

    override fun onCreate() {
        super.onCreate()
        instance = this
        notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        
        createNotificationChannel()

        try {
            val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
            wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "HonorReader:MediaWakeLock")
        } catch (e: Throwable) {
            Log.w(TAG, "Không thể tạo WakeLock: ${e.message}")
        }

        try {
            val wm = applicationContext.getSystemService(Context.WIFI_SERVICE) as? WifiManager
            wifiLock = wm?.createWifiLock(WifiManager.WIFI_MODE_FULL_HIGH_PERF, "HonorReader:WifiLock")
        } catch (e: Throwable) {
            Log.w(TAG, "Không thể tạo WifiLock: ${e.message}")
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
                val mediaButtonIntent = Intent(Intent.ACTION_MEDIA_BUTTON, null, this@ReaderMediaService, MediaControlReceiver::class.java)
                val mediaButtonPendingIntent = PendingIntent.getBroadcast(
                    this@ReaderMediaService,
                    0,
                    mediaButtonIntent,
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
                )
                setMediaButtonReceiver(mediaButtonPendingIntent)
                setCallback(object : MediaSession.Callback() {
                    override fun onPlay() {
                        Log.i(TAG, "MediaSession.Callback onPlay()")
                        actionListener?.onPlay()
                        updatePlaybackStateAndNotify(true)
                    }

                    override fun onPause() {
                        Log.i(TAG, "MediaSession.Callback onPause()")
                        actionListener?.onPause()
                        updatePlaybackStateAndNotify(false)
                    }

                    override fun onSkipToNext() {
                        Log.i(TAG, "MediaSession.Callback onSkipToNext()")
                        actionListener?.onNext()
                    }

                    override fun onSkipToPrevious() {
                        Log.i(TAG, "MediaSession.Callback onSkipToPrevious()")
                        actionListener?.onPrevious()
                    }

                    override fun onStop() {
                        Log.i(TAG, "MediaSession.Callback onStop()")
                        actionListener?.onStop()
                        updatePlaybackStateAndNotify(false)
                    }

                    override fun onMediaButtonEvent(mediaButtonIntent: Intent): Boolean {
                        val keyEvent = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                            mediaButtonIntent.getParcelableExtra(Intent.EXTRA_KEY_EVENT, KeyEvent::class.java)
                        } else {
                            @Suppress("DEPRECATION")
                            mediaButtonIntent.getParcelableExtra(Intent.EXTRA_KEY_EVENT)
                        }
                        if (keyEvent != null && keyEvent.action == KeyEvent.ACTION_DOWN) {
                            when (keyEvent.keyCode) {
                                KeyEvent.KEYCODE_MEDIA_PAUSE -> {
                                    actionListener?.onPause()
                                    updatePlaybackStateAndNotify(false)
                                    return true
                                }
                                KeyEvent.KEYCODE_MEDIA_PLAY -> {
                                    actionListener?.onPlay()
                                    updatePlaybackStateAndNotify(true)
                                    return true
                                }
                                KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE, KeyEvent.KEYCODE_HEADSETHOOK -> {
                                    if (isPlaying) {
                                        actionListener?.onPause()
                                        updatePlaybackStateAndNotify(false)
                                    } else {
                                        actionListener?.onPlay()
                                        updatePlaybackStateAndNotify(true)
                                    }
                                    return true
                                }
                                KeyEvent.KEYCODE_MEDIA_NEXT -> {
                                    actionListener?.onNext()
                                    return true
                                }
                                KeyEvent.KEYCODE_MEDIA_PREVIOUS -> {
                                    actionListener?.onPrevious()
                                    return true
                                }
                                KeyEvent.KEYCODE_MEDIA_STOP -> {
                                    actionListener?.onStop()
                                    updatePlaybackStateAndNotify(false)
                                    return true
                                }
                            }
                        }
                        return super.onMediaButtonEvent(mediaButtonIntent)
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

        manageLocksAndKeepAlive(isPlaying)
        updateSessionAndNotification()
        return START_STICKY
    }

    private fun updatePlaybackStateAndNotify(playing: Boolean) {
        isPlaying = playing
        manageLocksAndKeepAlive(playing)
        updateSessionAndNotification()
    }

    private fun manageLocksAndKeepAlive(acquire: Boolean) {
        try {
            if (acquire) {
                // 1. Giữ WakeLock CPU
                if (wakeLock?.isHeld == false) {
                    wakeLock?.acquire(12 * 60 * 60 * 1000L)
                }
                // 2. Giữ WifiLock
                if (wifiLock?.isHeld == false) {
                    wifiLock?.acquire()
                }
            } else {
                if (wakeLock?.isHeld == true) {
                    wakeLock?.release()
                }
                if (wifiLock?.isHeld == true) {
                    wifiLock?.release()
                }
            }
        } catch (e: Throwable) {
            Log.w(TAG, "Lỗi quản lý Locks: ${e.message}")
        }
    }

    private fun updateSessionAndNotification() {
        try {
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

            val stateInt = if (isPlaying) PlaybackState.STATE_PLAYING else PlaybackState.STATE_PAUSED
            val playbackState = PlaybackState.Builder()
                .setState(stateInt, 0L, 1.0f)
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

        val prevIntent = PendingIntent.getBroadcast(
            this,
            1,
            Intent(this, MediaControlReceiver::class.java).apply { action = ACTION_PREV },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val pauseIntent = PendingIntent.getBroadcast(
            this,
            2,
            Intent(this, MediaControlReceiver::class.java).apply { action = ACTION_PAUSE },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val playIntent = PendingIntent.getBroadcast(
            this,
            4,
            Intent(this, MediaControlReceiver::class.java).apply { action = ACTION_PLAY },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val playPauseIntent = if (isPlaying) pauseIntent else playIntent

        val nextIntent = PendingIntent.getBroadcast(
            this,
            3,
            Intent(this, MediaControlReceiver::class.java).apply { action = ACTION_NEXT },
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
        manageLocksAndKeepAlive(false)
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
        if (instance == this) instance = null
        manageLocksAndKeepAlive(false)
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
