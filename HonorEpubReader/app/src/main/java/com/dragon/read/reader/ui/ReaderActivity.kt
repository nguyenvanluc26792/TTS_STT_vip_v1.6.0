package com.dragon.read.reader.ui

import android.annotation.SuppressLint
import android.app.AlertDialog
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.util.Log
import android.view.ActionMode
import android.view.GestureDetector
import android.view.Gravity
import android.view.KeyEvent
import android.view.Menu
import android.view.MenuItem
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.webkit.JavascriptInterface
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.EditText
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import com.dragon.read.reader.server.HonorLocalServer
import com.dz.business.reader.utils.InputManagerExHelper
import android.app.DownloadManager
import android.os.Environment
import java.io.InputStream
import java.io.OutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.util.Locale
import kotlin.concurrent.thread

class ReaderActivity : ComponentActivity() {

    private val TAG = "HonorReaderActivity"
    private val PREFS_NAME = "honor_reader_prefs"
    private val KEY_SERVER_URL = "server_url"
    private val KEY_ANIM_MODE = "anim_mode"
    private val DEFAULT_SERVER_URL = "http://127.0.0.1:8765"

    private var textToSpeech: TextToSpeech? = null
    private var isTtsReady = false

    private var localServer: HonorLocalServer? = null
    private lateinit var prefs: SharedPreferences
    private lateinit var rootLayout: FrameLayout
    private lateinit var webView: WebView
    private lateinit var progressBar: ProgressBar
    private lateinit var errorLayout: LinearLayout
    private lateinit var errorText: TextView
    private lateinit var floatingEyeBtn: TextView

    private var currentAnimMode = InputManagerExHelper.ANIM_CURL
    private var isMediaPlaying = false
    private var isEyeTrackingSuspendedByMedia = false
    private var fileUploadCallback: ValueCallback<Array<Uri>>? = null
    private var lastBackPressTime = 0L

    private val filePickerLauncher = registerForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri: Uri? ->
        if (uri != null) {
            uploadEpubToServer(uri)
        } else {
            fileUploadCallback?.onReceiveValue(null)
            fileUploadCallback = null
        }
    }

    private fun setupBackPressHandler() {
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                webView.evaluateJavascript("""
                    (function() {
                        if (document.body.classList.contains('zen-mode')) {
                            if (typeof window.exitZenMode === 'function') window.exitZenMode();
                            return 'EXITED_ZEN';
                        }
                        if (typeof nrCurrentTab !== 'undefined' && nrCurrentTab === 'reader') {
                            if (typeof switchNrTab === 'function') switchNrTab('shelf');
                            return 'SWITCHED_SHELF';
                        }
                        return 'DEFAULT';
                    })();
                """.trimIndent()) { res ->
                    val clean = res?.trim('"') ?: "DEFAULT"
                    if (clean == "DEFAULT") {
                        val now = System.currentTimeMillis()
                        if (now - lastBackPressTime < 2000) {
                            finish()
                        } else {
                            lastBackPressTime = now
                            Toast.makeText(this@ReaderActivity, "Nhấn lần nữa để thoát ứng dụng", Toast.LENGTH_SHORT).show()
                        }
                    }
                }
            }
        })
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        try {
            val defaultHandler = Thread.getDefaultUncaughtExceptionHandler()
            Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
                Log.e(TAG, "CRASH caught on thread ${thread.name}: ${throwable.message}", throwable)
                try {
                    val crashFile = java.io.File(filesDir, "crash_log.txt")
                    val sw = java.io.StringWriter()
                    val pw = java.io.PrintWriter(sw)
                    throwable.printStackTrace(pw)
                    val stackTrace = sw.toString()
                    val info = "=== CRASH AT ${java.util.Date()} ===\nThread: ${thread.name}\nException: ${throwable::class.java.name}: ${throwable.message}\n$stackTrace\n\n"
                    crashFile.appendText(info, Charsets.UTF_8)
                } catch (e: Throwable) {}

                // Nếu là thread phụ (không phải main thread), ngăn ngừa app bị đóng ngang
                if (thread.name != "main") {
                    Log.w(TAG, "Suppressed crash on background thread ${thread.name} to keep app alive!")
                    return@setDefaultUncaughtExceptionHandler
                }

                // Nếu là main thread, tự động phục hồi và khởi động lại thay vì văng ra ngoài màn hình chính
                try {
                    val intent = packageManager.getLaunchIntentForPackage(packageName)?.apply {
                        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
                    }
                    if (intent != null) {
                        startActivity(intent)
                        Runtime.getRuntime().exit(0)
                        return@setDefaultUncaughtExceptionHandler
                    }
                } catch (e: Throwable) {}

                defaultHandler?.uncaughtException(thread, throwable)
            }
        } catch (e: Throwable) {
            Log.e(TAG, "Error setting exception handler: ${e.message}")
        }

        setupBackPressHandler()

        prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        currentAnimMode = prefs.getInt(KEY_ANIM_MODE, InputManagerExHelper.ANIM_CURL)

        setupWindowCutoutAndFullscreen()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), 1001)
            }
        }
        setupMediaServiceListener()

        try {
            // Dọn sạch toàn bộ cache audio cũ (bao gồm bất kỳ file demo 242KB nào còn sót lại)
            cacheDir.listFiles()?.forEach { f ->
                if (f.name.endsWith(".mp3") || f.name.endsWith(".wav") || f.name.startsWith("tts")) {
                    f.delete()
                }
            }
        } catch (e: Exception) {
            Log.w(TAG, "Lỗi xóa cache audio: ${e.message}")
        }

        rootLayout = FrameLayout(this).apply {
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
            setBackgroundColor(0xFF121212.toInt())
        }

        webView = WebView(this).apply {
            layoutParams = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
            )
            setBackgroundColor(0xFF121212.toInt())
            isVerticalScrollBarEnabled = false
            isHorizontalScrollBarEnabled = false
        }

        progressBar = ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal).apply {
            layoutParams = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                dpToPx(3)
            ).apply {
                topMargin = 0
            }
            max = 100
            visibility = View.GONE
        }

        buildErrorLayout()
        buildFloatingEyeButton()

        rootLayout.addView(webView)
        rootLayout.addView(progressBar)
        rootLayout.addView(errorLayout)
        rootLayout.addView(floatingEyeBtn)
        setContentView(rootLayout)

        configureWebView()

        // Khởi động Local Server nội bộ trên điện thoại (độc lập không cần máy tính)
        try {
            if (localServer == null) {
                localServer = HonorLocalServer(this, 8765)
                localServer?.start()
                Log.i(TAG, "HonorLocalServer started on http://127.0.0.1:8765")
            }
        } catch (e: Exception) {
            Log.e(TAG, "HonorLocalServer start error: ${e.message}")
        }

        val serverUrl = getServerUrl()
        loadUrl(serverUrl)

        // Initial eye tracking registration (chỉ đăng ký nếu người dùng đang bật)
        if (currentAnimMode != InputManagerExHelper.ANIM_NONE) {
            InputManagerExHelper.updateSwipeupGlobalHotZoneState(this, true)
            applyEyeTrackingMode(currentAnimMode, showToast = false)
        } else {
            InputManagerExHelper.disable(this)
        }

        thread {
            try {
                val methods = InputManagerExHelper.inspectHonorMethods()
                val url = URL("${serverUrl.trimEnd('/')}/api/debug_methods")
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.doOutput = true
                conn.connectTimeout = 5000
                conn.readTimeout = 5000
                conn.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                val payload = org.json.JSONObject().apply {
                    put("device", "${Build.MANUFACTURER} ${Build.MODEL}")
                    put("sdk", Build.VERSION.SDK_INT)
                    put("methods", org.json.JSONArray(methods))
                }
                conn.outputStream.use { it.write(payload.toString().toByteArray(Charsets.UTF_8)) }
                conn.responseCode
                conn.disconnect()
            } catch (e: Exception) {
                Log.e(TAG, "Failed to send debug methods", e)
            }
        }

        initNativeTts()
    }

    private fun initNativeTts() {
        try {
            textToSpeech = TextToSpeech(this) { status ->
                if (status == TextToSpeech.SUCCESS) {
                    try {
                        val vi = Locale("vi", "VN")
                        val res = textToSpeech?.setLanguage(vi)
                        if (res == TextToSpeech.LANG_MISSING_DATA || res == TextToSpeech.LANG_NOT_SUPPORTED) {
                            textToSpeech?.setLanguage(Locale.getDefault())
                        }
                        isTtsReady = true
                        textToSpeech?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                            override fun onStart(utteranceId: String?) {
                                runOnUiThread {
                                    try {
                                        webView.evaluateJavascript("if (window.onNativeTtsStart) window.onNativeTtsStart();", null)
                                    } catch (e: Throwable) {}
                                }
                            }
                            override fun onDone(utteranceId: String?) {
                                runOnUiThread {
                                    try {
                                        webView.evaluateJavascript("if (window.onNativeTtsDone) window.onNativeTtsDone();", null)
                                    } catch (e: Throwable) {}
                                }
                            }
                            override fun onError(utteranceId: String?) {
                                runOnUiThread {
                                    try {
                                        webView.evaluateJavascript("if (window.onNativeTtsError) window.onNativeTtsError();", null)
                                    } catch (e: Throwable) {}
                                }
                            }
                            override fun onError(utteranceId: String?, errorCode: Int) {
                                onError(utteranceId)
                            }
                        })
                        Log.i(TAG, "Android Native TextToSpeech initialized successfully")
                    } catch (e: Throwable) {
                        Log.e(TAG, "Lỗi cấu hình TextToSpeech: ${e.message}")
                    }
                } else {
                    Log.w(TAG, "Android Native TextToSpeech initialization failed: status $status")
                    isTtsReady = false
                }
            }
        } catch (e: Throwable) {
            Log.e(TAG, "Lỗi khởi tạo TextToSpeech: ${e.message}")
            isTtsReady = false
        }
    }

    @Suppress("DEPRECATION")
    private fun setupWindowCutoutAndFullscreen() {
        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.statusBarColor = Color.TRANSPARENT
        window.navigationBarColor = Color.TRANSPARENT

        window.setFlags(
            WindowManager.LayoutParams.FLAG_FULLSCREEN,
            WindowManager.LayoutParams.FLAG_FULLSCREEN
        )
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            window.attributes.layoutInDisplayCutoutMode =
                WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_ALWAYS
        } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            window.attributes.layoutInDisplayCutoutMode =
                WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
        }
        applyImmersiveSticky()
    }

    @Suppress("DEPRECATION")
    private fun applyImmersiveSticky() {
        WindowCompat.setDecorFitsSystemWindows(window, false)
        val windowInsetsController = WindowCompat.getInsetsController(window, window.decorView)
        windowInsetsController.systemBarsBehavior =
            WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        windowInsetsController.hide(WindowInsetsCompat.Type.systemBars())

        val isDark = prefs.getBoolean("is_dark_theme", false)
        windowInsetsController.isAppearanceLightStatusBars = !isDark
        windowInsetsController.isAppearanceLightNavigationBars = !isDark

        window.decorView.systemUiVisibility = (
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
            or View.SYSTEM_UI_FLAG_FULLSCREEN
            or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
            or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
            or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            or View.SYSTEM_UI_FLAG_LAYOUT_STABLE
        )
    }

    private fun setupMediaServiceListener() {
        ReaderMediaService.actionListener = object : MediaActionListener {
            override fun onPlay() {
                runOnUiThread {
                    webView.evaluateJavascript("""
                        (function() {
                            if (typeof window.resumeAudio === 'function') window.resumeAudio();
                            else if (typeof window.togglePlay === 'function') window.togglePlay();
                        })();
                    """.trimIndent(), null)
                }
            }

            override fun onPause() {
                runOnUiThread {
                    webView.evaluateJavascript("""
                        (function() {
                            if (typeof window.pauseAudio === 'function') window.pauseAudio();
                        })();
                    """.trimIndent(), null)
                }
            }

            override fun onNext() {
                runOnUiThread {
                    webView.evaluateJavascript("""
                        (function() {
                            if (typeof window.nextParagraph === 'function') window.nextParagraph();
                        })();
                    """.trimIndent(), null)
                }
            }

            override fun onPrevious() {
                runOnUiThread {
                    webView.evaluateJavascript("""
                        (function() {
                            if (typeof window.prevParagraph === 'function') window.prevParagraph();
                        })();
                    """.trimIndent(), null)
                }
            }

            override fun onStop() {
                runOnUiThread {
                    webView.evaluateJavascript("""
                        (function() {
                            if (typeof window.pauseAudio === 'function') window.pauseAudio();
                        })();
                    """.trimIndent(), null)
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        applyImmersiveSticky()
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        if (currentAnimMode != InputManagerExHelper.ANIM_NONE && !isMediaPlaying) {
            InputManagerExHelper.updateSwipeupGlobalHotZoneState(this, true)
            applyEyeTrackingMode(currentAnimMode, showToast = false)
        } else if (currentAnimMode == InputManagerExHelper.ANIM_NONE) {
            InputManagerExHelper.disable(this)
        }
    }

    override fun onPause() {
        super.onPause()
    }

    override fun onDestroy() {
        super.onDestroy()
        try {
            ReaderMediaService.stop(this)
            ReaderMediaService.actionListener = null
        } catch (e: Exception) {}
        try {
            textToSpeech?.stop()
            textToSpeech?.shutdown()
            textToSpeech = null
        } catch (e: Exception) {}
        try {
            localServer?.stop()
            localServer = null
        } catch (e: Exception) {
            Log.e(TAG, "Error stopping localServer", e)
        }
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) {
            applyImmersiveSticky()
            window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            if (currentAnimMode != InputManagerExHelper.ANIM_NONE && !isMediaPlaying) {
                InputManagerExHelper.updateSwipeupGlobalHotZoneState(this, true)
                applyEyeTrackingMode(currentAnimMode, showToast = false)
            } else if (currentAnimMode == InputManagerExHelper.ANIM_NONE) {
                InputManagerExHelper.disable(this)
            }
        }
    }

    fun onMediaPlayingChanged(playing: Boolean) {
        try {
            isMediaPlaying = playing
            if (playing) {
                // Khi media bật: tạm dừng chức năng tự lật trang bằng mắt nếu đang bật
                if (currentAnimMode != InputManagerExHelper.ANIM_NONE) {
                    isEyeTrackingSuspendedByMedia = true
                    Log.i(TAG, "Media đang phát -> Tạm dừng tự lật trang bằng mắt MagicOS")
                }
            } else {
                // Khi media tắt: CHỈ bật lại NẾU người dùng đang bật MagicOS (currentAnimMode != ANIM_NONE)
                if (isEyeTrackingSuspendedByMedia && currentAnimMode != InputManagerExHelper.ANIM_NONE) {
                    isEyeTrackingSuspendedByMedia = false
                    InputManagerExHelper.notifyEbookInteractionMode(this, currentAnimMode, currentAnimMode)
                    Log.i(TAG, "Media đã dừng -> Kích hoạt lại tự lật trang bằng mắt MagicOS: $currentAnimMode")
                } else {
                    isEyeTrackingSuspendedByMedia = false
                    Log.i(TAG, "Media đã dừng -> MagicOS đang Tắt nên giữ nguyên Tắt")
                }
            }
        } catch (e: Throwable) {
            Log.e(TAG, "Lỗi onMediaPlayingChanged: ${e.message}")
        }
    }

    fun toggleEyeTracking() {
        if (currentAnimMode != InputManagerExHelper.ANIM_NONE) {
            // Đang bật -> Bấm vào 1 lần để Tắt hoàn toàn
            currentAnimMode = InputManagerExHelper.ANIM_NONE
            prefs.edit().putInt(KEY_ANIM_MODE, InputManagerExHelper.ANIM_NONE).apply()
            isEyeTrackingSuspendedByMedia = false
            InputManagerExHelper.disable(this)
            updateFloatingButtonText()
            notifyWebEyeTrackingState(false, "none")
            Toast.makeText(this, "👁️ MagicOS: Đã TẮT theo dõi mắt", Toast.LENGTH_SHORT).show()
        } else {
            // Đang tắt -> Bấm vào 1 lần để Bật (Mặc định luôn luôn là lật 3D - ANIM_CURL)
            currentAnimMode = InputManagerExHelper.ANIM_CURL
            prefs.edit().putInt(KEY_ANIM_MODE, InputManagerExHelper.ANIM_CURL).apply()
            if (isMediaPlaying) {
                isEyeTrackingSuspendedByMedia = true
                updateFloatingButtonText()
                notifyWebEyeTrackingState(true, "curl")
                Toast.makeText(this, "👁️ MagicOS: Đã BẬT lật 3D (Tạm dừng khi Media đang đọc)", Toast.LENGTH_SHORT).show()
            } else {
                isEyeTrackingSuspendedByMedia = false
                InputManagerExHelper.updateSwipeupGlobalHotZoneState(this, true)
                applyEyeTrackingMode(InputManagerExHelper.ANIM_CURL, showToast = true)
            }
        }
    }

    private fun notifyWebEyeTrackingState(enabled: Boolean, modeName: String) {
        webView.evaluateJavascript("if (window.updateEyeTrackingState) { window.updateEyeTrackingState($enabled, '$modeName'); }", null)
    }

    private fun applyEyeTrackingMode(mode: Int, showToast: Boolean = false) {
        currentAnimMode = mode
        prefs.edit().putInt(KEY_ANIM_MODE, mode).apply()

        if (mode == InputManagerExHelper.ANIM_NONE) {
            isEyeTrackingSuspendedByMedia = false
            Log.i(TAG, "MagicOS: Đã TẮT hoàn toàn cảm biến theo dõi mắt")
        } else {
            if (isMediaPlaying) {
                isEyeTrackingSuspendedByMedia = true
                Log.i(TAG, "MagicOS: Chế độ $mode đang lưu, tạm dừng do Media đang phát")
            } else {
                isEyeTrackingSuspendedByMedia = false
                InputManagerExHelper.notifyEbookInteractionMode(this, mode, mode)
                Log.i(TAG, "MagicOS: Đã kích hoạt chế độ $mode")
            }
        }
        updateFloatingButtonText()

        val isEnabled = (mode != InputManagerExHelper.ANIM_NONE)
        val modeName = when (mode) {
            InputManagerExHelper.ANIM_SLIDE -> "slide"
            InputManagerExHelper.ANIM_SCROLL -> "scroll"
            InputManagerExHelper.ANIM_CURL -> "curl"
            else -> "none"
        }
        webView.evaluateJavascript("if (window.setReaderPageMode) { window.setReaderPageMode('$modeName'); } if (window.updateEyeTrackingState) { window.updateEyeTrackingState($isEnabled, '$modeName'); }", null)

        if (showToast) {
            val msg = if (isEnabled) {
                "👁️ MagicOS: Đã BẬT lật trang 3D"
            } else {
                "👁️ MagicOS: Đã TẮT theo dõi mắt"
            }
            Toast.makeText(this, msg, Toast.LENGTH_SHORT).show()
        }
    }

    private fun buildFloatingEyeButton() {
        val shape = GradientDrawable().apply {
            shape = GradientDrawable.RECTANGLE
            cornerRadius = dpToPx(16).toFloat()
            setColor(Color.parseColor("#991F2937"))
            setStroke(dpToPx(1), Color.parseColor("#6638BDF8"))
        }

        floatingEyeBtn = TextView(this).apply {
            layoutParams = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                gravity = Gravity.BOTTOM or Gravity.END
                bottomMargin = dpToPx(16)
                rightMargin = dpToPx(16)
            }
            background = shape
            setPadding(dpToPx(10), dpToPx(5), dpToPx(10), dpToPx(5))
            visibility = View.GONE
            setOnClickListener {
                toggleEyeTracking()
            }
        }
        updateFloatingButtonText()
    }

    private fun updateFloatingButtonText() {
        val modeStr = if (currentAnimMode != InputManagerExHelper.ANIM_NONE) "Bật (3D)" else "Tắt"
        floatingEyeBtn.text = "👁️ MagicOS: $modeStr"
    }

    fun showEyeTrackingDiagnosticsDialog() {
        val diag = InputManagerExHelper.getDiagnostics(this)
        val modeItems = listOf(
            Triple(InputManagerExHelper.ANIM_SLIDE, "↔️ Chế độ Trượt Ngang (SLIDE - Mã 1)", "Chuẩn cử chỉ MagicOS: Vuốt ngang / Liếc mắt lên trên"),
            Triple(InputManagerExHelper.ANIM_SCROLL, "↕️ Chế độ Cuộn Dọc (SCROLL - Mã 2)", "Cuộn trang nối tiếp: Phù hợp đọc dạng web dọc"),
            Triple(InputManagerExHelper.ANIM_CURL, "📖 Chế độ Lật Trang 3D (CURL - Mã 3)", "Mô phỏng lật trang sách thực tế"),
            Triple(InputManagerExHelper.ANIM_NONE, "❌ Tắt Theo Dõi Mắt (Mã 0)", "Chỉ dùng chạm vuốt trên màn hình")
        )

        val scroll = android.widget.ScrollView(this).apply {
            setBackgroundColor(Color.parseColor("#0F172A"))
        }
        val container = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#0F172A"))
            setPadding(dpToPx(16), dpToPx(16), dpToPx(16), dpToPx(16))
        }

        // Card 1: Diagnostic Info
        val infoCard = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            val bg = GradientDrawable().apply {
                setColor(Color.parseColor("#1E293B"))
                cornerRadius = dpToPx(12).toFloat()
                setStroke(dpToPx(1), Color.parseColor("#334155"))
            }
            background = bg
            setPadding(dpToPx(14), dpToPx(12), dpToPx(14), dpToPx(12))
        }
        val infoTitle = TextView(this).apply {
            text = "📊 TRẠNG THÁI HỆ THỐNG MAGICOS"
            textSize = 12f
            setTypeface(null, android.graphics.Typeface.BOLD)
            setTextColor(Color.parseColor("#38BDF8"))
            setPadding(0, 0, 0, dpToPx(6))
        }
        val infoBody = TextView(this).apply {
            text = diag
            textSize = 13f
            setTextColor(Color.parseColor("#E2E8F0"))
            setLineSpacing(dpToPx(2).toFloat(), 1f)
        }
        infoCard.addView(infoTitle)
        infoCard.addView(infoBody)
        container.addView(infoCard)

        // Guide Card
        val guideCard = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            val bg = GradientDrawable().apply {
                setColor(Color.parseColor("#1E293B"))
                cornerRadius = dpToPx(12).toFloat()
                setStroke(dpToPx(1), Color.parseColor("#F59E0B"))
            }
            background = bg
            setPadding(dpToPx(14), dpToPx(12), dpToPx(14), dpToPx(12))
            val lp = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                topMargin = dpToPx(12)
            }
            layoutParams = lp
        }
        val guideTitle = TextView(this).apply {
            text = "💡 CÁCH LẬT TRANG BẰNG MẮT (向上看翻页):"
            textSize = 12f
            setTypeface(null, android.graphics.Typeface.BOLD)
            setTextColor(Color.parseColor("#FBBF24"))
            setPadding(0, 0, 0, dpToPx(4))
        }
        val guideBody = TextView(this).apply {
            text = "1. Mắt đọc dần từ trên xuống cuối màn hình.\n2. Khi đến cuối, LIẾC MẮT NHÌN LÊN ĐỈNH MÀN HÌNH (về phía camera trước / cụm đảo Dynamic Island) để máy lật trang tự động.\n3. Hãy đảm bảo trong Cài đặt Honor: [Cài đặt -> 荣耀AI&YOYO -> 眼动追踪 -> 眼动翻页] đã BẬT công tắc cho ứng dụng."
            textSize = 12.5f
            setTextColor(Color.parseColor("#CBD5E1"))
            setLineSpacing(dpToPx(2).toFloat(), 1f)
        }
        guideCard.addView(guideTitle)
        guideCard.addView(guideBody)
        container.addView(guideCard)

        // Section Title: Select Mode
        val headerText = TextView(this).apply {
            text = "👉 BẤM CHỌN KIỂU LẬT TRANG (CHẠM VÀO ĐỂ ĐỔI):"
            textSize = 12.5f
            setTypeface(null, android.graphics.Typeface.BOLD)
            setTextColor(Color.parseColor("#38BDF8"))
            setPadding(0, dpToPx(14), 0, dpToPx(8))
        }
        container.addView(headerText)

        var dialogRef: AlertDialog? = null

        // Render each mode as a styled, highly visible clickable card
        for (item in modeItems) {
            val modeCode = item.first
            val title = item.second
            val desc = item.third
            val isSelected = (currentAnimMode == modeCode)

            val modeCard = LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL
                val cardBg = GradientDrawable().apply {
                    if (isSelected) {
                        setColor(Color.parseColor("#0C4A6E")) // Sky 900
                        cornerRadius = dpToPx(10).toFloat()
                        setStroke(dpToPx(2), Color.parseColor("#38BDF8")) // Bright sky border
                    } else {
                        setColor(Color.parseColor("#1E293B")) // Slate 800
                        cornerRadius = dpToPx(10).toFloat()
                        setStroke(dpToPx(1), Color.parseColor("#334155")) // Border
                    }
                }
                background = cardBg
                setPadding(dpToPx(14), dpToPx(10), dpToPx(14), dpToPx(10))
                val lp = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply {
                    bottomMargin = dpToPx(8)
                }
                layoutParams = lp
                isClickable = true
                isFocusable = true

                val titleTv = TextView(this@ReaderActivity).apply {
                    text = if (isSelected) "$title  ✅ (ĐANG CHỌN)" else title
                    textSize = 14f
                    setTypeface(null, if (isSelected) android.graphics.Typeface.BOLD else android.graphics.Typeface.NORMAL)
                    setTextColor(if (isSelected) Color.parseColor("#38BDF8") else Color.WHITE)
                }
                val descTv = TextView(this@ReaderActivity).apply {
                    text = desc
                    textSize = 11.5f
                    setTextColor(Color.parseColor("#94A3B8"))
                    setPadding(0, dpToPx(3), 0, 0)
                }
                addView(titleTv)
                addView(descTv)

                setOnClickListener {
                    if (modeCode == InputManagerExHelper.ANIM_NONE) {
                        currentAnimMode = InputManagerExHelper.ANIM_NONE
                        prefs.edit().putInt(KEY_ANIM_MODE, InputManagerExHelper.ANIM_NONE).apply()
                        InputManagerExHelper.disable(this@ReaderActivity)
                        updateFloatingButtonText()
                        notifyWebEyeTrackingState(false, "none")
                        dialogRef?.dismiss()
                        Toast.makeText(this@ReaderActivity, "👁️ MagicOS: Đã TẮT theo dõi mắt", Toast.LENGTH_SHORT).show()
                    } else {
                        InputManagerExHelper.updateSwipeupGlobalHotZoneState(this@ReaderActivity, true)
                        applyEyeTrackingMode(modeCode, showToast = true)
                        dialogRef?.dismiss()
                    }
                }
            }
            container.addView(modeCard)
        }

        // Open Phone System Settings Button
        val settingsBtn = TextView(this).apply {
            text = "⚙️ Mở Cài Đặt Hệ Thống Điện Thoại"
            textSize = 13f
            setTypeface(null, android.graphics.Typeface.BOLD)
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
            val btnBg = GradientDrawable().apply {
                setColor(Color.parseColor("#334155"))
                cornerRadius = dpToPx(8).toFloat()
            }
            background = btnBg
            setPadding(dpToPx(12), dpToPx(10), dpToPx(12), dpToPx(10))
            val lp = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                topMargin = dpToPx(8)
                bottomMargin = dpToPx(6)
            }
            layoutParams = lp
            setOnClickListener {
                try {
                    val intent = Intent(Settings.ACTION_SETTINGS)
                    startActivity(intent)
                } catch (e: Exception) {
                    Toast.makeText(this@ReaderActivity, "Không thể mở cài đặt: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
        }

        // Accessibility Service Button for Cross-App Page Flipping
        val accessibilityBtn = TextView(this).apply {
            val isConnected = DragonBridgeAccessibilityService.instance != null
            text = if (isConnected) "✓ Đã BẬT Trợ Năng Lật Trang Cho App Khác" else "⚡ BẬT Trợ Năng Lật Trang Cho Mọi App (Kindle, PDF...)"
            textSize = 13f
            setTypeface(null, android.graphics.Typeface.BOLD)
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
            val btnBg = GradientDrawable().apply {
                setColor(if (isConnected) Color.parseColor("#10B981") else Color.parseColor("#2563EB"))
                cornerRadius = dpToPx(8).toFloat()
            }
            background = btnBg
            setPadding(dpToPx(12), dpToPx(12), dpToPx(12), dpToPx(12))
            val lp = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                topMargin = dpToPx(10)
                bottomMargin = dpToPx(6)
            }
            layoutParams = lp
            setOnClickListener {
                try {
                    val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
                    startActivity(intent)
                    Toast.makeText(this@ReaderActivity, "Tìm và BẬT 'Honor Reader VIP' để lật trang trên app khác!", Toast.LENGTH_LONG).show()
                } catch (e: Exception) {
                    Toast.makeText(this@ReaderActivity, "Lỗi mở cài đặt: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
        }
        container.addView(accessibilityBtn)

        container.addView(settingsBtn)

        scroll.addView(container)

        val builder = AlertDialog.Builder(this)
            .setTitle("👁️ Điều Khiển Mắt MagicOS (Face ID 3D)")
            .setView(scroll)
            .setPositiveButton("🌐 Đổi IP Server") { _, _ ->
                showServerUrlDialog()
            }
            .setNegativeButton("Đóng", null)

        dialogRef = builder.create()
        dialogRef.show()
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun configureWebView() {
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            mediaPlaybackRequiresUserGesture = false
            allowFileAccess = true
            allowContentAccess = true
            useWideViewPort = true
            loadWithOverviewMode = true
            cacheMode = WebSettings.LOAD_NO_CACHE
            displayZoomControls = false
            builtInZoomControls = false
            mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
        }
        webView.clearCache(true)
        webView.overScrollMode = View.OVER_SCROLL_NEVER
        webView.isVerticalScrollBarEnabled = false
        webView.isHorizontalScrollBarEnabled = false
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            webView.setOnScrollChangeListener { _, scrollX, _, _, _ ->
                if (scrollX != 0) {
                    webView.scrollTo(0, webView.scrollY)
                }
            }
        }

        // Hỗ trợ quét tay chọn chữ tự do, kéo chọn đoạn văn bản linh hoạt
        webView.isLongClickable = true
        webView.isHapticFeedbackEnabled = true

        webView.setDownloadListener { url, _, _, _, _ ->
            try {
                val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url)).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                }
                startActivity(intent)
            } catch (e: Throwable) {
                Log.e(TAG, "DownloadListener error: ${e.message}")
            }
        }

        webView.addJavascriptInterface(HonorJsBridge(), "HonorBridge")

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                val uri = request?.url ?: return false
                val urlStr = uri.toString()
                if (urlStr.endsWith(".apk", ignoreCase = true) || urlStr.contains("/download-app")) {
                    try {
                        val intent = Intent(Intent.ACTION_VIEW, uri).apply {
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        }
                        startActivity(intent)
                        return true
                    } catch (e: Throwable) {
                        Log.e(TAG, "shouldOverrideUrlLoading error: ${e.message}")
                    }
                }
                return false
            }

            override fun onRenderProcessGone(view: WebView?, detail: android.webkit.RenderProcessGoneDetail?): Boolean {
                Log.e(TAG, "WebView onRenderProcessGone! didCrash=${detail?.didCrash()}")
                runOnUiThread {
                    try {
                        rootLayout.removeView(webView)
                        webView.destroy()
                        webView = WebView(this@ReaderActivity)
                        configureWebView()
                        rootLayout.addView(webView, 0)
                        loadUrl(getServerUrl())
                    } catch (e: Throwable) {
                        Log.e(TAG, "Lỗi phục hồi WebView: ${e.message}")
                    }
                }
                return true
            }

            override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
                progressBar.visibility = View.VISIBLE
                errorLayout.visibility = View.GONE
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                progressBar.visibility = View.GONE
                injectHonorCompanionScripts()
            }

            override fun onReceivedError(
                view: WebView?,
                request: WebResourceRequest?,
                error: WebResourceError?
            ) {
                if (request?.isForMainFrame == true) {
                    progressBar.visibility = View.GONE
                    showErrorScreen(error?.description?.toString() ?: "Lỗi kết nối")
                }
            }
        }

        webView.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView?, newProgress: Int) {
                progressBar.progress = newProgress
                if (newProgress >= 100) {
                    progressBar.visibility = View.GONE
                }
            }

            override fun onShowFileChooser(
                webView: WebView?,
                filePathCallback: ValueCallback<Array<Uri>>?,
                fileChooserParams: FileChooserParams?
            ): Boolean {
                fileUploadCallback?.onReceiveValue(null)
                fileUploadCallback = filePathCallback
                filePickerLauncher.launch(arrayOf(
                    "application/epub+zip",
                    "application/pdf",
                    "application/msword",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "text/plain",
                    "text/html",
                    "application/octet-stream",
                    "*/*"
                ))
                return true
            }
        }
    }

    private fun injectHonorCompanionScripts() {
        val isEnabled = (currentAnimMode != InputManagerExHelper.ANIM_NONE)
        val initialModeName = when (currentAnimMode) {
            InputManagerExHelper.ANIM_SLIDE -> "slide"
            InputManagerExHelper.ANIM_CURL -> "curl"
            InputManagerExHelper.ANIM_SCROLL -> "scroll"
            else -> "none"
        }
        val topPx = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            window.decorView.rootWindowInsets?.displayCutout?.safeInsetTop ?: 0
        } else 0
        val density = resources.displayMetrics.density
        val topDp = if (topPx > 0) (topPx / density).toInt() else 48

        val js = """
            (function() {
                window.isHonorApp = true;
                window.honorEyeTrackingSupported = ${InputManagerExHelper.isSupported()};
                window.eyeTrackingEnabled = $isEnabled;
                document.documentElement.style.setProperty('--android-cutout-top', '${topDp}px');
                
                window.openHonorSettings = function() {
                    if (window.HonorBridge) {
                        window.HonorBridge.toggleEyeTracking();
                    }
                };

                window.notifyHonorAnimType = function(animCode) {
                    if (window.HonorBridge) {
                        window.HonorBridge.setAnimMode(animCode);
                    }
                };

                if (window.updateEyeTrackingState) {
                    window.updateEyeTrackingState($isEnabled, '$initialModeName');
                }
                if (window.setReaderPageMode) {
                    window.setReaderPageMode('$initialModeName');
                }
                
                console.log("[HonorBridge] Initialized in ReaderActivity. Cutout: " + '${topDp}px' + ", EyeTracking: " + window.honorEyeTrackingSupported + ", Mode: " + '$initialModeName');
            })();
        """.trimIndent()
        webView.evaluateJavascript(js, null)
    }

    private fun buildErrorLayout() {
        errorLayout = LinearLayout(this).apply {
            layoutParams = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
            )
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(0xFF1E1E2E.toInt())
            setPadding(dpToPx(24), dpToPx(24), dpToPx(24), dpToPx(24))
            visibility = View.GONE
        }

        val icon = TextView(this).apply {
            text = "📖"
            textSize = 54f
            gravity = Gravity.CENTER
        }

        val title = TextView(this).apply {
            text = "Honor Reader VIP"
            textSize = 22f
            setTextColor(0xFFFFFFFF.toInt())
            gravity = Gravity.CENTER
            setPadding(0, dpToPx(12), 0, dpToPx(8))
        }

        errorText = TextView(this).apply {
            text = "Không thể kết nối đến máy chủ VIP TTS.\nVui lòng kiểm tra lại địa chỉ IP máy tính."
            textSize = 14f
            setTextColor(0xFFCCCCCC.toInt())
            gravity = Gravity.CENTER
            setPadding(0, 0, 0, dpToPx(24))
        }

        val btnChangeIp = android.widget.Button(this).apply {
            text = "⚙️ Cấu Hình Máy Chủ"
            setOnClickListener { showServerUrlDialog() }
            setBackgroundColor(0xFF4F46E5.toInt())
            setTextColor(0xFFFFFFFF.toInt())
            setPadding(dpToPx(16), dpToPx(10), dpToPx(16), dpToPx(10))
        }

        val btnRetry = android.widget.Button(this).apply {
            text = "🔄 Thử Tải Lại"
            setOnClickListener { loadUrl(getServerUrl()) }
            setBackgroundColor(0xFF374151.toInt())
            setTextColor(0xFFFFFFFF.toInt())
            setPadding(dpToPx(16), dpToPx(10), dpToPx(16), dpToPx(10))
        }

        val btnDiag = android.widget.Button(this).apply {
            text = "👁️ Kiểm Tra 3D Face ID"
            setOnClickListener { showEyeTrackingDiagnosticsDialog() }
            setBackgroundColor(0xFF059669.toInt())
            setTextColor(0xFFFFFFFF.toInt())
            setPadding(dpToPx(16), dpToPx(10), dpToPx(16), dpToPx(10))
        }

        errorLayout.addView(icon)
        errorLayout.addView(title)
        errorLayout.addView(errorText)
        errorLayout.addView(btnChangeIp)
        errorLayout.addView(createSpacer(dpToPx(10)))
        errorLayout.addView(btnRetry)
        errorLayout.addView(createSpacer(dpToPx(10)))
        errorLayout.addView(btnDiag)
    }

    private fun createSpacer(heightPx: Int): View {
        return View(this).apply {
            layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, heightPx)
        }
    }

    private fun showErrorScreen(msg: String) {
        val serverUrl = getServerUrl()
        errorText.text = "Không thể tải giao diện ứng dụng:\n$serverUrl\n\nChi tiết: $msg\n\nBạn có thể thử bấm Thử Tải Lại."
        errorLayout.visibility = View.VISIBLE
    }

    private fun loadUrl(url: String) {
        var finalUrl = url.trim()
        if (!finalUrl.startsWith("http://") && !finalUrl.startsWith("https://")) {
            finalUrl = "http://$finalUrl"
        }
        val buster = "_t=${System.currentTimeMillis()}"
        finalUrl = if (finalUrl.contains("?")) "$finalUrl&$buster" else "$finalUrl?$buster"
        Log.i(TAG, "Loading URL: $finalUrl")
        webView.clearCache(true)
        webView.loadUrl(finalUrl)
    }

    private fun getServerUrl(): String {
        var saved = prefs.getString(KEY_SERVER_URL, null)
        if (saved == null || saved.contains("192.168.") || saved.contains(":5000") || saved.contains("10.0.") || saved.contains("172.")) {
            saved = DEFAULT_SERVER_URL
            prefs.edit().putString(KEY_SERVER_URL, DEFAULT_SERVER_URL).apply()
        }
        return saved
    }

    fun showServerUrlDialog() {
        val current = getServerUrl()
        val input = EditText(this).apply {
            setText(current)
            hint = "http://127.0.0.1:8765"
            setSelectAllOnFocus(true)
        }

        AlertDialog.Builder(this)
            .setTitle("Cấu Hình Máy Chủ Đọc Sách")
            .setMessage("Ứng dụng chạy máy chủ độc lập (127.0.0.1:8765) trên máy. Nếu muốn dùng máy chủ máy tính, bạn có thể nhập IP:")
            .setView(input)
            .setPositiveButton("Lưu & Kết Nối") { _, _ ->
                val newUrl = input.text.toString().trim()
                if (newUrl.isNotEmpty()) {
                    prefs.edit().putString(KEY_SERVER_URL, newUrl).apply()
                    loadUrl(newUrl)
                }
            }
            .setNegativeButton("Hủy", null)
            .setNeutralButton("Mặc Định (Độc Lập)") { _, _ ->
                prefs.edit().putString(KEY_SERVER_URL, DEFAULT_SERVER_URL).apply()
                loadUrl(DEFAULT_SERVER_URL)
            }
            .show()
    }

    @Volatile
    private var isUiOverlayActive: Boolean = false

    private var touchDownX = 0f
    private var touchDownY = 0f
    private var isSwipeTriggered = false
    private var touchDownTime = 0L

    private fun isTouchInsideFloatingButton(ev: MotionEvent): Boolean {
        if (!::floatingEyeBtn.isInitialized || floatingEyeBtn.visibility != View.VISIBLE) return false
        val loc = IntArray(2)
        floatingEyeBtn.getLocationOnScreen(loc)
        val pad = dpToPx(16)
        val x = ev.rawX.toInt()
        val y = ev.rawY.toInt()
        return x >= (loc[0] - pad) && x <= (loc[0] + floatingEyeBtn.width + pad) &&
               y >= (loc[1] - pad) && y <= (loc[1] + floatingEyeBtn.height + pad)
    }

    override fun dispatchTouchEvent(ev: MotionEvent): Boolean {
        // Ưu tiên cao nhất: Nếu chạm vào nút MagicOS thì chuyển trực tiếp cho nút xử lý mở bảng điều khiển
        if (isTouchInsideFloatingButton(ev)) {
            return super.dispatchTouchEvent(ev)
        }

        // Nếu người dùng đang mở Menu, Bảng chọn giọng, Danh sách chương, Modal thì để WebView tự do thao tác chạm/cuộn danh sách
        if (isUiOverlayActive) {
            return super.dispatchTouchEvent(ev)
        }

        val curX = if (ev.rawX != 0f) ev.rawX else ev.x
        val curY = if (ev.rawY != 0f) ev.rawY else ev.y

        // Nhận diện sự kiện bơm tự động từ cảm biến mắt MagicOS (deviceId <= 0 hoặc source không có FLAG_IS_GENERATED_GESTURE thường có tọa độ ở giữa màn hình)
        val isSyntheticEyeGesture = (ev.deviceId <= 0)

        // KHÓA LẬT TRANG Ở 1/5 KHÔNG GIAN PHÍA TRÊN MÀN HÌNH (Top Safe Zone ~ 20% chiều cao màn hình):
        // Giúp người dùng vuốt thanh thông báo hệ thống xuống hoặc bấm thao tác phía trên mà KHÔNG bị lật trang ngoài ý muốn.
        // Vùng đáy: chỉ bảo vệ khi không ở chế độ đọc tràn viền (Zen mode) và không phải cử chỉ mắt tự động của MagicOS.
        val screenHeight = resources.displayMetrics.heightPixels
        val topSafeZone = screenHeight * 0.20f
        val isTouchInSafeZone = if (isSyntheticEyeGesture) {
            false
        } else {
            (curY < topSafeZone || touchDownY < topSafeZone)
        }

        when (ev.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                touchDownX = curX
                touchDownY = curY
                touchDownTime = System.currentTimeMillis()
                isSwipeTriggered = false
            }
            MotionEvent.ACTION_MOVE -> {
                if (!isSwipeTriggered && !isTouchInSafeZone) {
                    val deltaX = curX - touchDownX
                    val deltaY = curY - touchDownY
                    val absX = kotlin.math.abs(deltaX)
                    val absY = kotlin.math.abs(deltaY)
                    val thresh = dpToPx(16)

                    // 1. Nhận diện cử chỉ vuốt ngang từ MagicOS (SLIDE / CURL) hoặc vuốt ngón tay:
                    if (absX > thresh && absX > absY * 1.15f) {
                        isSwipeTriggered = true
                        if (deltaX < 0) {
                            // Vuốt phải sang trái -> Trang kế tiếp
                            triggerNextPage()
                        } else {
                            // Vuốt trái sang phải -> Trang trước
                            triggerPreviousPage()
                        }
                        val cancel = MotionEvent.obtain(ev).apply { action = MotionEvent.ACTION_CANCEL }
                        super.dispatchTouchEvent(cancel)
                        cancel.recycle()
                        return true
                    }

                    // 2. Nếu là cử chỉ bơm tự động từ cảm biến mắt MagicOS ở chế độ SCROLL (vuốt dọc từ dưới lên)
                    if (isSyntheticEyeGesture && absY > dpToPx(24) && absY > absX * 1.2f) {
                        isSwipeTriggered = true
                        if (deltaY < 0) {
                            triggerNextPage()
                        } else {
                            triggerPreviousPage()
                        }
                        val cancel = MotionEvent.obtain(ev).apply { action = MotionEvent.ACTION_CANCEL }
                        super.dispatchTouchEvent(cancel)
                        cancel.recycle()
                        return true
                    }
                }
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                if (!isSwipeTriggered && !isTouchInSafeZone) {
                    val deltaX = curX - touchDownX
                    val deltaY = curY - touchDownY
                    val absX = kotlin.math.abs(deltaX)
                    val absY = kotlin.math.abs(deltaY)
                    val duration = System.currentTimeMillis() - touchDownTime
                    val flingThresh = dpToPx(15)

                    // Fling vuốt ngang dứt khoát
                    if (duration < 800) {
                        if (absX > flingThresh && absX > absY * 1.15f) {
                            isSwipeTriggered = true
                            if (deltaX < 0) triggerNextPage() else triggerPreviousPage()
                            val cancel = MotionEvent.obtain(ev).apply { action = MotionEvent.ACTION_CANCEL }
                            super.dispatchTouchEvent(cancel)
                            cancel.recycle()
                            return true
                        }
                        if (isSyntheticEyeGesture && absY > dpToPx(20) && absY > absX * 1.2f) {
                            isSwipeTriggered = true
                            if (deltaY < 0) triggerNextPage() else triggerPreviousPage()
                            val cancel = MotionEvent.obtain(ev).apply { action = MotionEvent.ACTION_CANCEL }
                            super.dispatchTouchEvent(cancel)
                            cancel.recycle()
                            return true
                        }
                    }
                }
                isSwipeTriggered = false
            }
        }
        return super.dispatchTouchEvent(ev)
    }

    override fun dispatchKeyEvent(event: KeyEvent): Boolean {
        if (currentAnimMode == InputManagerExHelper.ANIM_NONE) {
            return super.dispatchKeyEvent(event)
        }
        if (event.action == KeyEvent.ACTION_DOWN) {
            when (event.keyCode) {
                KeyEvent.KEYCODE_PAGE_DOWN,
                KeyEvent.KEYCODE_DPAD_DOWN,
                KeyEvent.KEYCODE_DPAD_RIGHT,
                KeyEvent.KEYCODE_SPACE,
                KeyEvent.KEYCODE_FORWARD,
                KeyEvent.KEYCODE_MEDIA_NEXT,
                261, // KEYCODE_NAVIGATE_NEXT
                KeyEvent.KEYCODE_BUTTON_R1 -> {
                    triggerNextPage()
                    return true
                }
                KeyEvent.KEYCODE_PAGE_UP,
                KeyEvent.KEYCODE_DPAD_UP,
                KeyEvent.KEYCODE_DPAD_LEFT,
                KeyEvent.KEYCODE_MEDIA_PREVIOUS,
                260, // KEYCODE_NAVIGATE_PREVIOUS
                KeyEvent.KEYCODE_BUTTON_L1 -> {
                    triggerPreviousPage()
                    return true
                }
            }
        }
        return super.dispatchKeyEvent(event)
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        if (keyCode == KeyEvent.KEYCODE_BACK) {
            onBackPressedDispatcher.onBackPressed()
            return true
        }

        if (currentAnimMode == InputManagerExHelper.ANIM_NONE) {
            return super.onKeyDown(keyCode, event)
        }

        when (keyCode) {
            KeyEvent.KEYCODE_PAGE_DOWN,
            KeyEvent.KEYCODE_DPAD_DOWN,
            KeyEvent.KEYCODE_DPAD_RIGHT,
            KeyEvent.KEYCODE_SPACE,
            KeyEvent.KEYCODE_FORWARD,
            KeyEvent.KEYCODE_MEDIA_NEXT -> {
                triggerNextPage()
                return true
            }
            KeyEvent.KEYCODE_PAGE_UP,
            KeyEvent.KEYCODE_DPAD_UP,
            KeyEvent.KEYCODE_DPAD_LEFT,
            KeyEvent.KEYCODE_MEDIA_PREVIOUS -> {
                triggerPreviousPage()
                return true
            }
        }
        return super.onKeyDown(keyCode, event)
    }

    override fun dispatchGenericMotionEvent(event: MotionEvent): Boolean {
        if (currentAnimMode == InputManagerExHelper.ANIM_NONE) {
            return super.dispatchGenericMotionEvent(event)
        }
        if (event.action == MotionEvent.ACTION_SCROLL) {
            val vScroll = event.getAxisValue(MotionEvent.AXIS_VSCROLL)
            val hScroll = event.getAxisValue(MotionEvent.AXIS_HSCROLL)
            if (vScroll < -0.1f || hScroll < -0.1f) {
                triggerNextPage()
                return true
            } else if (vScroll > 0.1f || hScroll > 0.1f) {
                triggerPreviousPage()
                return true
            }
        }
        return super.dispatchGenericMotionEvent(event)
    }

    override fun onKeyUp(keyCode: Int, event: KeyEvent?): Boolean {
        when (keyCode) {
            KeyEvent.KEYCODE_PAGE_UP,
            KeyEvent.KEYCODE_PAGE_DOWN -> return true
        }
        return super.onKeyUp(keyCode, event)
    }

    override fun onActionModeStarted(mode: ActionMode?) {
        mode?.finish()
        super.onActionModeStarted(mode)
    }

    private fun triggerNextPage(fromUser: Boolean = true) {
        if (!fromUser && isMediaPlaying) {
            Log.i(TAG, "isMediaPlaying = true -> Bỏ qua triggerNextPage tự lật trang")
            return
        }
        if (!fromUser && currentAnimMode == InputManagerExHelper.ANIM_NONE) {
            Log.i(TAG, "currentAnimMode == ANIM_NONE -> Bỏ qua triggerNextPage vì MagicOS đã tắt")
            return
        }

        // Lật trang nội bộ trong WebView (Reset cờ isTouchStartedInTopSafeZone trước khi gọi để tránh bị kẹt)
        val js = """
            (function() {
                window.isTouchStartedInTopSafeZone = false;
                if (typeof nrCurrentTab !== 'undefined' && nrCurrentTab !== 'reader' && window.bookData) {
                    if (typeof switchNrTab === 'function') switchNrTab('reader');
                }
                const sc = document.getElementById('readerScrollArea') || document.querySelector('main');
                if (sc) sc.scrollLeft = 0;
                if (typeof window.nextPage === 'function') {
                    window.nextPage(true);
                } else if (typeof window.safeTurnNextPage === 'function') {
                    window.safeTurnNextPage(true);
                } else if (sc) {
                    sc.scrollBy({ top: window.innerHeight * 0.85, behavior: 'smooth' });
                }
                if (sc) sc.scrollLeft = 0;
            })();
        """.trimIndent()
        webView.evaluateJavascript(js, null)
    }

    private fun triggerPreviousPage(fromUser: Boolean = true) {
        if (!fromUser && isMediaPlaying) {
            Log.i(TAG, "isMediaPlaying = true -> Bỏ qua triggerPreviousPage tự lật trang")
            return
        }
        if (!fromUser && currentAnimMode == InputManagerExHelper.ANIM_NONE) {
            Log.i(TAG, "currentAnimMode == ANIM_NONE -> Bỏ qua triggerPreviousPage vì MagicOS đã tắt")
            return
        }

        // Lùi trang nội bộ trong WebView
        val js = """
            (function() {
                window.isTouchStartedInTopSafeZone = false;
                if (typeof nrCurrentTab !== 'undefined' && nrCurrentTab !== 'reader' && window.bookData) {
                    if (typeof switchNrTab === 'function') switchNrTab('reader');
                }
                const sc = document.getElementById('readerScrollArea') || document.querySelector('main');
                if (sc) sc.scrollLeft = 0;
                if (typeof window.prevPage === 'function') {
                    window.prevPage(true);
                } else if (typeof window.safeTurnPrevPage === 'function') {
                    window.safeTurnPrevPage(true);
                } else if (sc) {
                    sc.scrollBy({ top: -window.innerHeight * 0.85, behavior: 'smooth' });
                }
                if (sc) sc.scrollLeft = 0;
            })();
        """.trimIndent()
        webView.evaluateJavascript(js, null)
    }

    private fun uploadEpubToServer(fileUri: Uri) {
        Toast.makeText(this, "Đang tải sách / tài liệu lên máy chủ...", Toast.LENGTH_SHORT).show()
        val serverUrl = getServerUrl().trimEnd('/')
        val uploadUrl = "$serverUrl/api/upload"

        thread {
            try {
                val inputStream: InputStream? = contentResolver.openInputStream(fileUri)
                if (inputStream == null) {
                    runOnUiThread { Toast.makeText(this, "Không thể đọc tệp!", Toast.LENGTH_SHORT).show() }
                    return@thread
                }

                val fileName = getFileName(fileUri) ?: "book_${System.currentTimeMillis()}.epub"
                val boundary = "==Boundary_${System.currentTimeMillis()}=="
                val url = URL(uploadUrl)
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.doOutput = true
                conn.connectTimeout = 30000
                conn.readTimeout = 60000
                conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=$boundary")

                val outputStream: OutputStream = conn.outputStream
                outputStream.write("--$boundary\r\n".toByteArray())
                outputStream.write("Content-Disposition: form-data; name=\"file\"; filename=\"$fileName\"\r\n".toByteArray())
                val mimeType = contentResolver.getType(fileUri) ?: "application/octet-stream"
                outputStream.write("Content-Type: $mimeType\r\n\r\n".toByteArray())

                val buffer = ByteArray(8192)
                var bytesRead: Int
                while (inputStream.read(buffer).also { bytesRead = it } != -1) {
                    outputStream.write(buffer, 0, bytesRead)
                }
                outputStream.write("\r\n--$boundary--\r\n".toByteArray())
                outputStream.flush()
                outputStream.close()
                inputStream.close()

                val responseCode = conn.responseCode
                if (responseCode in 200..299) {
                    runOnUiThread {
                        Toast.makeText(this, "Nạp sách thành công! Đang mở sách...", Toast.LENGTH_SHORT).show()
                        loadUrl(serverUrl)
                    }
                } else {
                    runOnUiThread {
                        Toast.makeText(this, "Tải lên thất bại (Mã lỗi $responseCode)", Toast.LENGTH_LONG).show()
                    }
                }
                conn.disconnect()
            } catch (e: Exception) {
                Log.e(TAG, "Lỗi upload sách", e)
                runOnUiThread {
                    Toast.makeText(this, "Lỗi upload: ${e.message}", Toast.LENGTH_LONG).show()
                }
            } finally {
                fileUploadCallback?.onReceiveValue(null)
                fileUploadCallback = null
            }
        }
    }

    private fun getFileName(uri: Uri): String? {
        var name: String? = null
        val cursor = contentResolver.query(uri, null, null, null, null)
        cursor?.use {
            if (it.moveToFirst()) {
                val index = it.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
                if (index != -1) {
                    name = it.getString(index)
                }
            }
        }
        return name
    }

    private fun dpToPx(dp: Int): Int {
        return (dp * resources.displayMetrics.density).toInt()
    }

    inner class HonorJsBridge {
        @JavascriptInterface
        fun isHonorSupported(): Boolean {
            return InputManagerExHelper.isSupported()
        }

        @JavascriptInterface
        fun setAnimMode(mode: Int) {
            runOnUiThread {
                if (mode == InputManagerExHelper.ANIM_NONE) {
                    currentAnimMode = InputManagerExHelper.ANIM_NONE
                    prefs.edit().putInt(KEY_ANIM_MODE, InputManagerExHelper.ANIM_NONE).apply()
                    isEyeTrackingSuspendedByMedia = false
                    InputManagerExHelper.disable(this@ReaderActivity)
                    updateFloatingButtonText()
                    notifyWebEyeTrackingState(false, "none")
                    Toast.makeText(this@ReaderActivity, "👁️ MagicOS: Đã TẮT theo dõi mắt", Toast.LENGTH_SHORT).show()
                } else {
                    InputManagerExHelper.updateSwipeupGlobalHotZoneState(this@ReaderActivity, true)
                    applyEyeTrackingMode(mode, showToast = false)
                }
            }
        }

        @JavascriptInterface
        fun toggleEyeTracking() {
            runOnUiThread {
                this@ReaderActivity.toggleEyeTracking()
            }
        }

        @JavascriptInterface
        fun setMediaPlaying(isPlaying: Boolean) {
            try {
                runOnUiThread {
                    this@ReaderActivity.onMediaPlayingChanged(isPlaying)
                }
            } catch (e: Throwable) {
                Log.e(TAG, "Error in setMediaPlaying: ${e.message}")
            }
        }

        @JavascriptInterface
        fun updateMediaSession(title: String, artist: String, isPlaying: Boolean, album: String) {
            try {
                runOnUiThread {
                    localServer?.isAudioPlaying = isPlaying
                    this@ReaderActivity.onMediaPlayingChanged(isPlaying)
                    ReaderMediaService.startOrUpdate(
                        this@ReaderActivity,
                        title = title,
                        artist = artist,
                        isPlaying = isPlaying,
                        album = album
                    )
                }
            } catch (e: Throwable) {
                Log.e(TAG, "Error in updateMediaSession: ${e.message}")
            }
        }

        @JavascriptInterface
        fun stopMediaService() {
            try {
                runOnUiThread {
                    localServer?.isAudioPlaying = false
                    this@ReaderActivity.onMediaPlayingChanged(false)
                    if (localServer?.preloader?.isWorking != true) {
                        ReaderMediaService.stop(this@ReaderActivity)
                    }
                }
            } catch (e: Throwable) {
                Log.e(TAG, "Error in stopMediaService: ${e.message}")
            }
        }

        @JavascriptInterface
        fun openDiagnostics() {
            runOnUiThread {
                this@ReaderActivity.showEyeTrackingDiagnosticsDialog()
            }
        }

        @JavascriptInterface
        fun pickEpubFile() {
            runOnUiThread {
                filePickerLauncher.launch(arrayOf(
                    "application/epub+zip",
                    "application/pdf",
                    "application/msword",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "text/plain",
                    "text/html",
                    "application/octet-stream",
                    "*/*"
                ))
            }
        }

        @JavascriptInterface
        fun setUiOverlayActive(active: Boolean) {
            isUiOverlayActive = active
        }

        @JavascriptInterface
        fun setAppTheme(theme: String) {
            runOnUiThread {
                val isDark = (theme == "dark")
                prefs.edit().putBoolean("is_dark_theme", isDark).apply()
                val windowInsetsController = WindowCompat.getInsetsController(window, window.decorView)
                windowInsetsController.isAppearanceLightStatusBars = !isDark
                windowInsetsController.isAppearanceLightNavigationBars = !isDark
            }
        }

        @JavascriptInterface
        fun reloadApp() {
            runOnUiThread {
                loadUrl(getServerUrl())
            }
        }

        @JavascriptInterface
        fun getBatteryLevel(): Int {
            return try {
                val bm = getSystemService(Context.BATTERY_SERVICE) as? android.os.BatteryManager
                bm?.getIntProperty(android.os.BatteryManager.BATTERY_PROPERTY_CAPACITY) ?: -1
            } catch (e: Throwable) {
                -1
            }
        }

        @JavascriptInterface
        fun isNativeTtsAvailable(): Boolean {
            return isTtsReady && textToSpeech != null
        }

        @JavascriptInterface
        fun speakNative(text: String, speed: Float): Boolean {
            if (!isTtsReady || textToSpeech == null) return false
            try {
                runOnUiThread {
                    try {
                        textToSpeech?.setPitch(1.0f)
                        textToSpeech?.setSpeechRate(if (speed in 0.5f..2.5f) speed else 1.0f)
                        val uttId = "reader_utt_${System.currentTimeMillis()}"
                        val params = android.os.Bundle().apply {
                            putString(TextToSpeech.Engine.KEY_PARAM_UTTERANCE_ID, uttId)
                        }
                        val res = textToSpeech?.speak(text, TextToSpeech.QUEUE_FLUSH, params, uttId)
                        if (res != TextToSpeech.SUCCESS) {
                            Log.w(TAG, "textToSpeech.speak error code: $res")
                            runOnUiThread {
                                try {
                                    webView.evaluateJavascript("if (window.onNativeTtsError) window.onNativeTtsError();", null)
                                } catch (e: Throwable) {}
                            }
                        }
                    } catch (e: Throwable) {
                        Log.e(TAG, "Lỗi speakNative: ${e.message}")
                        runOnUiThread {
                            try {
                                webView.evaluateJavascript("if (window.onNativeTtsError) window.onNativeTtsError();", null)
                            } catch (err: Throwable) {}
                        }
                    }
                }
                return true
            } catch (e: Throwable) {
                Log.e(TAG, "Error in speakNative bridge: ${e.message}")
                return false
            }
        }

        @JavascriptInterface
        fun speakNativeWithPitch(text: String, speed: Float, pitch: Float): Boolean {
            if (!isTtsReady || textToSpeech == null) return false
            try {
                runOnUiThread {
                    try {
                        textToSpeech?.setSpeechRate(if (speed in 0.5f..2.5f) speed else 1.0f)
                        textToSpeech?.setPitch(if (pitch in 0.5f..2.0f) pitch else 1.0f)
                        val uttId = "reader_utt_${System.currentTimeMillis()}"
                        val params = android.os.Bundle().apply {
                            putString(TextToSpeech.Engine.KEY_PARAM_UTTERANCE_ID, uttId)
                        }
                        val res = textToSpeech?.speak(text, TextToSpeech.QUEUE_FLUSH, params, uttId)
                        if (res != TextToSpeech.SUCCESS) {
                            Log.w(TAG, "textToSpeech.speak error code: $res")
                            runOnUiThread {
                                try {
                                    webView.evaluateJavascript("if (window.onNativeTtsError) window.onNativeTtsError();", null)
                                } catch (e: Throwable) {}
                            }
                        }
                    } catch (e: Throwable) {
                        Log.e(TAG, "Lỗi speakNativeWithPitch: ${e.message}")
                        runOnUiThread {
                            try {
                                webView.evaluateJavascript("if (window.onNativeTtsError) window.onNativeTtsError();", null)
                            } catch (err: Throwable) {}
                        }
                    }
                }
                return true
            } catch (e: Throwable) {
                Log.e(TAG, "Error in speakNativeWithPitch bridge: ${e.message}")
                return false
            }
        }

        @JavascriptInterface
        fun stopNativeSpeak() {
            runOnUiThread {
                try {
                    textToSpeech?.stop()
                } catch (e: Exception) {}
            }
        }

        @JavascriptInterface
        fun copyToClipboard(text: String) {
            runOnUiThread {
                try {
                    val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as? ClipboardManager
                    val clip = ClipData.newPlainText("Copied Text", text)
                    clipboard?.setPrimaryClip(clip)
                    Toast.makeText(this@ReaderActivity, "📋 Đã sao chép vào bộ nhớ tạm", Toast.LENGTH_SHORT).show()
                } catch (e: Throwable) {
                    Log.e(TAG, "Error copyToClipboard: ${e.message}")
                }
            }
        }

        @JavascriptInterface
        fun downloadApk(url: String) {
            runOnUiThread {
                try {
                    val safeUrl = url.trim()
                    Log.i(TAG, "HonorJsBridge.downloadApk called with: $safeUrl")

                    // 1. Dùng Android DownloadManager tải trực tiếp file về thư mục Downloads của máy
                    try {
                        val uri = Uri.parse(safeUrl)
                        val request = DownloadManager.Request(uri).apply {
                            setTitle("Honor Reader v1.6.45")
                            setDescription("Đang tải tệp cài đặt LReader.apk...")
                            setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                            setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, "LReader.apk")
                            setMimeType("application/vnd.android.package-archive")
                        }
                        val dm = getSystemService(Context.DOWNLOAD_SERVICE) as? DownloadManager
                        dm?.enqueue(request)
                        Toast.makeText(this@ReaderActivity, "📥 Đang tải APK về máy...", Toast.LENGTH_SHORT).show()
                    } catch (dmErr: Throwable) {
                        Log.w(TAG, "DownloadManager enqueue error: ${dmErr.message}")
                    }

                    // 2. Mở trình duyệt mặc định tải trực tiếp để đảm bảo 100% người dùng có file ngay
                    val browserIntent = Intent(Intent.ACTION_VIEW, Uri.parse(safeUrl)).apply {
                        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    }
                    startActivity(browserIntent)
                } catch (e: Throwable) {
                    Log.e(TAG, "Lỗi mở liên kết tải APK: ${e.message}")
                    Toast.makeText(this@ReaderActivity, "Lỗi mở tải: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }
}
