package com.dragon.read.reader.server

import org.junit.Test
import java.io.File

class CapCutTest {
    @Test
    fun testCapCutDirect() {
        println("=== Starting CapCut TTS Test ===")
        try {
            val audio = CapCutTtsHelper.synthesize("Xin chào bạn, đây là thử nghiệm giọng đọc sách.", "BV074_streaming", false)
            if (audio != null) {
                println("SUCCESS! Received audio bytes: ${audio.size}")
                File("test_output.mp3").writeBytes(audio)
            } else {
                println("FAILURE! audio is null")
            }
        } catch (e: Exception) {
            println("EXCEPTION during CapCut test: ${e.message}")
            e.printStackTrace()
        }
    }
}
