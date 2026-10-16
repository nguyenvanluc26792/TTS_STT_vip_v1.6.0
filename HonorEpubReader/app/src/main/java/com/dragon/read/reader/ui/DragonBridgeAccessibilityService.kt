package com.dragon.read.reader.ui

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.graphics.Path
import android.util.DisplayMetrics
import android.util.Log
import android.view.accessibility.AccessibilityEvent

class DragonBridgeAccessibilityService : AccessibilityService() {

    companion object {
        var instance: DragonBridgeAccessibilityService? = null
        private const val TAG = "DragonBridgeAccess"
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        Log.i(TAG, "DragonBridgeAccessibilityService đã kết nối!")
    }

    override fun onDestroy() {
        super.onDestroy()
        instance = null
    }

    fun performSwipeNext() {
        try {
            val metrics = resources.displayMetrics
            val width = metrics.widthPixels.toFloat()
            val height = metrics.heightPixels.toFloat()

            val path = Path().apply {
                moveTo(width * 0.85f, height * 0.5f)
                lineTo(width * 0.15f, height * 0.5f)
            }

            val gesture = GestureDescription.Builder()
                .addStroke(GestureDescription.StrokeDescription(path, 0, 150))
                .build()

            dispatchGesture(gesture, null, null)
            Log.i(TAG, "Đã gửi lệnh vuốt lật trang kế tiếp (Next Page) thành công!")
        } catch (e: Exception) {
            Log.e(TAG, "Lỗi vuốt trang: ${e.message}")
        }
    }

    fun performSwipePrev() {
        try {
            val metrics = resources.displayMetrics
            val width = metrics.widthPixels.toFloat()
            val height = metrics.heightPixels.toFloat()

            val path = Path().apply {
                moveTo(width * 0.15f, height * 0.5f)
                lineTo(width * 0.85f, height * 0.5f)
            }

            val gesture = GestureDescription.Builder()
                .addStroke(GestureDescription.StrokeDescription(path, 0, 150))
                .build()

            dispatchGesture(gesture, null, null)
            Log.i(TAG, "Đã gửi lệnh vuốt trang trước (Previous Page) thành công!")
        } catch (e: Exception) {
            Log.e(TAG, "Lỗi vuốt trang: ${e.message}")
        }
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}
    override fun onInterrupt() {}
}
