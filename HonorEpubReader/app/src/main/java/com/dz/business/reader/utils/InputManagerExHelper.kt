package com.dz.business.reader.utils

import android.content.Context
import android.os.Build
import android.util.Log

object InputManagerExHelper {
    private const val TAG = "InputManagerExHelper"
    private const val HONOR_CLASS = "com.hihonor.android.hardware.input.InputManagerEx"
    private const val HONOR_METHOD = "notifyEbookInteractionMode"

    const val ANIM_NONE = 0
    const val ANIM_SLIDE = 1
    const val ANIM_SCROLL = 2
    const val ANIM_CURL = 3

    var lastStatusMessage: String = "Chưa khởi tạo"
        private set

    fun isSupported(): Boolean {
        return try {
            val clazz = Class.forName(HONOR_CLASS)
            clazz.getMethod(
                HONOR_METHOD,
                Context::class.java,
                Int::class.javaPrimitiveType,
                Int::class.javaPrimitiveType
            )
            true
        } catch (e: Throwable) {
            false
        }
    }

    fun notifyEbookInteractionMode(context: Context, normalAnimType: Int, extAnimType: Int = normalAnimType): Boolean {
        return try {
            val clazz = Class.forName(HONOR_CLASS)
            val method = clazz.getMethod(
                HONOR_METHOD,
                Context::class.java,
                Int::class.javaPrimitiveType,
                Int::class.javaPrimitiveType
            )
            try {
                method.invoke(null, context, normalAnimType, extAnimType)
            } catch (e: Exception) {
                val appContext = context.applicationContext ?: context
                method.invoke(null, appContext, normalAnimType, extAnimType)
            }
            val modeStr = when (normalAnimType) {
                1 -> "SLIDE (Trượt ngang)"
                2 -> "SCROLL (Cuộn dọc)"
                3 -> "CURL (Lật trang 3D)"
                0 -> "TẮT (Mã 0)"
                else -> "Mã $normalAnimType"
            }
            lastStatusMessage = "MagicOS: $modeStr"
            Log.i(TAG, "notifyEbookInteractionMode success: $modeStr (Mã: $normalAnimType)")
            true
        } catch (e: Exception) {
            lastStatusMessage = "notifyEbookInteractionMode error: ${e.message}"
            Log.e(TAG, lastStatusMessage, e)
            false
        }
    }

    fun updateSwipeupGlobalHotZoneState(context: Context, state: Boolean): Boolean {
        return try {
            val clazz = Class.forName(HONOR_CLASS)
            val method = clazz.getMethod(
                "updateSwipeupGlobalHotZoneState",
                Context::class.java,
                Boolean::class.javaPrimitiveType
            )
            val res = method.invoke(null, context, state) as? Boolean ?: true
            Log.i(TAG, "updateSwipeupGlobalHotZoneState($state): $res")
            res
        } catch (e: Exception) {
            Log.e(TAG, "updateSwipeupGlobalHotZoneState error: ${e.message}")
            false
        }
    }

    fun disable(context: Context) {
        lastStatusMessage = "MagicOS: Đã tắt theo dõi mắt"
        // 1. Tắt chế độ tương tác E-book bằng mã 0 chuẩn
        try {
            notifyEbookInteractionMode(context, 0, 0)
        } catch (e: Exception) {
            Log.e(TAG, "Lỗi notifyEbookInteractionMode(0, 0): ${e.message}")
        }

        // 2. Vô hiệu hóa vùng nhận diện cử chỉ lướt mắt / nhìn lên trên đỉnh màn hình
        try {
            updateSwipeupGlobalHotZoneState(context, false)
        } catch (e: Exception) {
            Log.e(TAG, "Lỗi updateSwipeupGlobalHotZoneState(false): ${e.message}")
        }
        Log.i(TAG, "MagicOS disable: đã gửi notifyEbookInteractionMode(0, 0) và updateSwipeupGlobalHotZoneState(false)")
    }

    fun inspectHonorMethods(): List<String> {
        val result = mutableListOf<String>()
        try {
            val clazz = Class.forName(HONOR_CLASS)
            for (m in clazz.methods) {
                val params = m.parameterTypes.joinToString(",") { it.simpleName }
                result.add("${m.name}($params):${m.returnType.simpleName}")
            }

            // Inspect declared fields & service instances
            for (f in clazz.declaredFields) {
                f.isAccessible = true
                val fType = f.type.name
                val fVal = try { f.get(null) } catch (e: Exception) { null }
                result.add("FIELD:${f.name}:$fType=${if (fVal != null) fVal.javaClass.name else "null"}")
                if (fVal != null) {
                    for (sm in fVal.javaClass.methods) {
                        val smParams = sm.parameterTypes.joinToString(",") { it.simpleName }
                        result.add("SERVICE_METHOD:${f.name}:${sm.name}($smParams):${sm.returnType.simpleName}")
                    }
                }
            }
        } catch (e: Exception) {
            result.add("Error: ${e.message}")
        }
        return result
    }

    fun getDiagnostics(context: Context): String {
        val supported = isSupported()
        val pkg = context.packageName
        val model = "${Build.MANUFACTURER} ${Build.MODEL}"
        return "📱 Thiết bị: $model\n📦 Package: $pkg\n📖 Activity: com.dragon.read.reader.ui.ReaderActivity\n⚙️ API InputManagerEx: ${if (supported) "Có sẵn trong MagicOS ✅" else "Không tìm thấy ❌"}\n📊 Kích hoạt: $lastStatusMessage"
    }
}
